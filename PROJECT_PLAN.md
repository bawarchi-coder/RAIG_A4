# Gender-Fair CV Screening Skill: Project Plan

**Course:** Responsible AI and Governance (final project)
**Brief:** 13, Fairness and Discrimination Assessment
**Build tool:** Claude Code in VS Code

> How to use this file: save it as `PROJECT_PLAN.md` in your project root. In Claude Code you can then say "Read PROJECT_PLAN.md and do Step 3" instead of pasting long prompts.

---

## 1. What we are building

An **agent skill** that can be added to any CV-screening workflow so that candidates for a role are assessed without gender influencing the result.

It does three things:

| Stage | What happens | Why |
|---|---|---|
| **Redact** | Gender markers are removed from each CV and replaced with neutral placeholders | The screener (human or software) cannot act on what it cannot see |
| **Screen blind** | The existing screening tool scores the redacted CVs | The skill does not replace the HR software, it wraps around it |
| **Audit** | The shortlist is checked for gender gaps, and proxy signals are flagged | Redaction alone does not prove fairness; proxies such as career breaks survive it |

**One-line pitch:** "A plug-in fairness layer for CV screening: it hides gender before screening and checks the outcome after."

---

## 2. How this answers the brief

| Brief element | How the project covers it |
|---|---|
| Primary perspective: risk manager, fairness lead or business owner | Output is a short audit report with a clear recommendation, written for a non-technical decision-maker |
| Core decision: does the system create unjustified differences in errors, outcomes or opportunities? | Audit compares shortlist rates by gender (outcomes), twin-CV score differences (errors), and proxy penalties such as career gaps (opportunities) |
| Example 01: applicant ranking, career breaks, non-traditional backgrounds | Career breaks are treated as a proxy signal: flagged for human review, never auto-penalised |
| "Unjustified" | The report asks whether each remaining gap has a job-related reason, and recommends a human decision where it does not |

---

## 3. What you need before starting

- [ ] VS Code installed
- [ ] Python 3.10 or later (`python --version`)
- [ ] Git installed
- [ ] A paid Claude plan (Pro or above) or a Console account. The free plan does not include Claude Code
- [ ] Claude Code installed (see Step 1)
- [ ] Your course readings on fairness metrics and hiring law, for the reference files

You do **not** need: Vercel, a database, real CVs, or a real HR system.

---

## 4. Final folder structure

```
gender-fair-screening/
├── PROJECT_PLAN.md
├── README.md
├── requirements.txt
├── .claude/
│   └── skills/
│       └── gender-fair-screening/
│           ├── SKILL.md
│           ├── scripts/
│           │   ├── redact_cv.py
│           │   ├── leak_check.py
│           │   └── audit_shortlist.py
│           ├── references/
│           │   ├── gender_markers.md
│           │   ├── proxy_signals.md
│           │   └── thresholds.md
│           └── templates/
│               └── audit_report.md
├── data/
│   ├── job_description.md
│   ├── cvs_raw/            # cv_001.txt ... cv_030.txt
│   ├── cvs_redacted/       # produced by the skill
│   └── gender_labels.csv   # audit only, never shown to the screener
├── demo/
│   ├── make_cvs.py
│   └── biased_screener.py  # stand-in for a legacy HR tool
└── outputs/                # rankings, logs, reports
```

---

## 5. Build steps

Do these in order. Data and scripts come first; `SKILL.md` is written last so that it describes a workflow you have already seen working.

### Step 1: Install Claude Code and open the project

