# Resume Decision Framework (seed reference)

Note for the agent: the examples below use cybersecurity and technical roles. The logic applies to any field. For a different profession, replace the evidence types with the equivalents for that field (for example: campaigns and case studies for marketing, clinical rotations for healthcare, portfolio pieces for design).

---

# 1. First principle: Resume is not a list of everything you know

Think of a resume as:

> **Target Role -> Relevant Evidence -> Strongest Sections -> Appropriate Order**

For example, someone may have:

* B.Tech CSE
* no formal job
* 2 CVEs
* bug bounty reports
* 5 projects
* cybersecurity certifications
* technical blog
* GitHub

That person should **not** use the same resume structure as someone who has:

* 4 years of SOC experience
* 3 companies
* multiple security roles
* no CVE
* no public research

Both are cybersecurity candidates, but their **strongest evidence is different**.

---

# 2. First decide the candidate type

Before choosing sections, classify the candidate.

| Candidate profile                     | Primary evidence                                 |
| ------------------------------------- | ------------------------------------------------ |
| Student / Fresher                     | Education + Projects + Skills                    |
| Student + strong security work        | Projects + Security Experience + Research        |
| Experienced professional              | Professional Experience                          |
| Research-oriented                     | Research + Publications + CVEs                   |
| Bug bounty / vulnerability researcher | Vulnerability Research + CVEs + Bug Bounty       |
| Developer moving into security        | Development Experience + Security Projects       |
| Security professional                 | Security Experience + Technical Skills           |
| Academic / higher studies             | Education + Research + Publications              |
| Mixed technical profile               | Experience + Projects + Specialized achievements |

This is the **first decision**.

---

# 3. Then identify the candidate's "strongest proof"

This is the most important HR/ATS concept.

Do not ask:

> "What sections does a resume normally have?"

Ask:

> **"What evidence proves that this person can do the target job?"**

### Candidate A

Has:

* B.Tech
* 3 projects
* Python
* Burp Suite
* Nmap
* no experience

Their resume should emphasize:

**Education -> Projects -> Technical Skills -> Certifications**

---

### Candidate B

Has:

* B.Tech
* 1 CVE
* responsible disclosure
* bug bounty
* security research

The structure changes:

**Professional/Security Experience -> Vulnerability Research -> CVE/Achievements -> Projects -> Education -> Skills**

The CVE is not just another line under "Achievements." It is **evidence of security research ability**.

---

### Candidate C

Has:

* 3 years SOC experience
* SIEM
* incident response
* threat hunting
* certifications

The resume should primarily be:

**Professional Experience -> Skills -> Certifications -> Education**

Projects might become a small section or disappear completely.

---

# 4. Sections should be earned, not mandatory

A common mistake is believing every resume needs:

* Objective
* Summary
* Education
* Experience
* Projects
* Skills
* Certifications
* Achievements
* Publications
* Blogs
* Volunteer
* Hobbies
* Languages
* References

No. A section should exist only if it adds **useful evidence**.

| Section        | When to use                                                 |
| -------------- | ----------------------------------------------------------- |
| Summary        | Almost always useful for experienced/specialized candidates |
| Objective      | Usually unnecessary for experienced candidates              |
| Education      | Students/freshers; important degree information             |
| Experience     | If actual professional/relevant experience exists           |
| Projects       | Students, freshers, developers, technical candidates        |
| Research       | If meaningful research exists                               |
| CVEs           | If assigned CVEs exist                                      |
| Publications   | If actual publications exist                                |
| Bug Bounty     | If meaningful bounty/research activity exists               |
| Certifications | If relevant certifications exist                            |
| Skills         | Almost always                                               |
| Achievements   | Only meaningful achievements                                |
| Blogs          | Only if technically relevant and worth showing              |
| GitHub         | If it demonstrates useful technical work                    |
| Volunteer      | If relevant to target role                                  |
| Hobbies        | Usually unnecessary                                         |
| References     | Usually unnecessary                                         |

---

# 5. The same person can have different resumes

Suppose a candidate has:

* B.Tech CSE
* M.Tech in AI & Data Science
* Web/API VAPT
* vulnerability research
* an assigned CVE
* bug bounty
* web development
* AI and AI automation work
* security certifications
* technical projects

