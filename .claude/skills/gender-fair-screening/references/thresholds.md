# Thresholds, law and how to read the audit numbers

Verify every item against its original source before citing it. Tick the box when done.

## The measures

| Measure | Meaning | How to read it |
|---|---|---|
| Selection rate | shortlisted ÷ candidates, per gender | The basic outcome measure |
| Impact ratio | lower selection rate ÷ higher selection rate | 1.00 means equal rates; below 0.80 fails the four-fifths rule |
| Fisher's exact test (p) | Chance of a gap at least this large if gender made no difference | p < 0.05: unlikely to be chance. p ≥ 0.05 on a small pool: **not** evidence of fairness, only too little data to tell |
| Mean score gap | mean score of men minus women | Shows direction and size even when the shortlist hides it |
| Twin test | Score difference between CVs identical except for gender markers | Any non-zero difference means the tool reacts to gender markers directly |
| Proxy probe | Score change when one proxy signal is removed | A positive change means the tool penalises that signal |

## Four-fifths rule

- [ ] **Source:** US Uniform Guidelines on Employee Selection Procedures (1978), 29 C.F.R. § 1607.4(D).
- A selection rate for any sex, race or ethnic group that is less than four-fifths (80%) of the rate for the group with the highest rate is generally regarded by US federal enforcement agencies as evidence of adverse impact.
- The same section says smaller differences can still be adverse impact if they are statistically and practically significant, and larger differences may not be if they rest on small numbers. **This is why the audit reports Fisher's exact test as well.**
- It is a rule of thumb for enforcement, not a legal definition of discrimination, and it is a US rule. Use it as a screening threshold, not as a verdict.

## EU AI Act

- [ ] **Source:** Regulation (EU) 2024/1689 (Artificial Intelligence Act), Article 6(2) and Annex III, point 4(a).
- AI systems intended to be used for recruitment or selection, in particular to place targeted job adverts, to analyse and filter job applications and to evaluate candidates, are **high-risk**.
- Relevant obligations for high-risk systems include risk management (Art. 9), data governance including examination for possible biases (Art. 10), record-keeping and logs (Art. 12), transparency to deployers (Art. 13), human oversight (Art. 14), and deployer duties including informing workers' representatives (Art. 26).
- [ ] **Check the current application date.** The Act set 2 August 2026 for Annex III high-risk obligations. In November 2025 the European Commission proposed a "Digital Omnibus" that would delay them. Confirm whether that delay was adopted before you state a date.
- How this project maps: redaction log and reports → record-keeping; audit → bias examination; "a human decides" → human oversight.

## NYC Local Law 144

- [ ] **Source:** New York City Local Law 144 of 2021 (NYC Administrative Code §§ 20-870 to 20-874) and the Department of Consumer and Worker Protection rules (6 RCNY § 5-300 and following). Enforced from 5 July 2023.
- Employers using an automated employment decision tool in New York City must have an independent bias audit done within the year before use, publish a summary of the results, and notify candidates.
- The audit must report selection rates (or scoring rates) and **impact ratios** by sex and by race/ethnicity, including intersectional categories. This project's impact ratio is the same calculation for two groups.

## NIST AI Risk Management Framework

- [ ] **Source:** NIST AI 100-1, *Artificial Intelligence Risk Management Framework (AI RMF 1.0)*, January 2023.
- Four functions: **Govern, Map, Measure, Manage.** "Fair, with harmful bias managed" is one of its characteristics of trustworthy AI.
- [ ] Related: NIST Special Publication 1270, *Towards a Standard for Identifying and Managing Bias in Artificial Intelligence* (2022), which separates systemic, human and statistical/computational bias.
- How this project maps: Map = proxy signals list; Measure = audit and probe; Manage = redaction and conditions; Govern = human decision-maker and logs.

## Your jurisdiction (fill in and verify)

- [ ] **UK:** Equality Act 2010. Sex and pregnancy and maternity are protected characteristics (s.4). Indirect discrimination (s.19): a provision, criterion or practice applied to everyone that puts one sex at a particular disadvantage is unlawful unless it is a proportionate means of achieving a legitimate aim. **A career-gap penalty is a textbook example to test against s.19.** Also UK GDPR Article 22 on solely automated decisions.
- [ ] **India:** Code on Wages, 2019, section 3: no discrimination on the ground of gender in recruitment for the same work or work of a similar nature. Check the commencement date of the labour codes before citing. Also the Digital Personal Data Protection Act, 2023, for handling CV data and gender labels.
- [ ] **EU:** GDPR Article 22 (automated decision-making) and Article 9 (special categories), plus national equal-treatment law.

## Statistics: what to say in every report

- With 15 candidates per group, one candidate moves a selection rate by about 7 percentage points. The four-fifths rule is unreliable at this size; say so.
- A failed four-fifths check with p ≥ 0.05 is a **warning sign that needs investigation**, not proof of discrimination.
- A passed four-fifths check on a small pool is **not proof of fairness**. Look at the twin test and the probe.
- Repeat the audit over several hiring rounds and pool the results before drawing firm conclusions.
