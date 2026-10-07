# Gender Fairness Audit: Data Analyst

**Date:** 2026-10-07 &nbsp; **Candidates:** 30 &nbsp; **Shortlist size:** 10 &nbsp; **Screening tool:** demo/biased_screener.py &nbsp; **CVs screened:** raw (gender markers visible)

## Recommendation
**Do not use this shortlist**

This shortlist shows evidence of adverse impact: the selection rate for female candidates is 0.25 of the rate for male candidates, below the four-fifths (0.80) threshold; and 5 of 5 twin pairs, whose CVs differ only in gender markers, received different scores. The probe also found that the screener penalises career break or gap (candidates affected, career break or gap: 5 female, 1 male).

## Results
| Measure | Men | Women | Result |
|---|---|---|---|
| Candidates | 15 | 15 | |
| Shortlisted | 8 | 2 | |
| Selection rate | 53% | 13% | |
| Impact ratio | | | 0.25: **FAIL** at 0.80 |
| Mean score | 61.2 | 35.5 | gap +25.7 points (men minus women) |

**Twin test:** 5 pairs, 0 scored identically.

| Pair | Man | Woman | Score (man) | Score (woman) | Difference |
|---|---|---|---|---|---|
| T1 | cv_014 | cv_021 | 89.8 | 64.8 | +25.0 |
| T2 | cv_022 | cv_023 | 76.5 | 51.5 | +25.0 |
| T3 | cv_006 | cv_005 | 61.5 | 36.5 | +25.0 |
| T4 | cv_016 | cv_018 | 51.5 | 26.5 | +25.0 |
| T5 | cv_011 | cv_007 | 30.5 | 19.5 | +11.0 |

**Statistical note:** Fisher's exact test p = 0.050. With this few candidates the difference could be chance (p ≥ 0.05), so the four-fifths result is a warning sign, not proof. The four-fifths rule is a rule of thumb and is unreliable on small samples.

## Redaction summary
Not applied. The CVs were screened with names, pronouns and other gender markers visible. This is the baseline the fairness layer is compared with.

## Proxy signals found
| Signal | Who it affects | Penalty measured by probe | Job-related reason? | Action |
|---|---|---|---|---|
| Career break or gap | 5 female, 1 male | 6 of 6 CVs penalised, mean 10.0 points | Not established: a human must answer | Remove the penalty or justify it in writing; review affected CVs by hand |
| Part-time work | 4 female, 1 male | 0 of 5 CVs penalised, mean 0.0 points | n/a | Keep monitoring |

Selection rates for candidates with and without each signal: career break or gap 33% with, 33% without; part-time work 0% with, 40% without. Rates alone can hide a penalty in small pools; the probe tests it directly.

## Conditions and next steps
1. Do not shortlist from this ranking. Find the cause of the gap and re-run the audit.
2. The tool reacts to gender markers. Screen only redacted CVs, or replace the tool.
3. Ask the vendor or tool owner to remove the career break or gap penalty, or document a job-related reason for it. Until then, review every affected CV by hand (cv_003, cv_004, cv_019, cv_024, cv_027, cv_030).
4. Repeat the audit on a larger pool, or across several hiring rounds, before drawing firm conclusions.
5. A named person reviews this report and makes the final shortlist decision.

## Limits of this audit
- Redaction reduces gender signals; it does not guarantee fairness.
- Results on small candidate pools are indicative, not conclusive. Here at least one group has fewer than 30 candidates.
- Only gender is assessed, as a binary label, not other protected characteristics or their intersections.
- The screener was tested as a black box. The probe shows *that* a signal is penalised, not why.

## Reviewer notes
*Reviewer: Claude (AI assistant), 2026-10-07. To be confirmed by the named decision-maker.*

- **This is the current shortlist.** Fisher's p = 0.050 is borderline, but the twin test settles the question on its own: CVs identical except for gender markers scored 25 points higher for the man in 4 pairs and 11 points higher in the fifth. The tool scores gender markers directly.
- **Clearest example:** twin pair T2. cv_022 (man) is shortlisted at rank 4; cv_023 (woman), word-for-word the same CV apart from name, pronouns and one summer-job title, ranks 15th and is rejected.
- **Who changes when gender is hidden:** the blind run shortlists cv_004 and cv_023 (both women) in place of cv_006 and cv_019 (both men). The other 8 names are the same.
- The proxy rows come from the probe run on redacted CVs with the same tool; the career-break penalty applies to this baseline as well.

*This audit supports a human decision. It does not make the hiring decision. A named person must review it and is accountable for the outcome.*