In a terminal:

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```

Check it worked: `claude --version`

Then:

1. Create an empty folder called `gender-fair-screening` and open it in VS Code.
2. Open the VS Code terminal (Terminal > New Terminal).
3. Run `claude` and complete the browser login.
4. Save this file into the folder as `PROJECT_PLAN.md`.

Optional: install the Claude Code extension from the VS Code Extensions panel if you prefer a side panel to the terminal.

### Step 2: Scaffold the project

Prompt:

> Read PROJECT_PLAN.md. Create the folder structure from section 4 with empty placeholder files. Create a Python virtual environment, a requirements.txt with pandas, and initialise a git repository with a sensible .gitignore.

### Step 3: Generate synthetic CVs

Prompt:

> Write `demo/make_cvs.py` and run it. It should create:
> 1. `data/job_description.md` for an entry-to-mid level Data Analyst role.
> 2. 30 synthetic CVs as `data/cvs_raw/cv_001.txt` to `cv_030.txt`: 15 men and 15 women, with qualification levels matched across genders so that an unbiased screener should shortlist them at similar rates.
> 3. Realistic gender markers spread across the CVs: full names, pronouns in the summary, titles (Mr, Ms, Mrs), a "Photo: attached" line, marital status, father's or husband's name, date of birth, women's colleges, men's and women's sports teams, "Women in Tech" style societies, and maternity-related career breaks for about 5 of the women.
> 4. 5 twin pairs within the 30: two CVs that are word-for-word identical except for gender markers.
> 5. `data/gender_labels.csv` with columns `cv_id, gender, twin_pair_id`.
> Use a fixed random seed. All people must be fictional.

Check: open three or four CVs and confirm they look plausible.

### Step 4: Build the biased screener (the "existing HR software")

This is a deliberately flawed tool so your skill has something real to catch.

Prompt:

> Write `demo/biased_screener.py`. It takes `--cvs <folder> --jd <file> --out <csv> --top-k 10`. It scores each CV from 0 to 100 on keyword match with the job description and years of experience. It also contains hidden bias: it subtracts points for career gaps longer than 6 months, adds points for male-coded terms (for example "men's cricket team captain", "he", "Mr"), and subtracts points for female-coded terms (for example "women's", "she", "Mrs", "maternity"). Output columns: `cv_id, score, rank, shortlisted`. Run it on `data/cvs_raw` and save to `outputs/ranking_raw.csv`.

### Step 5: Build the three skill scripts

Prompt:

> Write the three scripts in `.claude/skills/gender-fair-screening/scripts/` according to the specifications in section 6 of PROJECT_PLAN.md. Then run redact_cv.py on data/cvs_raw, run leak_check.py on the result, and run audit_shortlist.py on outputs/ranking_raw.csv. Show me the output of each.

Check by hand: count the women in the top 10 of `ranking_raw.csv` yourself and confirm the audit's numbers match.

### Step 6: Write the reference files

Write these yourselves from course material. Claude Code can draft, but you must verify each threshold and citation against its source. Outlines are in section 7.

### Step 7: Write SKILL.md

Start from the draft in section 8. Prompt:

> Create SKILL.md from the draft in section 8 of PROJECT_PLAN.md. Check that every script and reference file it mentions exists at that path, and that the commands in it actually run.

### Step 8: Write the report template

Use section 9.

### Step 9: Test

Always test in a **fresh** Claude Code session (close and reopen), so leftover context does not hide gaps in the instructions. If the skill does not appear, run `/reload-skills`.

| Test | Prompt or action | Expected result |
|---|---|---|
| Skill is found | "What skills are available?" | `gender-fair-screening` is listed |
| Natural trigger | "We're hiring a Data Analyst. Screen the CVs in data/cvs_raw fairly using demo/biased_screener.py and tell me if I can trust the shortlist." | Skill loads and runs all stages |
| Direct trigger | `/gender-fair-screening` | Same |
| Redaction quality | Open 3 redacted CVs | No names, pronouns, titles or marital status; qualifications intact |
| Leak check | Output of `leak_check.py` | Zero leaks, or leaks listed and fixed |
| Raw audit | Audit of `ranking_raw.csv` | Fails the four-fifths rule; twins score differently |
| Redacted audit | Audit of `ranking_redacted.csv` | Gap smaller; twins score identically; career-gap penalty still flagged |
| Baseline | Turn the skill off in `/skills`, repeat the natural-trigger prompt | Generic answer, no redaction, no numbers |

### Step 10: Make it pluggable (optional stretch)

Prompt:

> Add `api.py` using FastAPI with two endpoints: POST /redact (takes CV text, returns redacted text and a change log) and POST /audit (takes a ranking and labels, returns the audit JSON). Reuse the functions from the skill scripts. Add a short "Integration" section to README.md.

This shows that non-agent HR software can call the same logic over HTTP.

### Step 11: Package

- [ ] README.md: what it is, how to install, how to run, limitations
- [ ] Three saved reports in `outputs/` (raw audit, redacted audit, clean control if you make one)
- [ ] Screen recording of a full successful run as a demo backup
- [ ] Commit everything to git

---

## 6. Script specifications

All scripts print JSON to the terminal and take arguments on the command line. Use `python` instead of `python3` on Windows.

### redact_cv.py

```
python redact_cv.py --input data/cvs_raw --output data/cvs_redacted --log outputs/redaction_log.json
```

- Reads every `.txt` file in the input folder.
- Applies the rules in `references/gender_markers.md` (summary below).
- Replaces rather than deletes, so the CV still reads naturally.
- Never alters skills, qualifications, job titles, employers, dates or grades.
- Writes the redacted CV under the same `cv_id` and logs every change (cv_id, original text, replacement, rule).

| Marker | Replacement |
|---|---|
| Candidate name (first line or "Name:" field) | `[CANDIDATE]` |
| Father's, husband's or spouse's name | line removed |
| he / she, him / her, his / her | they / them / their |
| Mr, Ms, Mrs, Miss, Shri, Smt, Kumari | removed |
| Marital status, date of birth, photo line | line removed |
| Gendered institution names ("XYZ Women's College") | `[COLLEGE]`, degree and grade kept |
| Gendered teams and societies ("Men's Cricket Team", "Women in Tech") | "Sports team", "Professional society" |
| Gendered job words (chairman, salesman, waitress) | chairperson, salesperson, server |
| Stated reason for a career break (maternity, family care) | "Career break", dates kept |
| Email or profile links containing the name | `[EMAIL]`, `[PROFILE]` |

### leak_check.py

```
python leak_check.py --input data/cvs_redacted
```

- Scans redacted CVs for any remaining marker from the lexicon, plus any first name from the original CVs.
- Output: `{"files_checked": 30, "leaks": [{"cv_id": "...", "line": 4, "text": "..."}]}`

### audit_shortlist.py

```
python audit_shortlist.py --ranking outputs/ranking_raw.csv --labels data/gender_labels.csv
```

Computes:

- **Selection rate by gender** = shortlisted / total, per gender
- **Impact ratio** = lower selection rate / higher selection rate
- **Four-fifths check** = pass if impact ratio is 0.80 or above
- **Mean score gap** = average score of men minus average score of women
- **Twin test** = score difference within each twin pair (should be 0)
- **Sample-size warning** if either group has fewer than 30 candidates

---

## 7. Reference file outlines

### gender_markers.md
- Full table of markers and replacements (expand the table in section 6)
- Regional notes: markers common in CVs in your market (photo, marital status, family names, honorifics)
- Rule: replace, do not delete; never touch qualifications

### proxy_signals.md
Signals that correlate with gender even after redaction. The skill flags these and tells the screener not to penalise them automatically.
- Career breaks and gaps
- Part-time or flexible work history
- Fewer years of continuous experience at the same qualification level
- Gendered language style in summaries
- Certain subjects, institutions or activities
- Case study to cite: Amazon's experimental recruiting tool, reported by Reuters in 2018, which learned to downgrade CVs containing the word "women's" and was scrapped

### thresholds.md
Verify each of these against the original source before citing.
- **Four-fifths rule** (US EEOC Uniform Guidelines, 1978): a selection rate below 80% of the highest group's rate is treated as evidence of adverse impact
- **EU AI Act**: AI used for recruitment and candidate evaluation is classed as high-risk (Annex III)
- **NYC Local Law 144**: requires bias audits of automated employment decision tools
- **NIST AI Risk Management Framework**: general structure for mapping, measuring and managing bias risk
- Your own jurisdiction's equal-opportunity and data-protection rules
- Note on statistics: the four-fifths rule is unreliable on small samples; say so in the report

---

## 8. SKILL.md draft

```markdown
---
name: gender-fair-screening
description: Makes CV screening gender-fair. Redacts gender markers from CVs before they are scored, then audits the shortlist for gender gaps and proxy bias. Use when asked to screen, rank or shortlist CVs or candidate profiles, to check a hiring shortlist or screening tool for gender bias, or to anonymise CVs.
allowed-tools: Bash(python3 *) Bash(python *)
---

