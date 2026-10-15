# Images for the README

Add your demo video and screenshots here, then switch them on in the main `README.md`.

## Capture rules
- Use fictional data only. Use the "Alex Example" person and the files in `examples/`.
- Point the harness at a throwaway data folder before you open the agent, so your real data never appears. On macOS or Linux:

```bash
export RESUME_HARNESS_DATA=/tmp/rh-demo-media
```

- On Windows PowerShell the same setting is:

```text
$env:RESUME_HARNESS_DATA="C:\temp\rh-demo-media"
```

- Hide your username, home folder path, and anything personal in the terminal prompt and window title.
- Do not show a real job posting that names a real company contact.

## Suggested files
- `demo.gif`: about 30 to 60 seconds, from the first message to the finished files. Keep it small (a few MB). For a longer video, upload it to YouTube and link it from the README with a screenshot as the thumbnail.
- `01-first-message.png`: the first message and the agent's first question.
- `02-plan-approval.png`: the plan table and the approval question.
- `03-ats-report.png`: the check report, including the keyword gaps.
- `04-final-resume.png`: the finished PDF.

## Switch them on
1. Put the files in this folder.
2. In the main `README.md`, remove the comment markers around the demo line near the top.
3. To add the screenshots, put lines like this under a new "Screenshots" heading:

```text
![The plan the agent asks you to approve](docs/images/02-plan-approval.png)
```

4. Run the maintainer check. It fails if a README image points to a missing file:

```bash
python dev/verify_harness.py
```

## Delete the throwaway data afterwards

```bash
python scripts/rh.py --data-dir /tmp/rh-demo-media reset --confirm "DELETE ALL DATA"
```
