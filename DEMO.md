# Demo script (about 10 minutes)

## Before you present

- [ ] Double-click `start_demo.bat`. Three windows open (Vendor B, API, app) and two browser tabs. Leave the windows open.
- [ ] Browser tabs: app (`http://127.0.0.1:8501/?run=screener_a`), Swagger (`http://127.0.0.1:8000/docs`).
- [ ] In the app, also run **Vendor B** and **Screener A control** once, so the "All runs" tab is filled.
- [ ] VS Code open on this folder, Claude Code panel open, font enlarged (Ctrl + =).
- [ ] Editor tabs open: `SKILL.md`, `references/gender_markers.md`, `outputs/screener_a/audit_report_redacted.md`.
- [ ] Backup: screen recording of a full run, the saved reports in `outputs/`, and the public demo page (shared from claude.ai), which works on any device with no setup.
- [ ] Wi-Fi not needed for the app or API. Claude Code needs internet.

## 1. The problem (1 min)

"An HR team screens 30 CVs for a Data Analyst role with the tool they already own. 15 women, 15 men, matched on qualifications. Is the shortlist fair?"

## 2. Without the fairness layer (2 min): app, tab ① Existing tool

- Point at the grey bars: **53% of men shortlisted, 13% of women. Impact ratio 0.25: fails the four-fifths rule.**
- Twin table: "These five pairs of CVs are word-for-word identical except for gender markers. The tool gives the man 25 points more."
- "Note Fisher's p = 0.05: borderline. With 30 CVs even a gap this large is only just significant. That is why the report never treats one number as proof."

## 3. The fairness layer (2 min): VS Code

- Show `SKILL.md`: six stages, the ground rules (labels never reach the screener, the tool is a black box, a human decides).
- Show the marker table in `gender_markers.md`, principle 4: "a placeholder used only for women would itself reveal gender, so every institution is replaced".
- One line on the three ways in: same scripts for the agent, the app and the API.

## 4. With the fairness layer (4 min)

**Agent, Claude Code panel.** Type:

> We're hiring a Data Analyst. Screen the CVs in data/cvs_raw fairly using demo/biased_screener.py and tell me if I can trust the shortlist. Labels are in data/gender_labels.csv.

Narrate as it goes: redaction → leak check → blind screening → audit → proxy probe → report. (If it is slow, continue in the app and come back to it.)

**App, while the agent works:**
- Tab ② Redaction: pick `cv_003`. "Name, email, pronouns, the girls' school, the reason for the career break: gone. Dates, skills, employers, grades: untouched." Leak check: 0. Point at the yellow box: "salesperson appears only on men's CVs. The jobs themselves are gendered. We don't hide job history; we flag it for a human."
- Tab ③ Blind screening: twin pairs now 5/5 identical. Impact ratio up from 0.25 to 0.67 … **still fails.**

## 5. The honest finding (1 min): tab ④ Proxy probe

- "Why does it still fail? We scored every CV again with the career break removed and nothing else changed. Every one gained 10 points. Five of the six are women."
- "Comparing rates alone would have missed it: people with breaks were shortlisted at the same rate as people without."
- Reveal: open `demo/biased_screener.py` and show the hidden rule `score -= 10 * len(gaps(jobs))`. "Blind screening helped, but only the audit caught this."
- **Vendor B** (sidebar → Vendor B → Run): "This vendor claims to be gender-blind, and the twin test agrees. It still fails at 0.67: it penalises career breaks and part-time work. Redaction does nothing against that; the probe catches it."
- **Dataset 2** (sidebar → Candidate pool → Dataset 2, Screener A → Run): "A second, harder pool we built to test the code. After redaction this shortlist *passes* the 80% rule, 0.93, and yet the probe shows breaks still cost 8.6 points. That is why the report says 'proceed with conditions', not 'fair'. And running this pool first found five real gaps in our own code, which we fixed."

## 6. Plugs into existing software (1 min): Swagger tab

- `POST /redact` → Try it out → Execute: the example CV comes back redacted with a change log.
- "Any HR system can call this. The screening tools are registered on the server, so callers can't make it run arbitrary commands." Optionally run `python integration/hr_system_example.py --screener vendor_b` in a terminal.

## 7. Limits (1 min)

- Small sample: indicative, not conclusive.
- Gender only, binary labels; no intersectional analysis.
- Redaction is a control, not proof; the audit is the evidence.
- A named human makes the final decision: tab ⑤ Report ends with that sentence.

## If something goes wrong

| Problem | Fix |
|---|---|
| Claude Code slow or offline | Carry on in the app; it shows every stage. Then show `outputs/screener_a/audit_report_redacted.md` |
| App shows "Vendor B is not running" | Re-run `start_demo.bat`, or `.venv\Scripts\python demo\screener_service.py` |
| A port is already in use | Close the old windows (or restart the laptop) and run `start_demo.bat` again |
| Everything fails | Play the recording; open the saved reports in `outputs/` |

## Likely questions

- **Why not just remove names?** Pronouns, titles, colleges, teams, family names and break reasons all reveal gender. The twin test shows the tool reacts to them.
- **Isn't penalising gaps reasonable?** Only if there is a job-related reason, and it must be justified in writing. The report leaves that decision to a person. Under the UK Equality Act 2010 s.19, a rule that disadvantages one sex must be a proportionate means of achieving a legitimate aim.
- **Why use gender labels at all, if the goal is to ignore gender?** You cannot check for a gap without knowing who is who. The labels go to the audit only, never to the screener, and should come from a voluntary, separately stored form.
- **Does a pass mean the tool is fair?** No. The control passes, but the report still says "proceed with conditions": the sample is small, and only two proxies were tested.
- **Why did the agent need rules about not reading the code?** Real vendors don't share code, so the audit has to work from outputs alone. In testing, an agent without the skill read the demo tool's code, which a real audit couldn't do.
- **Is the data real?** No, all 30 CVs are fictional and generated with a fixed seed (`demo/make_cvs.py`), with 5 twin pairs built in on purpose.
