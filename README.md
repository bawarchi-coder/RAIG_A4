# Gender-Fair CV Screening

**A plug-in fairness layer for CV screening: it hides gender before screening and checks the outcome after.**

Responsible AI and Governance, final project. Brief 13: Fairness and Discrimination Assessment.

The layer does not replace an organisation's screening software. It wraps around it:

| Stage | What happens | Script |
|---|---|---|
| 1. Redact | Gender markers are removed from each CV and replaced with neutral placeholders | `redact_cv.py` |
| 2. Leak check | Redacted CVs are scanned for surviving markers, names and one-sided terms | `leak_check.py` |
| 3. Screen blind | The existing tool scores only the redacted CVs, as a black box | `screener_adapter.py` |
| 4. Audit | Selection rates, impact ratio (four-fifths rule), Fisher's exact test, twin test | `audit_shortlist.py` |
| 5. Proxy probe | Each CV is re-scored without a career break or "part-time", to test for proxy penalties | `proxy_probe.py` |
| 6. Report | A one-page audit report with a recommendation for a human decision-maker | `make_report.py` |

The same scripts can be used in three ways:

```
            ┌──────────── fairness layer (plain Python, standard library only) ────────────┐
            │  redact → leak check → screen blind → audit → proxy probe → report          │
            └─────────────────────────────────────────────────────────────────────────────┘
                   ▲                           ▲                            ▲
         Claude Code skill            Standalone app                 HTTP API
         (an AI agent follows         (browser, no login,            (existing HR software
          SKILL.md step by step)       no internet)                   calls it)
```

All candidates, employers and institutions in `data/` are fictional.

## Quick start (Windows)

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
start_demo.bat
```

`start_demo.bat` starts the Vendor B demo service, the API and the app, and opens the app and the API's Swagger page in the browser. The skill scripts themselves need only Python 3.10+; the packages are for the app and the API.

## 1. As an agent skill (Claude Code)

The skill is in `.claude/skills/gender-fair-screening/`. Open this folder in Claude Code and ask, for example:

> We're hiring a Data Analyst. Screen the CVs in data/cvs_raw fairly using demo/biased_screener.py and tell me if I can trust the shortlist. Labels are in data/gender_labels.csv.

or type `/gender-fair-screening`. The agent follows `SKILL.md`: it runs each stage, fixes leaks by hand if any are found, reads the references, writes `outputs/audit_report_*.md` and gives a recommendation. It is told to treat the screening tool as a black box and never read its code.

The skill follows the open [Agent Skills](https://agentskills.io) format, so the folder can be copied into another project or another compatible agent.

## 2. As a standalone app

```
.venv\Scripts\streamlit run app.py
```

Choose a screening tool in the sidebar and press **Run fairness check**. Tabs: the existing tool on raw CVs, redaction (each CV before and after, with changes highlighted), blind screening, proxy probe, the report, a "Try it" box to redact any pasted CV, and a comparison of all tools run. A bookmark such as `http://127.0.0.1:8501/?run=vendor_b` runs a tool on load. The app only listens on 127.0.0.1 (see `.streamlit/config.toml`).

## 3. Integration with existing HR software

```
.venv\Scripts\python -m uvicorn integration.api:app --port 8000
```

Open `http://127.0.0.1:8000/docs` to try every endpoint.

| Endpoint | Input | Output |
|---|---|---|
| `GET /screeners` | | screening tools registered on the server |
| `POST /redact` | one CV's text | redacted text and change log |
| `POST /leak-check` | redacted CVs | surviving markers |
| `POST /audit` | ranking and gender labels | audit figures |
| `POST /screen-fairly` | CVs, job description, tool name, optional labels | redaction, blind ranking, audit, probe, report |

`integration/hr_system_example.py` shows the whole integration from the HR system's side in about 30 lines.

**Connecting a screening tool.** A tool needs only a way to send CVs in and get scores out:

- **Command-line tool:** registered as a command template, e.g. `python demo/biased_screener.py --cvs {cvs} --jd {jd} --out {out} --top-k {top_k}`. It must write a CSV with `cv_id` and `score`.
- **Web service:** registered as a URL that accepts `{"job_description", "cvs": [{"cv_id", "text"}], "top_k"}` and returns `{"ranking": [{"cv_id", "score"}]}`.

Tools are registered on the server in `integration/screeners.json`. API callers choose one by name and can never send a command to execute.

## The demo screening tools

| Tool | How it connects | What is wrong with it (hidden) |
|---|---|---|
| **Screener A** (`demo/biased_screener.py`) | command line | Adds points for male-coded words, subtracts for female-coded words, −10 per career gap |
| **Screener A, control** (`--no-bias`) | command line | Nothing: keyword and experience scoring only |
| **Vendor B** (`demo/screener_service.py`) | HTTP | Claims to be gender-blind and never reads names or pronouns, but −12 per career gap and −8 for part-time work |

## Results on the demo data (30 CVs, 15 women, 15 men, shortlist of 10)

| Tool | CVs | Shortlisted (men / women) | Impact ratio | Twin pairs identical | Proxy probe | Recommendation |
|---|---|---|---|---|---|---|
| Screener A | raw | 8 / 2 | 0.25 FAIL | 0 / 5 | career break −10 | Do not use |
| Screener A | redacted | 6 / 4 | 0.67 FAIL | 5 / 5 | career break −10 | Do not use |
| Control | redacted | 5 / 5 | 1.00 PASS | 5 / 5 | none | Proceed with conditions (small sample) |
| Vendor B | raw or redacted | 6 / 4 | 0.67 FAIL | 5 / 5 | career break −12, part-time −8 | Do not use |