That candidate should not necessarily have **one universal resume**. They can create different versions.

### Version A: Web Application Security

**Summary** -> Web/API Security -> VAPT -> Vulnerability Research -> CVE -> Projects -> Certifications -> Skills -> Education

---

### Version B: Vulnerability Research

**Summary** -> Vulnerability Research -> CVE -> Responsible Disclosure -> Security Research Projects -> Technical Skills -> Certifications -> Education

---

### Version C: General Cybersecurity

**Summary** -> Cybersecurity Experience -> VAPT -> Network/Wireless Security -> Vulnerability Research -> Projects -> Certifications -> Skills -> Education

---

### Version D: AI Security / AI Security Engineering

The AI-related work becomes much more prominent.

**Summary** -> AI + Cybersecurity -> AI Security Projects -> Security Research -> AI/ML Skills -> Cybersecurity Skills -> Projects -> Education

Same person. Same facts. Different **information hierarchy**.

---

# 6. The "section selection" algorithm

## Step 1: Define the target job

Example:

> Web Application Security Engineer

Not:

> Cybersecurity

Be specific.

---

## Step 2: Extract all evidence

Create a master database:

```text
Education
Experience
Internships
Projects
Research
CVEs
Bug Bounty
Certifications
Achievements
Publications
Blogs
GitHub
Technical Skills
Tools
Open Source
Competitions
Conferences
Leadership
Volunteer
```

Do not worry about resume length yet.

---

## Step 3: Score relevance

For every item ask:

* A. Is it relevant to the job?
* B. Does it demonstrate ability?
* C. Is it credible/verifiable?
* D. Is it recent?
* E. Is it stronger than something already included?

Conceptually:

```text
Resume Value =
Relevance
+ Evidence
+ Credibility
+ Recency
```

Numerical scores do not appear on the resume.

---

# 7. Evidence hierarchy

For technical/security resumes, evidence is roughly ranked like this:

```text
Professional Security Experience
        |
Major Security Research
        |
CVE / Vulnerability Disclosure
        |
Relevant Projects
        |
Internship / Practical Experience
        |
Certifications
        |
Technical Writing / Blogs
        |
Coursework
        |
General Skills
```

This is **not a universal ranking**. A highly relevant CVE can be much more useful for a vulnerability-research position than an unrelated internship. That is why **job relevance comes first**.

---

# 8. How to decide between Projects, Experience and Research

### Experience

Someone else gave you a role/responsibility.

Example:

> Security Intern, Company X

---

### Project

You built or performed something yourself.

Example:

> Developed a vulnerable web application and performed systematic security testing against it.

---

### Research

You investigated something and produced a meaningful finding.

Example:

> Discovered an IDOR vulnerability affecting user records in a web application and coordinated responsible disclosure.

---

### Achievement

The result itself is noteworthy.

Example:

> CVE-XXXX-XXXXX assigned.

The same activity can sometimes produce multiple types of evidence.

---

# 9. CVEs deserve special treatment

If someone has a legitimate assigned CVE, do not hide it in a generic "Achievements" section.

For a security resume, use something like:

## Vulnerability Research

**CVE-XXXX-XXXXX: IDOR Vulnerability**
Product name and version

Then explain concisely:

* vulnerability type
* affected component
* impact
* disclosure status

The CVE itself acts as an external validation signal.

---

# 10. What about blogs?

Having a blog does **not automatically mean** adding a "Blog" section.

Ask: **Does the blog demonstrate expertise relevant to the job?**

### Weak

> 25 Linux commands I use every day

Not necessarily useful for a professional security resume.

### Stronger

> Technical analysis of an authentication bypass vulnerability

Potentially useful for a security research role.

Instead of:

> Blog: 30 articles

use:

## Technical Writing

* Web application vulnerability research
* API security testing methodology
* Analysis of a specific vulnerability

Provide links if appropriate.

---

# 11. Certifications should not dominate automatically

A fresher might give certifications considerable space:

```text
Certifications
CEH
Security+
...
```

But someone with 5 years of experience should not have certifications occupying half the page.

Reason: **real professional experience is stronger evidence than course completion** in most hiring contexts.

---

# 12. ATS changes the formatting decision

There are two separate decisions:

