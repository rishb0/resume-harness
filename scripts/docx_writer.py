#!/usr/bin/env python3
"""Write the resume as a .docx file using only the standard library.

The file uses real Word structure: a Title for the name, Heading 1 for section headings,
list paragraphs with real bullets, and real hyperlinks. No tables, text boxes, or images,
so it reads cleanly in any ATS. Unlike the default PDF engine, Word handles any script
(for example Devanagari), so non-Latin names and text are kept as typed.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import io
import re
import zipfile
from typing import Any, Dict, List, Tuple
from xml.sax.saxutils import escape

import build_resume

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

PAGE = {"a4": (11906, 16838), "letter": (12240, 15840)}

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""

STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {NS}>
<w:docDefaults>
<w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="40" w:line="252" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:jc w:val="center"/><w:spacing w:after="40"/></w:pPr><w:rPr><w:b/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="000000"/></w:pBdr><w:spacing w:before="200" w:after="60"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:caps/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:ind w:left="360"/><w:spacing w:after="20"/></w:pPr></w:style>
<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>
</w:styles>"""

NUMBERING = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering {NS}>
<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>
<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/><w:lvlJc w:val="left"/>
<w:pPr><w:ind w:left="360" w:hanging="220"/></w:pPr><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr></w:lvl>
</w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>"""


class _Ctx:
    def __init__(self) -> None:
        self.rels: List[Tuple[str, str]] = []

    def link(self, url: str) -> str:
        for rid, target in self.rels:
            if target == url:
                return rid
        rid = f"rId{len(self.rels) + 10}"
        self.rels.append((rid, url))
        return rid


def _run(text: str, bold: bool = False, italic: bool = False, mono: bool = False, link: bool = False) -> str:
    props = ""
    if link:
        props += '<w:rStyle w:val="Hyperlink"/>'
    if mono:
        props += '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>'
    if bold:
        props += "<w:b/>"
    if italic:
        props += "<w:i/>"
    rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def _link(ctx: _Ctx, text: str, url: str) -> str:
    return f'<w:hyperlink r:id="{ctx.link(url)}">{_run(text, link=True)}</w:hyperlink>'


def _inline(ctx: _Ctx, text: str, bold: bool = False, italic: bool = False) -> str:
    out = []
    for token in build_resume._INLINE_RX.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            out.append(_run(token[2:-2], bold=True, italic=italic))
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            out.append(_run(token[1:-1], mono=True, bold=bold, italic=italic))
        elif token.startswith("[") and "](" in token:
            label, url = token[1:-1].split("](", 1)
            out.append(_link(ctx, label, url))
        else:
            out.append(_run(token, bold=bold, italic=italic))
    return "".join(out)


def _para(content: str, style: str = "", align: str = "", keep_next: bool = False,
          bullet: bool = False, after: int = -1) -> str:
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        ppr += "<w:keepNext/>"
    if bullet:
        ppr += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    if after >= 0:
        ppr += f'<w:spacing w:after="{after}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    return f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{content}</w:p>"


def _display_url(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def build_docx(doc: Dict[str, Any], contact: Dict[str, Any], paper: str) -> bytes:
    ctx = _Ctx()
    body: List[str] = []
    body.append(_para(_run(doc["name"]), style="Title"))
    if doc["headline"]:
        body.append(_para(_inline(ctx, doc["headline"]), align="center", after=40))
    bits: List[str] = []
    if contact.get("email"):
        bits.append(_link(ctx, contact["email"], "mailto:" + contact["email"]))
    if contact.get("phone"):
        bits.append(_run(contact["phone"]))
    if contact.get("location"):
        bits.append(_run(contact["location"]))
    for link in contact.get("links", []):
        bits.append(_link(ctx, _display_url(link["url"]), link["url"]))
    if bits:
        joined = _run("  |  ").join(bits)
        body.append(_para(joined, align="center", after=60))

    for sec in doc["sections"]:
        body.append(_para(_run(sec["title"]), style="Heading1"))
        is_skills = sec["title"].strip().lower() in build_resume.SKILL_SECTION_TITLES
        for kind, value in sec["blocks"]:
            if kind == "entry":
                primary, secondary, location, dates = value
                head = _inline(ctx, primary, bold=True)
                if not secondary and not location:
                    if dates:
                        head += _run("  |  " + dates)
                    body.append(_para(head, keep_next=True, after=20))
                else:
                    body.append(_para(head, keep_next=True, after=0))
                    parts = []
                    if secondary:
                        parts.append(_inline(ctx, secondary, italic=True))
                    if location:
                        parts.append(_run(location))
                    if dates:
                        parts.append(_run(dates))
                    body.append(_para(_run("  |  ").join(parts), keep_next=True, after=20))
            elif kind == "bullets":
                if is_skills and all(": " in b for b in value):
                    for item in value:
                        cat, rest = item.split(": ", 1)
                        body.append(_para(_run(cat + ": ", bold=True) + _inline(ctx, rest), after=20))
                else:
                    for b in value:
                        body.append(_para(_inline(ctx, b), style="ListParagraph", bullet=True))
            elif kind == "para":
                body.append(_para(_inline(ctx, value)))

    width, height = PAGE.get(paper, PAGE["a4"])
    sect = (f'<w:sectPr><w:pgSz w:w="{width}" w:h="{height}"/>'
            '<w:pgMar w:top="900" w:right="1000" w:bottom="900" w:left="1000" w:header="450" w:footer="450" w:gutter="0"/></w:sectPr>')
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {NS}><w:body>'
                + "".join(body) + sect + "</w:body></w:document>")

    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>']
    for rid, target in ctx.rels:
        rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                    f'Target="{escape(target, {chr(34): "&quot;"})}" TargetMode="External"/>')
    rels.append("</Relationships>")

    title = escape(doc["name"] + " Resume")
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>' + title + "</dc:title><dc:creator>"
            + escape(doc["name"]) + "</dc:creator></cp:coreProperties>")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("word/document.xml", document)
        zf.writestr("word/styles.xml", STYLES)
        zf.writestr("word/numbering.xml", NUMBERING)
        zf.writestr("word/_rels/document.xml.rels", "".join(rels))
        zf.writestr("docProps/core.xml", core)
    return buf.getvalue()
