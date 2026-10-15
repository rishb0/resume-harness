# Resume policy (enforced by `rh.py lint` and `rh.py check`)

These rules come from hiring practice and are checked by code. A rule marked FAIL blocks the resume until fixed.

## 1. Header order (FAIL if broken)
1. Name
2. Designation (the `Headline:` line)
3. Contact line: email, phone, city and country, then at most 3 professional links

Nothing else goes in the header. The builder fixes this order; the check confirms it in the extracted PDF text.

## 2. Designation (the Headline line)
- Required.
- It states the person's real current title, or the target role worded honestly.
- Honest wording examples: `Application Security Engineer | Web Testing` (if that is the person's title), `Computer Science Graduate | Web Application Security`, `Aspiring Data Analyst | SQL and Python`.
- Not honest: a senior title the profile does not show.
- The check warns when the designation is neither a title found in the profile nor qualified (Aspiring, Graduate, Seeking, Entry-level, Student, Trainee).

## 3. Contact details
- Phone with country code (for example `+91` followed by the number).
- Location is city and country only. No street address, house number, or PIN code.
- A professional email address.
- A WhatsApp number may be the phone number. The word WhatsApp never appears.

## 4. Links (FAIL for social media or more than 3)
- Allowed: LinkedIn for everyone; GitHub or a portfolio for technical work; Behance or Dribbble for design; Google Scholar or ORCID for research.
- Not allowed: Instagram, WhatsApp, Twitter or X, Facebook, Telegram, Snapchat, TikTok, Pinterest, Reddit, Discord, Threads, and similar. This applies to links, handles, and mentions in the text.
- Maximum 3 links. `contact set` refuses blocked links and a fourth link.

## 5. Personal data (FAIL)
Do not write: date of birth or age, marital status, religion, gender, caste, parents' names, ID numbers (Aadhaar, PAN, passport, national ID, social security), or a full "Address:" line.
Nationality is allowed only in regions where it is customary (the region list shows which).

## 6. Photo (optional, off by default)
- Off unless the region allows it and the user wants it. In the United States, Canada, and the United Kingdom photos are not used (`photo: never`).
- The ATS file never contains a photo. If a photo is on, the build makes a separate `resume-photo` PDF for email or print.
- Photo standard: recent, head and shoulders, face fully visible, plain light background, even lighting, neutral expression, smart simple clothing, no filters, no sunglasses or hat, not a fashion or party photo, printed small (about 2.6 x 3.0 cm). It does not need to look like an official ID or passport photo.
- The harness never judges a person's appearance and the photo is never a selection criterion. It is only there where local practice expects a photo.

## 7. Writing lint (WARN)
- No filler: hard-working, passionate, innovative, results-driven, responsible for, worked on, helped with, various, etc.
- No first-person pronouns.
- Vary opening verbs (the same opener at most twice), but only with verbs that are true.
- Bullets 5 to 30 words. Summary 3 sentences or fewer, about 60 words or fewer.
- Finished jobs use past tense.
- One date style. Newest entry first. Gaps over 6 months between jobs are flagged so the user can prepare an honest explanation.
- At most 5 bullets per entry.