# Gender-fair CV screening

Follow every stage in order for the whole task. Never show raw CVs or
gender labels to whatever is doing the scoring.

## Stage 1: Redact
Run:
python3 ${CLAUDE_SKILL_DIR}/scripts/redact_cv.py --input <raw_folder> --output <redacted_folder> --log outputs/redaction_log.json

Rules for what is removed are in [references/gender_markers.md](references/gender_markers.md).

## Stage 2: Leak check
Run:
python3 ${CLAUDE_SKILL_DIR}/scripts/leak_check.py --input <redacted_folder>

If any leaks are reported, read those CVs, fix the leaks by hand following
the same replacement rules, and re-run until there are none. Also read two
redacted CVs yourself and look for markers the script cannot know about.

## Stage 3: Blind screening
Pass only the redacted folder to the screening tool the user named.
If the user asks you to score the CVs yourself, score only on job-related
criteria from the job description and state the criteria you used.

## Stage 4: Audit
Run:
python3 ${CLAUDE_SKILL_DIR}/scripts/audit_shortlist.py --ranking <ranking_csv> --labels <labels_csv>

Never calculate these figures yourself. Interpret them using
[references/thresholds.md](references/thresholds.md).

## Stage 5: Proxy review
Read [references/proxy_signals.md](references/proxy_signals.md). Check
whether shortlisted and rejected candidates differ on any proxy signal,
especially career breaks. Flag each one. Do not decide that a proxy is
acceptable; ask whether there is a job-related reason for it.

