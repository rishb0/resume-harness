---
description: "After the strategy is approved: write the resume, build the PDF, run checks and review"
---
Load the skill `resume-workflow` and follow it from Step 6 through Step 9 for the application given here: $ARGUMENTS. Every command needs the person slug and the application id. If either is missing, run `python scripts/rh.py person list`, then `python scripts/rh.py app list <person>`, and ask the user which application to continue. Do not start if the strategy was not approved in this conversation: ask the user to confirm first.
