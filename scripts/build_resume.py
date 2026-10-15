#!/usr/bin/env python3
"""Convert a resume Markdown file to LaTeX and (if a TeX engine exists) to PDF.

Contact details are never written by the agent. The resume Markdown contains
placeholders such as {{NAME}}; this script fills them from the person's
contact.json at build time, on the local machine only.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import rhlib
from rhlib import RHError

TEMPLATE_DIR = rhlib.HARNESS_ROOT / "templates" / "latex"
SKILL_SECTION_TITLES = {"skills", "technical skills", "core skills", "key skills", "tools and technologies"}
PLACEHOLDER_RX = re.compile(r"\{\{\s*([A-Z_]+)\s*\}\}")
CONTACT_ONLY_RX = re.compile(r"^\s*\{\{\s*CONTACT\s*\}\}\s*$")


# --------------------------------------------------------------------------
# placeholders
# --------------------------------------------------------------------------

def contact_values(contact: Dict[str, Any]) -> Dict[str, str]:
    links = contact.get("links", [])
    return {
        "NAME": contact.get("name", ""),
        "EMAIL": contact.get("email", ""),
        "PHONE": contact.get("phone", ""),
        "LOCATION": contact.get("location", ""),
        "LINKS": ", ".join(_display_url(x["url"]) for x in links),
    }


def fill_placeholders(text: str, contact: Dict[str, Any]) -> str:
    values = contact_values(contact)
    missing: List[str] = []
    unknown: List[str] = []

    def sub(match: "re.Match[str]") -> str:
        key = match.group(1)
        if key == "CONTACT":
            return match.group(0)
        if key not in values:
            unknown.append(key)
            return match.group(0)
        if not values[key]:
            missing.append(key.lower())
        return values[key]

    out = PLACEHOLDER_RX.sub(sub, text)
    if unknown:
        raise RHError("Unknown placeholder(s) in resume: " + ", ".join("{{%s}}" % k for k in sorted(set(unknown))),
                      "Allowed placeholders: {{NAME}} {{EMAIL}} {{PHONE}} {{LOCATION}} {{LINKS}} {{CONTACT}}")
    if missing:
        raise RHError("Contact data missing for: " + ", ".join(sorted(set(missing))),
                      "Save it with: python scripts/rh.py contact set <person> --" + sorted(set(missing))[0] + " ...")
    return out


# --------------------------------------------------------------------------
# Markdown parsing (strict, small format; see .claude/skills/resume-writer/references/resume-md-format.md)
# --------------------------------------------------------------------------

def parse_resume_md(text: str) -> Dict[str, Any]:
    doc: Dict[str, Any] = {"name": "", "headline": "", "sections": []}
    section: Optional[Dict[str, Any]] = None
    para: List[str] = []
    bullets: Optional[List[str]] = None

    def flush_para() -> None:
        nonlocal para
        if para and section is not None:
            section["blocks"].append(("para", " ".join(para)))
        para = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets is not None and section is not None:
            section["blocks"].append(("bullets", bullets))
        bullets = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if CONTACT_ONLY_RX.match(line):
            continue
        if line.startswith("# ") and not doc["name"]:
            doc["name"] = line[2:].strip()
            continue
        if section is None and line.lower().startswith("headline:"):
            doc["headline"] = line.split(":", 1)[1].strip()
            continue
        if line.startswith("## "):
            flush_para(); flush_bullets()
            section = {"title": line[3:].strip(), "blocks": []}
            doc["sections"].append(section)
            continue
        if section is None:
            continue
        if line.startswith("### "):
            flush_para(); flush_bullets()
            parts = [p.strip() for p in line[4:].split("|")]
            if len(parts) > 4:
                raise RHError(f"Entry heading has more than 4 fields: {line}",
                              "Format: ### Primary | Secondary | Location | Dates (use an empty field to skip one)")
            parts += [""] * (4 - len(parts))
            section["blocks"].append(("entry", parts))
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m and not line.startswith("  ") or (m and bullets is None):
            flush_para()
            if bullets is None:
                bullets = []
            bullets.append(m.group(1).strip())
            continue
        if not line.strip():
            flush_para(); flush_bullets()
            continue
        if bullets is not None and line.startswith(" "):
            bullets[-1] += " " + line.strip()
            continue
        flush_bullets()
        para.append(line.strip())
    flush_para(); flush_bullets()
    if not doc["name"]:
        raise RHError("Resume Markdown has no '# Name' line.", "The first line must be: # {{NAME}}")
    if not doc["sections"]:
        raise RHError("Resume Markdown has no '## Section' headings.")
    return doc


# --------------------------------------------------------------------------
# LaTeX conversion
# --------------------------------------------------------------------------

LATEX_CHARS = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    "\u2013": "--", "\u2014": "---", "\u2018": "'", "\u2019": "'", "\u201c": "``", "\u201d": "''",
    "\u2022": "-", "\u00a0": "~", "\u2026": "...", "\u2192": "->", "\u2713": "", "\u00b7": "-",
}


def esc(text: str, warnings: List[str]) -> str:
    out = []
    for ch in text:
        if ch in LATEX_CHARS:
            out.append(LATEX_CHARS[ch])
        elif ord(ch) < 256:
            out.append(ch)
        else:
            ascii_form = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode("ascii")
            if ascii_form:
                out.append(ascii_form)
            else:
                out.append("?")
                warnings.append(f"Character U+{ord(ch):04X} cannot be typeset by pdfLaTeX; replaced with '?'.")
    return "".join(out)


_INLINE_RX = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))")


def _href_url(url: str) -> str:
    return url.replace("\\", "/").replace("%", r"\%").replace("#", r"\#")


def _display_url(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def inline(text: str, warnings: List[str]) -> str:
    out = []
    for token in _INLINE_RX.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            out.append(r"\textbf{" + esc(token[2:-2], warnings) + "}")
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            out.append(r"\texttt{" + esc(token[1:-1], warnings) + "}")
        elif token.startswith("[") and "](" in token:
            label, url = token[1:-1].split("](", 1)
            out.append(r"\href{" + _href_url(url) + "}{" + esc(label, warnings) + "}")
        else:
            out.append(esc(token, warnings))
    return "".join(out)


def render_header(doc: Dict[str, Any], contact: Dict[str, Any], warnings: List[str],
                  photo_file: Optional[str] = None) -> str:
    """Header order is fixed: name, designation (headline), contact."""
    parts = []
    if contact.get("email"):
        parts.append(r"\href{mailto:" + contact["email"] + "}{" + esc(contact["email"], warnings) + "}")
    if contact.get("phone"):
        parts.append(esc(contact["phone"], warnings))
    if contact.get("location"):
        parts.append(esc(contact["location"], warnings))
    for link in contact.get("links", []):
        parts.append(r"\href{" + _href_url(link["url"]) + "}{" + esc(_display_url(link["url"]), warnings) + "}")
    contact_line = " $|$ ".join(parts)
    if not photo_file:
        lines = [r"\begin{center}", r"{\LARGE\bfseries " + esc(doc["name"], warnings) + r"}\\[3pt]",
                 inline(doc["headline"], warnings) + r"\\[2pt]"]
        if contact_line:
            lines.append(contact_line)
        lines.append(r"\end{center}")
        return "\n".join(lines)
    conf = rhlib.settings()["photo"]
    return "\n".join([
        r"\noindent\begin{minipage}[c]{0.76\textwidth}\raggedright",
        r"{\LARGE\bfseries " + esc(doc["name"], warnings) + r"}\\[3pt]",
        inline(doc["headline"], warnings) + r"\\[2pt]",
        contact_line,
        r"\end{minipage}\hfill",
        r"\begin{minipage}[c]{0.20\textwidth}\raggedleft",
        r"\includegraphics[width=%scm,height=%scm,keepaspectratio]{%s}" % (conf["width_cm"], conf["height_cm"], photo_file),
        r"\end{minipage}",
        r"\par\vspace{2pt}",
    ])


def render_body(doc: Dict[str, Any], warnings: List[str]) -> str:
    out: List[str] = []
    for sec in doc["sections"]:
        out.append(r"\section*{" + esc(sec["title"], warnings) + "}")
        is_skills = sec["title"].strip().lower() in SKILL_SECTION_TITLES
        for kind, value in sec["blocks"]:
            if kind == "entry":
                # Left-aligned, strictly linear text. Right-aligned columns (\hfill) make many
                # PDF text extractors move dates and locations away from their heading.
                primary, secondary, location, dates = value
                head = r"\textbf{" + inline(primary, warnings) + "}"
                if not secondary and not location:
                    if dates:
                        head += " | " + esc(dates, warnings)
                    out.append(r"\noindent " + head + r"\par\nopagebreak")
                else:
                    out.append(r"\noindent " + head + r"\par\nopagebreak")
                    bits = []
                    if secondary:
                        bits.append(r"\textit{" + inline(secondary, warnings) + "}")
                    if location:
                        bits.append(esc(location, warnings))
                    if dates:
                        bits.append(esc(dates, warnings))
                    out.append(r"\noindent " + " | ".join(bits) + r"\par\nopagebreak")
            elif kind == "bullets":
                if is_skills and all(": " in b for b in value):
                    for item in value:
                        cat, rest = item.split(": ", 1)
                        out.append(r"\noindent\textbf{" + inline(cat, warnings) + ":} " + inline(rest, warnings) + r"\par")
                else:
                    out.append(r"\begin{itemize}")
                    out.extend(r"\item " + inline(b, warnings) for b in value)
                    out.append(r"\end{itemize}")
            elif kind == "para":
                out.append(inline(value, warnings) + r"\par")
    return "\n".join(out)


def build_latex(md_text: str, contact: Dict[str, Any], paper: str, source_name: str,
                preset: Optional[Dict[str, str]] = None,
                photo_file: Optional[str] = None) -> Tuple[str, List[str], Dict[str, Any]]:
    warnings: List[str] = []
    preset = preset or rhlib.settings()["autofit_presets"][2]
    filled = fill_placeholders(md_text, contact)
    doc = parse_resume_md(filled)
    if not doc["headline"]:
        raise RHError("The resume has no 'Headline:' line (the designation).",
                      "The header must be: name, designation, contact. Add 'Headline: <designation>' under '# {{NAME}}', "
                      "save a new resume-md version, and rebuild.")
    template = (TEMPLATE_DIR / "ats-classic" / "template.tex").read_text(encoding="utf-8")
    pdf_name = re.sub(r"[^A-Za-z0-9 ]", "", doc["name"]) or "Resume"
    tex = (template.replace("%%SOURCE%%", source_name)
           .replace("%%PRESET%%", preset["name"])
           .replace("%%FONTSIZE%%", preset["font"])
           .replace("%%MARGIN_H%%", preset["margin_h"])
           .replace("%%MARGIN_V%%", preset["margin_v"])
           .replace("%%LINESPREAD%%", preset["linespread"])
           .replace("%%ITEMSEP%%", preset["itemsep"])
           .replace("%%SEC_BEFORE%%", preset["sec_before"])
           .replace("%%SEC_AFTER%%", preset["sec_after"])
           .replace("%%PAPER%%", "a4paper" if paper == "a4" else "letterpaper")
           .replace("%%PDF_TITLE%%", pdf_name + " Resume")
           .replace("%%PDF_AUTHOR%%", pdf_name)
           .replace("%%HEADER%%", render_header(doc, contact, warnings, photo_file))
           .replace("%%BODY%%", render_body(doc, warnings)))
    return tex, warnings, doc


# --------------------------------------------------------------------------
# compile
# --------------------------------------------------------------------------

def find_engine() -> Optional[str]:
    for name in ("pdflatex", "tectonic"):
        if shutil.which(name):
            return name
    return None


def _log_excerpt(log_path: Path) -> str:
    if not log_path.exists():
        return "(no log file was written)"
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    picked: List[str] = []
    for i, line in enumerate(lines):
        if line.startswith("!") or ": " in line and ".tex:" in line:
            picked.extend(lines[i:i + 3])
        if len(picked) > 24:
            break
    return "\n".join(picked) or "\n".join(lines[-20:])


def compile_tex(tex_text: str, photo_path: Optional[Path] = None, photo_file: Optional[str] = None,
                passes: int = 2) -> Dict[str, Any]:
    """Compile once. Returns pdf bytes (or None), pages, fill ratio of the last page, and a log excerpt."""
    engine = find_engine()
    if not engine:
        return {"pdf": None, "info": "no-engine", "pages": None, "fill": None}
    with tempfile.TemporaryDirectory(prefix="rh-build-") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "main.tex").write_text(tex_text, encoding="utf-8")
        if photo_path and photo_file:
            shutil.copyfile(photo_path, tmp_path / photo_file)
        if engine == "pdflatex":
            cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"]
            runs = [cmd] * max(1, passes)
        else:
            runs = [["tectonic", "main.tex"]]
        output = ""
        for cmd in runs:
            try:
                res = subprocess.run(cmd, cwd=tmp, capture_output=True, timeout=180)
                output += res.stdout.decode("utf-8", "replace") + res.stderr.decode("utf-8", "replace")
            except subprocess.TimeoutExpired:
                return {"pdf": None, "info": "The TeX engine timed out after 180 seconds.", "pages": None, "fill": None}
        pdf = tmp_path / "main.pdf"
        if not pdf.exists():
            return {"pdf": None, "info": _log_excerpt(tmp_path / "main.log"), "pages": None, "fill": None}
        log_path = tmp_path / "main.log"
        log = output + (log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else "")
        pages = None
        m = re.search(r"\((\d+) pages?", log)
        if m:
            pages = int(m.group(1))
        pages = pages or page_count(pdf)
        fill = None
        m = re.search(r"RH-FILL\s+([\d.]+)pt\s*/\s*([\d.]+)pt", log)
        if m and float(m.group(2)) > 0:
            fill = round(min(1.0, float(m.group(1)) / float(m.group(2))), 2)
        return {"pdf": pdf.read_bytes(), "info": "ok", "pages": pages, "fill": fill}


def page_count(pdf_path: Path) -> Optional[int]:
    if shutil.which("pdfinfo"):
        res = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True)
        m = re.search(r"^Pages:\s+(\d+)", res.stdout, re.M)
        if m:
            return int(m.group(1))
    return None


def autofit(md_text: str, contact: Dict[str, Any], paper: str, source_name: str, target_pages: int,
            start_index: int = 0, photo_file: Optional[str] = None,
            photo_path: Optional[Path] = None) -> Dict[str, Any]:
    """Pick the roomiest layout preset that fits the page target. Returns tex, pdf, pages, fill, preset."""
    presets = rhlib.settings()["autofit_presets"]
    best: Optional[Dict[str, Any]] = None
    for i in range(start_index, len(presets)):
        tex, warnings, doc = build_latex(md_text, contact, paper, source_name, presets[i], photo_file)
        res = compile_tex(tex, photo_path, photo_file, passes=1)
        if res["pdf"] is None:
            res.update(tex=tex, warnings=warnings, doc=doc, preset=presets[i]["name"], index=i, fits=False)
            return res
        best = {"tex": tex, "warnings": warnings, "doc": doc, "preset": presets[i]["name"], "index": i,
                "pages": res["pages"], "fill": res["fill"], "fits": (res["pages"] or 99) <= target_pages}
        if best["fits"]:
            break
    assert best is not None
    final = compile_tex(best["tex"], photo_path, photo_file, passes=2)
    best.update(pdf=final["pdf"], info=final["info"])
    if final["pages"]:
        best["pages"] = final["pages"]
    if final["fill"] is not None:
        best["fill"] = final["fill"]
    return best


# --------------------------------------------------------------------------
# build entry point
# --------------------------------------------------------------------------

def _next_k(d: Path, pairs: List[Tuple[str, str]]) -> int:
    return max(rhlib.next_version(d, stem, ext) for stem, ext in pairs)


def build(root: Path, person: str, app_id: str, paper: Optional[str] = None,
          no_compile: bool = False, pages: Optional[int] = None) -> Dict[str, Any]:
    import docx_writer
    d = rhlib.app_dir(root, person, app_id)
    latest_md = rhlib.app_latest(root, person, app_id, "resume-md")
    if not latest_md:
        raise RHError("This application has no resume Markdown yet.",
                      "Save it first: python scripts/rh.py app save <person> <app> resume-md --file <file>")
    contact = rhlib.load_contact(root, person)
    if not contact.get("name"):
        raise RHError("No contact name saved for this person.",
                      "Save contact details first: python scripts/rh.py contact set <person> --name ... --email ... --phone ...")
    rhlib.validate_contact_links(contact)
    st = rhlib.app_settings(root, person, app_id)
    paper = paper or st["paper"]
    if paper not in ("a4", "letter"):
        raise RHError("Paper must be 'a4' or 'letter'.")
    target_pages = pages or st["pages"]
    md_text = latest_md[1].read_text(encoding="utf-8")

    photo = rhlib.latest_photo(root, person) if st["photo"] else None
    if st["photo"] and not photo:
        raise RHError("Photo is switched on but no photo is saved.", "Save one: python scripts/rh.py photo set <person> --file <image>")
    photo_file = ("photo" + photo[1].suffix) if photo else None

    stems = [("resume", "tex"), ("resume", "pdf"), ("resume", "docx"), ("overleaf-resume", "zip"),
             ("resume-photo", "tex"), ("resume-photo", "pdf"), ("overleaf-resume-photo", "zip")]
    k = _next_k(d, stems)
    result: Dict[str, Any] = {"tex": None, "zip": None, "pdf": None, "docx": None, "photo_pdf": None, "photo_tex": None,
                              "photo_zip": None, "pages": None, "fill": None, "preset": None, "fits": None,
                              "warnings": [], "status": "tex-only", "log": "", "version": k, "paper": paper,
                              "target_pages": target_pages}

    if no_compile or not find_engine():
        preset = rhlib.settings()["autofit_presets"][2]
        tex, warnings, doc = build_latex(md_text, contact, paper, latest_md[1].name, preset)
        fit = {"tex": tex, "warnings": warnings, "doc": doc, "preset": preset["name"], "index": 2,
               "pdf": None, "pages": None, "fill": None, "fits": None, "info": "skipped" if no_compile else "no-engine"}
    else:
        fit = autofit(md_text, contact, paper, latest_md[1].name, target_pages)
    result["warnings"] = list(fit["warnings"])
    result["preset"] = fit["preset"]

    tex_path = rhlib.create_text(d / f"resume.v{k}.tex", fit["tex"])
    zip_path = d / f"overleaf-resume.v{k}.zip"
    with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.tex", fit["tex"])
    result.update(tex=tex_path, zip=zip_path)

    docx_path = d / f"resume.v{k}.docx"
    with open(docx_path, "xb") as handle:
        handle.write(docx_writer.build_docx(fit["doc"], contact, paper))
    result["docx"] = docx_path

    if fit.get("pdf"):
        pdf_path = d / f"resume.v{k}.pdf"
        with open(pdf_path, "xb") as handle:
            handle.write(fit["pdf"])
        result.update(pdf=pdf_path, pages=fit["pages"], fill=fit["fill"], fits=fit["fits"], status="ok")
        rhlib.app_status(root, person, app_id, "built")
    elif fit.get("info") == "no-engine":
        result["status"] = "no-engine"
    elif fit.get("info") == "skipped":
        result["status"] = "tex-only"
    else:
        result.update(status="compile-failed", log=fit.get("info", ""))

    if photo and result["status"] in ("ok", "no-engine", "tex-only"):
        if result["status"] == "ok":
            pfit = autofit(md_text, contact, paper, latest_md[1].name, target_pages,
                           start_index=fit["index"], photo_file=photo_file, photo_path=photo[1])
        else:
            ptex, pw, pdoc = build_latex(md_text, contact, paper, latest_md[1].name,
                                         rhlib.settings()["autofit_presets"][2], photo_file)
            pfit = {"tex": ptex, "pdf": None, "warnings": pw, "pages": None, "fill": None}
        ptex_path = rhlib.create_text(d / f"resume-photo.v{k}.tex", pfit["tex"])
        pzip = d / f"overleaf-resume-photo.v{k}.zip"
        with zipfile.ZipFile(pzip, "x", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("main.tex", pfit["tex"])
            zf.write(photo[1], photo_file)
        result.update(photo_tex=ptex_path, photo_zip=pzip)
        if pfit.get("pdf"):
            ppdf = d / f"resume-photo.v{k}.pdf"
            with open(ppdf, "xb") as handle:
                handle.write(pfit["pdf"])
            result["photo_pdf"] = ppdf
            result["photo_pages"] = pfit["pages"]
            if (pfit["pages"] or 0) > target_pages:
                result["warnings"].append(f"The photo version has {pfit['pages']} pages (target {target_pages}); shorten the content.")

    rhlib.app_record_build(root, person, app_id, {
        "version": k, "preset": result["preset"], "pages": result["pages"], "fill": result["fill"],
        "target_pages": target_pages, "paper": paper, "photo": bool(photo), "at": rhlib.now_iso()})
    return result