## Stage 6: Report
Fill in [templates/audit_report.md](templates/audit_report.md) and save it
to outputs/. End with one recommendation: proceed, proceed with
conditions, or do not use this shortlist. State that a human makes the
final decision.

## Limits to state in every report
- Redaction reduces gender signals; it does not guarantee fairness.
- Results on small candidate pools are indicative, not conclusive.
- Only gender is assessed, not other protected characteristics.
```

---

## 9. Audit report template

```markdown
# Gender Fairness Audit: [Role]

**Date:**   **Candidates:**   **Shortlist size:**   **Screening tool:**

## Recommendation
[Proceed / Proceed with conditions / Do not use this shortlist]
[Two sentences explaining why.]

## Results
| Measure | Men | Women | Result |
|---|---|---|---|
| Candidates | | | |
| Shortlisted | | | |
| Selection rate | | | |
| Impact ratio | | | [Pass / Fail at 0.80] |
| Mean score | | | |

**Twin test:** [n] pairs, [n] scored identically.

## Redaction summary
[Number of CVs redacted, number of changes, leaks found and fixed.]

## Proxy signals found
| Signal | Who it affects | Job-related reason? | Action |
|---|---|---|---|

## Conditions and next steps
[What must change before this shortlist is used.]

## Limits of this audit
[Sample size, gender only, redaction is not proof of fairness.]

*This audit supports a human decision. It does not make the hiring decision.*
```

---

## 10. Demo script (about 10 minutes)

1. **The problem (1 min).** "An HR team screens 30 CVs with their existing tool. Is the shortlist fair?"
2. **Without the skill (2 min).** Run the biased screener on raw CVs. Show the top 10. Ask Claude Code, with the skill turned off, whether it is fair: generic answer.
3. **The skill (2 min).** Open the folder. Show SKILL.md, the marker table, and one script.
4. **With the skill (4 min).** Same request. Narrate each stage: redaction (show one CV before and after), leak check, blind screening, audit numbers, proxy flags, report.
5. **The honest finding (1 min).** The gap shrinks but the career-break penalty remains. Reveal the hidden rule in `biased_screener.py`. "Blind screening helps, but only the audit caught this."
6. **Limits (1 min).** Small sample, gender only, human makes the final call.

Before the day: record a backup run, enlarge the terminal font, and keep the three saved reports open in tabs.

---

## 11. Governance points to make

- **Separation of duties in data:** gender labels are required for the audit and must never reach the screener. In a real deployment they would be collected voluntarily and stored separately.
- **Mitigation is not assurance:** redaction is a control; the audit is the evidence that the control worked.
- **Human oversight:** the skill recommends; a named person decides and is accountable.
- **Transparency:** every redaction is logged, so the process can be reviewed.
- **Scope honesty:** gender only. Intersectional effects and other protected characteristics are future work.
- **Portability:** the skill follows the open Agent Skills format, and the same logic can be exposed as an API for conventional HR software.

---

## 12. Sources to consult

- Claude Code setup: https://code.claude.com/docs/en/setup
- Claude Code skills: https://code.claude.com/docs/en/skills
- Agent Skills standard: https://agentskills.io
- Barocas, Hardt and Narayanan, *Fairness and Machine Learning*: https://fairmlbook.org
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- EEOC Uniform Guidelines on Employee Selection Procedures (four-fifths rule)
- EU AI Act, Annex III (employment as high-risk)
- NYC Local Law 144 (automated employment decision tools)
- Reuters (2018), report on Amazon's scrapped AI recruiting tool
- Fairlearn documentation (if you extend the metrics): https://fairlearn.org

---

## 13. Progress checklist

- [ ] Step 1: Claude Code running in VS Code
- [ ] Step 2: Project scaffolded
- [ ] Step 3: 30 synthetic CVs and labels generated
- [ ] Step 4: Biased screener produces `ranking_raw.csv`
- [ ] Step 5: Three scripts working, one result verified by hand
- [ ] Step 6: Reference files written and sources checked
- [ ] Step 7: SKILL.md written
- [ ] Step 8: Report template added
- [ ] Step 9: All tests pass in a fresh session
- [ ] Step 10: API wrapper (optional)
- [ ] Step 11: README, saved reports, demo recording, git commit
