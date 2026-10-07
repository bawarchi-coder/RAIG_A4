---
name: gender-fair-screening
description: Makes CV screening gender-fair. Redacts gender markers from CVs before an existing screening tool scores them, then audits the shortlist for gender gaps and tests the tool for proxy bias such as career-break penalties. Use when asked to screen, rank or shortlist CVs or candidate profiles, to check whether a hiring shortlist or screening tool can be trusted or is biased against women or men, or to anonymise CVs.
allowed-tools: Bash(python *) Bash(python3 *)
---

# Gender-fair CV screening

A fairness layer that wraps around whatever screening tool the user already
has: hide gender before screening, then check the outcome after.

Follow every stage in order for the whole task, and tell the user which stage
you are on. Run commands from the project root. Use `python` (on Windows
`python3` may not exist). Always keep the script paths in double quotes.

## Ground rules
- **Separation of duties.** Gender labels are for the audit only. Never pass
  raw CVs or labels to whatever does the scoring.
- **Black box.** Judge the screening tool only by its outputs. Do not open,
  read or search its source code, even if it is in the project. Real vendors
  do not share code, and the audit must work without it.
- **Never calculate the figures yourself.** Every number comes from a script.
- **A human decides.** You recommend; a named person makes the hiring decision.

## Stage 0: Gather inputs
Confirm, from the request or by asking:
- raw CV folder (e.g. `data/cvs_raw`) and job description file
- the screening tool: either a command (a program that reads a CV folder and
  writes a CSV with `cv_id` and `score`) or an HTTP endpoint
- gender labels CSV (`cv_id, gender, twin_pair_id`) and shortlist size (default 10)

Write the tool as a command template with the placeholders `{cvs}`, `{jd}`,
`{out}`, `{top_k}` and forward slashes, for example
`python demo/biased_screener.py --cvs {cvs} --jd {jd} --out {out} --top-k {top_k}`.
In the commands below, `<TOOL>` means either `--cmd "<template>"` or `--url <endpoint>`.

## Stage 1: Redact
```
python "${CLAUDE_SKILL_DIR}/scripts/redact_cv.py" --input <raw_folder> --output <redacted_folder> --log outputs/redaction_log.json
```
Rules are in [references/gender_markers.md](references/gender_markers.md).

## Stage 2: Leak check
```
python "${CLAUDE_SKILL_DIR}/scripts/leak_check.py" --input <redacted_folder> --raw <raw_folder> --labels <labels_csv> --out outputs/leak_check.json
```
If leaks are reported, fix them in the redacted CVs by hand using the same
replacement rules, and re-run until there are none. Read every
`one_sided_terms` entry: a term used only for one gender can reveal gender.
Then open two redacted CVs and look for markers the script cannot know about.

## Stage 3: Blind screening
Screen the redacted CVs:
```
python "${CLAUDE_SKILL_DIR}/scripts/screener_adapter.py" --cvs <redacted_folder> --jd <jd_file> --out outputs/ranking_redacted.csv --top-k 10 <TOOL>
```
If the user wants to know whether their **current** shortlist can be trusted,
also run the same command on `<raw_folder>` with `--out outputs/ranking_raw.csv`
as a baseline. If the user asks you to score the CVs yourself instead of using
a tool, score only on job-related criteria from the job description, state the
criteria, and write a CSV with `cv_id, score, rank, shortlisted`.

## Stage 4: Audit
```
python "${CLAUDE_SKILL_DIR}/scripts/audit_shortlist.py" --ranking outputs/ranking_redacted.csv --labels <labels_csv> --cvs <redacted_folder> --out outputs/audit_redacted.json
```
Do the same for `ranking_raw.csv` (with `--cvs <raw_folder>`, `--out outputs/audit_raw.json`)
if you ran the baseline. Interpret the numbers with
[references/thresholds.md](references/thresholds.md).

## Stage 5: Proxy review
```
python "${CLAUDE_SKILL_DIR}/scripts/proxy_probe.py" --cvs <redacted_folder> --jd <jd_file> <TOOL> --out outputs/proxy_probe.json
```
Read [references/proxy_signals.md](references/proxy_signals.md). Flag every
signal the probe shows is penalised and every signal concentrated in one
gender. Do not decide that a proxy is acceptable; ask whether there is a
job-related reason.

## Stage 6: Report
```
python "${CLAUDE_SKILL_DIR}/scripts/make_report.py" --audit outputs/audit_redacted.json --probe outputs/proxy_probe.json --redaction outputs/redaction_log.json --leaks outputs/leak_check.json --role "<role>" --tool "<tool name>" --out outputs/audit_report_redacted.md
```
For the baseline, run it again with `--audit outputs/audit_raw.json`, no
`--redaction`/`--leaks`, and `--out outputs/audit_report_raw.md`.
This fills in [templates/audit_report.md](templates/audit_report.md). Read the
report, check it against the JSON, and add your observations (for example
one-sided terms you judged harmless or not, things you noticed in the CVs)
under **Reviewer notes** without changing any number.

Finish with a short answer to the user: the recommendation (proceed, proceed
with conditions, or do not use this shortlist), the two or three numbers that
justify it, what the proxy probe found, and that a human makes the final decision.

## One-shot mode
If the user wants everything at once without inspection between stages:
```
python "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" --raw <raw_folder> --jd <jd_file> --labels <labels_csv> --out outputs/<run_name> <TOOL> --tool-name "<tool name>"
```
Still read the reports it writes before answering.

## Limits to state in every answer
- Redaction reduces gender signals; it does not guarantee fairness.
- Results on small candidate pools are indicative, not conclusive.
- Only gender is assessed, as a binary label, not other protected characteristics.
