# Cover letter

A cover letter is read by a person, not by a machine. Keep it short, specific and true. One page, never more.

## Shape: three or four short paragraphs
1. **The role.** One sentence with the exact job title, the company, and where the posting was found if the user said.
2. **Why this person.** Two or three sentences. Each one ties a real profile entry to a must-have in the job analysis. Use the posting's wording only where it means the same as the profile's wording.
3. **One piece of proof.** The strongest true achievement, with its number when the profile holds a number.
4. **Close.** One sentence. Say the person is available to start and that the contact details are in the header.

## Header
Use the same three lines as the resume, in the same order: `# {{NAME}}`, then the `Headline:` line, then `{{CONTACT}}`. The build fills in the real contact details from the saved contact file, exactly as it does for the resume. Never type the real name, email, phone or links into the letter.

## Rules
- Facts come from the profile only. The same truth rule applies as for the resume: no employer, title, date, degree, certification, tool, skill, metric or achievement that the profile does not support. The automated evidence map covers the resume; for this prose you must check every statement yourself.
- A number may appear only if the profile holds that number.
- Name the company and the role. A letter that could be sent anywhere is not worth sending.
- No flattery that cannot be supported ("world-class team"), no apologies, and no "I am writing to apply for".
- Plain words, short sentences, active voice. Past tense for finished work.
- Never mention a gap, an illness, a salary, a notice period, or a move the user has not confirmed. Never mention a reason for leaving a job.
- No photo, age, marital status, nationality, religion, or any other detail the resume policy forbids.

## Save it
Write `scratch/cover-letter.md`, then:

`python scripts/rh.py app save <person> <app> cover-letter --file scratch/cover-letter.md`

The build turns it into a PDF with the same header layout as the resume. Save your own copy first if you want to change the wording by hand.

## Before it is sent
Read the letter aloud once. If a sentence could go into any other application, delete it or make it specific to this job.
