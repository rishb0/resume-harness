# Resume Markdown format (strict)

The builder parses this format. Anything outside it may be dropped.

```
# {{NAME}}
Headline: <required: the designation, for example Computer Science Graduate | Web Application Security>
{{CONTACT}}

## Summary
<two or three plain sentences, no first-person pronouns>

## <Section title>
### <Primary> | <Secondary> | <Location> | <Dates>
- <bullet>
- <bullet>

## Skills
- <Category>: <item>, <item>, <item>
```

## Rules
- Line 1 is `# {{NAME}}`. Line `{{CONTACT}}` stays exactly as written. The builder fills both from the saved contact file.
- `Headline:` is required (the designation). It comes right after the name line and before the first `##`. The header order is name, designation, contact.
- Section titles use standard names (see `config/settings.json`): Summary, Experience, Internships, Projects, Research, Publications, Education, Skills, Certifications, Achievements, Open Source, Volunteer Experience, Languages.
- Entry headings have at most 4 fields separated by `|`, in this order: primary (job title, degree, project name), secondary (employer, school, tech), location, dates. Leave a field empty but keep the bars when you skip one in the middle: `### Project name | | | 2024`.
- Dates: `Jun 2022 - Aug 2022`, `2019 - 2023`, `2024 - Present`. Use one style for the whole resume.
- Bullets start with `- `. A long bullet may continue on an indented next line.
- Inline: `**bold**`, `` `code` ``, and `[text](url)` only.
- No tables, no columns, no images, no icons, no emoji, no HTML.
- Plain characters only. Curly quotes and dashes are converted; other symbols and non-Latin letters cannot be typeset by the default engine and are replaced with `?` (the builder warns).
- Allowed placeholders: `{{NAME}}`, `{{CONTACT}}`, and, only if needed in text, `{{EMAIL}}`, `{{PHONE}}`, `{{LOCATION}}`, `{{LINKS}}`.

## Evidence map format

One line per claim: `<exact text> => <id>, <id>`

```
SUMMARY => int-01, res-01
- <exact bullet text> => int-01
```

- Copy the bullet text exactly as in the resume (bold marks and links are ignored when matching).
- Ids are profile ids from `profile show`.
- The truth check fails on any bullet without a line, any unknown id, any skill missing from the profile, and warns on numbers not found in the cited entries.