* **Content architecture**: what sections should exist?
* **Visual design**: how should they look?

For ATS-heavy applications, prioritize:

* standard section headings
* readable fonts
* normal text
* clear dates
* consistent job titles
* simple bullet points
* standard chronology
* no critical information inside graphics
* no text embedded in images
* minimal tables
* no complicated multi-column layouts unless the ATS is known to handle them

A beautiful resume is not necessarily an ATS-friendly resume.

---

# 13. Chronological vs functional vs hybrid

## 1. Reverse chronological

```text
Summary
Experience
Projects
Education
Skills
Certifications
```

Best when professional experience is substantial.

---

## 2. Functional / skills-based

```text
Summary
Technical Skills
Security Projects
Research
Education
Certifications
```

Useful for students, career changers, or candidates whose strongest evidence is not conventional employment. Pure functional resumes can make recruiters suspicious because they obscure chronology.

---

## 3. Hybrid

Usually the most useful approach for technical candidates with mixed experience.

```text
Summary
Technical/Security Experience
Research / Projects
Education
Certifications
Skills
```

It answers both: **What can you do?** and **Where did you demonstrate it?**

---

# 14. Decision tree

```text
START
  |
  |-- Does candidate have relevant professional experience?
  |       |
  |       |-- YES
  |       |     |
  |       |     +-- Is it substantial?
  |       |            |
  |       |            |-- YES -> Experience-led resume
  |       |            |
  |       |            +-- NO  -> Hybrid resume
  |       |
  |       +-- NO
  |             |
  |             +-- Does candidate have strong projects/research?
  |                    |
  |                    |-- YES -> Project/Research-led resume
  |                    |
  |                    +-- NO  -> Education/Skills-led fresher resume
  |
  +-- Then add specialized evidence:
          |
          |-- CVE?            -> Vulnerability Research
          |-- Publications?   -> Publications
          |-- Bug bounty?     -> Security Research / Bug Bounty
          |-- Certifications? -> Certifications
          |-- Strong GitHub?  -> Projects / Open Source
          |-- Relevant blogs? -> Technical Writing
          +-- Awards?         -> Achievements
```

---

# 15. The most important rule: no empty sections

If someone has no publications, do not write:

```text
PUBLICATIONS

None
```

Same with:

```text
ACHIEVEMENTS

N/A
```

The section does not exist. The resume is **assembled dynamically**.

---

# 16. Practical resume architectures

### Technical fresher

```text
NAME
Contact | LinkedIn | GitHub | Portfolio

SUMMARY

EDUCATION

TECHNICAL SKILLS

PROJECTS

CERTIFICATIONS

ACHIEVEMENTS / RESEARCH
```

Then modify according to evidence.

### Security researcher

```text
NAME
Contact | LinkedIn | GitHub | Portfolio

SUMMARY

SECURITY EXPERIENCE / RESEARCH

VULNERABILITY RESEARCH

PROJECTS

CERTIFICATIONS

TECHNICAL SKILLS

EDUCATION
```

### Experienced security engineer

```text
NAME
Contact | LinkedIn | GitHub | Portfolio

SUMMARY

PROFESSIONAL EXPERIENCE

SELECTED SECURITY PROJECTS

TECHNICAL SKILLS

CERTIFICATIONS

EDUCATION
```

---

# 17. Master profile and targeted variants

Maintain a **Master Resume Database** first:

```text
MASTER PROFILE
|
|-- Education
|-- Professional Experience
|-- Internships
|-- Security Research
|-- CVEs
|-- Bug Bounty
|-- Projects
|-- Certifications
|-- Achievements
|-- Publications
|-- Technical Writing
|-- Open Source
|-- GitHub
|-- Skills
+-- Other Evidence
```

Then generate one resume per target role:

```text
                 MASTER PROFILE
                       |
          +------------+------------+
          |            |            |
     Web Security   Vuln Research  AI Security
          |            |            |
      Resume A      Resume B      Resume C
```

This is far more maintainable than editing one giant resume every time.

**The resume does not change because the person changed. It changes because the evidence hierarchy changes for the target role.**

---

# Core rule (one sentence)

> **Choose the resume structure based on the candidate's strongest relevant evidence, then choose sections only when the candidate has meaningful content for them, and finally order those sections according to the target job.**
