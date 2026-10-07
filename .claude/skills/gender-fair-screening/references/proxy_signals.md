# Proxy signals

A proxy signal is something that is not a gender marker but is correlated with gender, so a screener that penalises it disadvantages one gender even when it never sees gender. Redaction does not remove proxies, because most of them are job-related information that must stay on the CV.

**Rule for the skill:** flag every proxy that the screener penalises or that is unevenly spread between shortlisted and rejected candidates. Never decide that a proxy penalty is acceptable. Ask whether there is a job-related reason, and leave that decision to a named person.

## How the skill tests for proxies

| Test | Script | What it shows |
|---|---|---|
| Who carries each signal, and selection rates with and without it | `audit_shortlist.py --cvs` | Whether a signal is concentrated in one gender, and whether it lines up with the shortlist |
| Counterfactual probe: score each CV again without the signal | `proxy_probe.py` | Whether the screener itself penalises the signal, and by how many points |
| One-sided terms in redacted CVs | `leak_check.py --labels` | Words that appear only on one gender's CVs |

The probe matters because rate comparisons can hide a penalty in small pools. In the demo data, candidates with a career break are shortlisted at the same rate as those without, yet the probe shows every one of them lost 10 points.

## Signals to check

| Signal | Why it is a proxy | Detected automatically? |
|---|---|---|
| **Career breaks and gaps** | Breaks for childbirth and caring are taken mostly by women. Penalising a gap penalises mothers. | Yes: "Career break" lines and gaps over 6 months |
| **Part-time or flexible work** | Women are much more likely than men to work part-time, often because of caring responsibilities. | Yes: "part-time" |
| **Fewer years of continuous experience** at the same qualification level | Follows from breaks and part-time work. Scoring total years can be legitimate; scoring *continuity* usually is not. | Partly: via the gap test |
| **Gendered language in summaries** | Women's and men's self-descriptions differ on average (communal vs agentic words). Tools trained on past hires learn these. | No: read summaries by hand |
| **Subjects, institutions and activities** | Single-sex colleges, some sports, some societies, some degree subjects. | Institutions and gendered team names are redacted; subjects and activities are kept and listed by the one-sided term check |
| **Previous job types** | Occupational segregation: for example summer jobs as "salesperson" vs "server". | Listed by the one-sided term check |

## Evidence to cite (verify each one before citing)

- [ ] **Amazon recruiting tool.** Reuters reported that Amazon's experimental recruiting model learned to penalise CVs containing the word "women's" (as in "women's chess club captain") and downgraded graduates of two all-women's colleges, and that the project was abandoned. Jeffrey Dastin, "Amazon scraps secret AI recruiting tool that showed bias against women", *Reuters*, 10 October 2018.
- [ ] **Motherhood penalty.** In a lab experiment and an audit study, mothers were rated as less competent and committed and offered lower starting salaries than otherwise identical non-mothers; fathers were not penalised. Correll, S. J., Benard, S. and Paik, I. (2007), "Getting a Job: Is There a Motherhood Penalty?", *American Journal of Sociology*, 112(5), 1297–1338.
- [ ] **Names alone change outcomes.** Identical CVs received fewer callbacks with distinctively Black-sounding names. Bertrand, M. and Mullainathan, S. (2004), "Are Emily and Greg More Employable than Lakisha and Jamal?", *American Economic Review*, 94(4), 991–1013. (About race, but the mechanism, a name as a marker, is the same.)
- [ ] **Blind screening.** Screens in orchestra auditions were associated with more women advancing. Goldin, C. and Rouse, C. (2000), "Orchestrating Impartiality", *American Economic Review*, 90(4), 715–741. Note: the size and significance of this effect have been questioned since; cite it as supportive, not conclusive.
- [ ] **Gendered wording.** Masculine-coded wording in job adverts reduced women's interest. Gaucher, D., Friesen, J. and Kay, A. C. (2011), "Evidence That Gendered Wording in Job Advertisements Exists and Sustains Gender Inequality", *Journal of Personality and Social Psychology*, 101(1), 109–128.
- [ ] **Part-time work by gender.** Use current official labour-force statistics for your country (for example the UK Office for National Statistics or India's Periodic Labour Force Survey) for the share of women and men working part-time.
