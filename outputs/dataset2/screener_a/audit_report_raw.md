# Gender Fairness Audit: Software Developer

**Date:** 2026-10-08 &nbsp; **Candidates:** 40 &nbsp; **Shortlist size:** 12 &nbsp; **Screening tool:** Screener A: legacy command-line tool &nbsp; **CVs screened:** raw (gender markers visible)

## Recommendation
**Do not use this shortlist**

This shortlist shows evidence of adverse impact: the selection rate for female candidates is 0.30 of the rate for male candidates, below the four-fifths (0.80) threshold; and 3 of 4 twin pairs, whose CVs differ only in gender markers, received different scores. The probe also found that the screener penalises career break or gap (candidates affected, career break or gap: 5 female, 2 male).

## Results
| Measure | Men | Women | Result |
|---|---|---|---|
| Candidates | 24 | 16 | |
| Shortlisted | 10 | 2 | |
| Selection rate | 42% | 12% | |
| Impact ratio | | | 0.30: **FAIL** at 0.80 |
| Mean score | 61.9 | 44.7 | gap +17.1 points (men minus women) |

**Twin test:** 4 pairs, 1 scored identically.

| Pair | Man | Woman | Score (man) | Score (woman) | Difference |
|---|---|---|---|---|---|
| T1 | cv_036 | cv_023 | 98.2 | 76.2 | +22.0 |
| T2 | cv_033 | cv_006 | 84.0 | 62.0 | +22.0 |
| T3 | cv_019 | cv_022 | 59.2 | 59.2 | +0.0 |
| T4 | cv_040 | cv_025 | 44.7 | 33.7 | +11.0 |

**Statistical note:** Fisher's exact test p = 0.079. With this few candidates the difference could be chance (p ≥ 0.05), so the four-fifths result is a warning sign, not proof. The four-fifths rule is a rule of thumb and is unreliable on small samples.

## Redaction summary
Not applied. The CVs were screened with names, pronouns and other gender markers visible. This is the baseline the fairness layer is compared with.

## Proxy signals found
| Signal | Who it affects | Penalty measured by probe | Job-related reason? | Action |
|---|---|---|---|---|
| Career break or gap | 5 female, 2 male | 6 of 7 CVs penalised, mean 9.1 points | Not established: a human must answer | Remove the penalty or justify it in writing; review affected CVs by hand |
| Part-time work | 3 female, 1 male | 0 of 4 CVs penalised, mean 0.0 points | n/a | Keep monitoring |

Selection rates for candidates with and without each signal: career break or gap 29% with, 30% without; part-time work 0% with, 33% without. Rates alone can hide a penalty in small pools; the probe tests it directly.

## Conditions and next steps
1. Do not shortlist from this ranking. Find the cause of the gap and re-run the audit.
2. The tool reacts to gender markers. Screen only redacted CVs, or replace the tool.
3. Ask the vendor or tool owner to remove the career break or gap penalty, or document a job-related reason for it. Until then, review every affected CV by hand (cv_001, cv_005, cv_013, cv_015, cv_016, cv_017, cv_031).
4. Repeat the audit on a larger pool, or across several hiring rounds, before drawing firm conclusions.
5. A named person reviews this report and makes the final shortlist decision.

## Limits of this audit
- Redaction reduces gender signals; it does not guarantee fairness.
- Results on small candidate pools are indicative, not conclusive. Here at least one group has fewer than 30 candidates.
- Only gender is assessed, as a binary label, not other protected characteristics or their intersections.
- The screener was tested as a black box. The probe shows *that* a signal is penalised, not why.

## Reviewer notes
_None yet. The reviewer adds notes here; the numbers above are not edited._

*This audit supports a human decision. It does not make the hiring decision. A named person must review it and is accountable for the outcome.*
