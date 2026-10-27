# Your first resume

This is one full run, from a job advert to a folder of files you can send. It takes about fifteen minutes of your time, most of it answering questions.

You talk in normal English. The agent can run every command for you; the commands in this guide are only there if you want to see them.

For a short list of copy-paste prompts for every task, use [docs/USAGE.md](USAGE.md). This page explains what happens and why.

## What to have ready

- The job advert you are applying to. Copy the whole thing, including the requirements.
- Your work history roughly in mind: employer names, job titles, dates, what you did, and any numbers you remember (how many, how much, how often).
- A photo, only if you want a photo version and the country uses them. This is optional. If you do not have one, the agent gives you phone instructions and an editor prompt. It will not create a face.
- Nothing else. The agent asks for the rest.

## Step 1: Start

Open your agent inside the `resume-harness` folder. OpenCode is recommended; if you use another agent, see [docs/AGENT-INSTALL.md](AGENT-INSTALL.md). Then paste this and press Enter:

```text
Read AGENTS.md and follow it. Make my resume for this job:
```

Then paste the job advert underneath, on the lines after it.

> Do not run `/init` in this folder. `AGENTS.md` is already the harness instruction file, and `/init` can change it.

The agent works out that this is a new job, reads the advert, and starts asking questions. If you have used the harness before it will first ask which saved person this is.

## Step 2: The questions about you

The first time, the agent builds your profile: your work history, education, skills, projects, and certificates. It asks for one thing at a time and waits for your answer.

- Answer honestly. Everything on the resume comes from these answers. The harness checks the resume against them, so a guess now becomes a problem later.
- Give numbers when you can: team size, percentages, money, hours saved, users. Real numbers are the strongest part of a resume. If you do not know a number, say so and the line is written without one.
- This happens once per person. Your profile is saved, so the next job starts from Step 3.
- Answers are saved as you go, so a long conversation is safe. If you have to stop, ask `Where did we get to?` when you come back.

When the agent needs your contact details, it runs the command that opens a private form on your computer. Fill in your name, email, phone, city and country, and any professional links, then save and close it.

The agent is instructed not to read the saved contact file, and the PDF is built locally. Do not type contact details into the conversation; if you do, do not repeat them. The instruction is a policy, not a technical lock, so use an agent and model you trust.

## Step 3: The company and the job

The agent looks up the company from public pages, writes a short brief, and picks apart the job advert: what the employer must have, what is nice to have, and the exact words they use.

It shows you what it found and where each fact came from. If something looks wrong, correct it. It never logs in anywhere and never uses information about individual employees.

## Step 4: The choices, then the plan

The agent asks a short list of questions for this application. The same list is asked once for each new application, because the answers change:

1. Which country is the job in? This sets the paper size and the rules about photos and nationality.
2. Do you want a photo version? Only where that is normal, and only if you have one saved.
3. How long should it be? One page is normal under about ten years of experience; two if you have more or the country expects it; three is rare.
4. Do you want a cover letter as well?
5. Should it also find how to apply, including the careers page and any public application address?
6. Do you want a longer CV beside the one-page resume?
7. Is there anything you want left out, or put first?

Then it shows you a plan: which sections, in what order, and what it will leave out. The plan is saved at this point, but no resume text has been written. Read the plan and answer `Approved`, or say what to change. This is the moment to disagree with it, and it is normal to.

## Step 5: The writing

After you approve, the agent writes the resume, plus a second file that shows where every line came from. Then it checks its own work:

- Every bullet must point at something in your profile. A bullet with nothing behind it is rejected and rewritten.
- Links, photo rules, and the list of personal details that must not appear are checked automatically.
- Filler words, long bullets, mixed tenses, and unexplained gaps are flagged.

If something fails, the agent fixes it and runs the check again. It stops after a few rounds and tells you what is left. If a real gap remains, such as a certificate you do not have, it says so instead of hiding it.

The cover letter and the longer CV are written in the same step, when you asked for them.

## Step 6: The files

The agent builds the files, checks the finished PDF the way an automatic screening system would, and reviews it once more the way a person would. Then it puts the files in one folder and tells you the path.

| File | Use it for |
| --- | --- |
| `YourName_Resume.pdf` | Job websites and application forms. Send this one. |
| `YourName_Resume.docx` | The same resume in Word, for places that ask for Word. |
| `YourName_Cover-Letter.pdf` | Only if you asked for one. For the cover letter box, or the body of the email. |
| `YourName_CV.pdf` | Only if you asked for a longer CV. |
| `YourName_Resume_Photo.pdf` | Only if you asked for a photo version. |

The same folder also holds the LaTeX source and a zip you can upload to Overleaf if you ever want to edit the layout by hand.

### Changing the layout by hand

The export folder holds `YourName_Resume.tex` and `YourName_Overleaf.zip`.

- Overleaf: New Project -> Upload Project, choose the zip, then Recompile.
- On your computer: install TeX Live or MiKTeX, then run `pdflatex YourName_Resume.tex` in that folder.
- These files are generated. A new build makes a new copy, so edit the exported copy for a one-off change. The Markdown is the source of truth; for a permanent change, ask the agent.

## Step 7: Sending it

The agent also tells you what it could not fix. Those are the real gaps: a skill the advert asks for that you do not have, or a missing number. Be ready for a question about them in the interview.

Finally it asks whether to mark the application as applied. Say yes and it records the date, so you can see later which applications are still open.

## Your second job

Paste the next advert the same way. Your profile, the company if it repeats, and every saved job are reused. You are asked the choice list again, because the country, the length, and the cover letter may all be different, and then the agent goes straight to the plan.

## Where your data lives

Everything about you sits in one folder on your computer, separate from the program. Ask `Where is my data?` at any time.

Useful things to say:

- `What do you have saved about me?`
- `Back up my data.`
- `Move my data to this folder: <path>`
- `Delete all my data.`

The harness sends nothing anywhere. It has no account and no server of its own, and everything is saved in that folder.

Your work history is part of the conversation because the agent needs it to write. Your agent may send that conversation to its model provider. Contact details stay in the local contact file. Use an agent with a local model if you need everything to stay on your computer.

## Later changes

- To add something new about you: `Add this to my profile:` and then the details. It applies to your next resume, not to resumes you have already sent.
- To change your contact details: `Change my contact details.` The agent opens the private form again; type the new details there, not in the conversation.
- To change one resume: `Change the summary on my Northwind resume.` The program saves a new version and keeps the old one, so nothing is lost.
- To see the state of a half-finished application: `Where did we get to?`
- To get a newer copy of the program: `Is there a newer version?` It reports what it found clearly, and replaces the program files only after you say yes. Your data is not part of it and is not touched.

## If it goes wrong

- Ask the agent to run the setup check and explain the result clearly.
- If the agent seems to be ignoring the instructions, start your message with `Read AGENTS.md and follow it.`
- If it invents a fact, stop it and say `That is not true. Remove it and check the rest.` The truth check catches this on the resume, and a false line on a resume is worse than a missing one.