What this shows:

1. Redaction removes the direct bias: Screener A's twin pairs go from a 25-point gap to identical scores, and its impact ratio rises from 0.25 to 0.67.
2. Redaction cannot remove proxy bias: the career-break penalty survives and still fails the four-fifths rule. Vendor B, which never reads gender, fails just the same.
3. Comparing selection rates alone would have missed the penalty: candidates with a break were shortlisted at the same rate as those without (33% vs 33%). The counterfactual probe found that every one of them lost points.
4. The redacted CVs also revealed an occupational proxy: "salesperson" appears only on men's CVs (the original summer jobs were "salesman" and "waitress"). The leak check flags it for a human.

Saved reports: `outputs/screener_a/`, `outputs/control/`, `outputs/vendor_b/` (`audit_report_raw.md` and `audit_report_redacted.md` in each). Regenerate with `pipeline.py`, see below.

`outputs/data_analyst/` is a full run by the agent in a fresh Claude Code session (plan Step 9), started from the natural-language prompt above. The skill loaded by itself, ran all six stages, did not open the screener's code, produced rankings and audit figures identical to `outputs/screener_a/`, and added its own observations under "Reviewer notes" in both reports.

## Re-running from scratch

```
python demo/make_cvs.py
python ".claude/skills/gender-fair-screening/scripts/pipeline.py" --raw data/cvs_raw --jd data/job_description.md ^
  --labels data/gender_labels.csv --out outputs/screener_a --tool-name "Screener A" ^
  --cmd "python demo/biased_screener.py --cvs {cvs} --jd {jd} --out {out} --top-k {top_k}"
```

## Folder structure

```
.claude/skills/gender-fair-screening/   the skill: SKILL.md, scripts/, references/, templates/
data/                                   job description, raw and redacted CVs, gender labels
demo/                                   CV generator, Screener A, Vendor B service, answer key
integration/                            HTTP API, screener registry, example HR-system client
outputs/                                rankings, logs and audit reports
app.py                                  standalone app
start_demo.bat                          starts the services for a demo
PROJECT_PLAN.md                         the original plan
```

## Changes from the project plan

- **Three ways in.** The plan had the skill plus an optional API. The API is now required, and a standalone app was added, so the layer can be shown without an AI agent and plugged into other software.
- **Extra scripts.** `screener_adapter.py` (runs any tool as a black box), `proxy_probe.py` (counterfactual proxy test), `make_report.py` (fills the template from the JSON, so no number is typed by hand), `pipeline.py` (all stages in one call) and `cv_signals.py` (shared date parsing).
- **Proxy probe.** Comparing selection rates could not detect the career-break penalty on 30 CVs; re-scoring each CV without its break could.
- **Fisher's exact test** is reported next to the four-fifths rule, because the rule is unreliable on small samples.
- **Symmetric placeholders.** The plan replaced gendered colleges with `[COLLEGE]` and gendered teams with "Sports team". A placeholder used only for women reveals gender, so every education institution becomes `[INSTITUTION]`, and team or society names lose only the gender word. All career-break reasons are removed, not only maternity.
- **One-sided term check** in `leak_check.py` (with `--labels`) finds words used for only one gender.
- **Black-box rule.** The skill must not read the screening tool's code. In an earlier trial, an agent without the skill read the demo screener's code and found the hidden rules, which a real vendor's tool would not allow.
- **Second demo screener (Vendor B)** over HTTP, to show the layer works with different tools and that proxy bias survives redaction.
- **Control mode** (`--no-bias`) on Screener A gives a clean comparison.
- **Standard library only** for the skill scripts, instead of pandas, so the skill runs anywhere without installing anything.
- **Twins differ in phone number** as well as gender markers, since they are different people. No tool scores phone numbers.

## Limitations

- **Gender only, binary labels.** Other protected characteristics, intersections and non-binary candidates are not assessed.
- **Small sample.** 15 candidates per group: results are indicative, not conclusive.
- **Synthetic data and screeners.** Real CVs are messier (PDF layouts, other languages), and real tools are less predictable.
- **Rule-based redaction.** It can miss unusual markers and can mis-conjugate rare verbs after a pronoun. The leak check and a human read of two CVs are the safeguard.
- **The probe tests the signals it knows** (career breaks, part-time). Other proxies need other counterfactuals.
- **Recommendations are rule-based** and support, not replace, a human decision.

## Governance points

- **Separation of duties in data:** gender labels are needed for the audit but never reach the screener. In practice they come from a voluntary, separately stored equal-opportunities form.
- **Mitigation is not assurance:** redaction is a control; the audit and probe are the evidence of whether it worked.
- **Human oversight:** the layer recommends; a named person decides and is accountable.
- **Transparency:** every redaction is logged; every report shows its numbers and limits.
- **Scope honesty:** gender only; intersectional effects are future work.
- **Portability:** the open Agent Skills format for agents, an HTTP API for conventional software.
- **Black-box auditing:** the layer judges a tool only by its outputs, as an external auditor of a vendor's tool must (compare NYC Local Law 144 bias audits).
