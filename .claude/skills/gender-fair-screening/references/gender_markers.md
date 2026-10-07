# Gender markers and how they are redacted

`scripts/redact_cv.py` implements this table. If you change one, change the other.

## Principles

1. **Replace, do not delete**, wherever a line carries job-related content, so the CV still reads naturally.
2. **Never alter** skills, qualifications, degrees, grades, job titles, employers or dates. The one exception is a gendered word inside a title (chairman → chairperson), which keeps its meaning.
3. **Log every change** (cv_id, line, original text, replacement, rule) so the process can be reviewed.
4. **Placeholders must not reveal gender.** A placeholder that is only ever used for one group becomes a marker itself. For that reason *every* education institution becomes `[INSTITUTION]`, not only women's colleges, and team or society names keep their activity but lose the gender word ("Women's Cricket Team" → "Cricket Team", "Men's Cricket Team" → "Cricket Team").
5. **Redaction is a control, not proof.** The leak check and the audit test whether it worked.

## Marker table

| Marker | Example | Replacement | Rule name in log |
|---|---|---|---|
| Candidate name (first line or `Name:` field), with any title | `Mrs. Priya Sharma` | `[CANDIDATE]` | candidate_name |
| Name tokens elsewhere in the CV | `Priya's project` | `[CANDIDATE]'s project` | candidate_name |
| Titles and honorifics | Mr, Mrs, Ms, Miss, Mx, Shri, Shrimati, Smt, Kumari, Sushri | removed | title |
| Subject pronouns, with the verb fixed | `She has built` | `They have built` | pronoun, pronoun_verb_agreement |
| Object, possessive, reflexive pronouns | him / her / his / hers / himself / herself | them / their / theirs / themself | pronoun |
| Father's, mother's, husband's, wife's, spouse's or guardian's name; S/o, D/o, W/o | `Husband's name: Rahul Iyer` | line removed | family_name |
| Date of birth, age | `Date of birth: 14/03/1996` | line removed | date_of_birth |
| Gender or sex field | `Gender: Female` | line removed | gender_field |
| Marital status | `Marital status: Married` | line removed | marital_status |
| Photo line | `Photo: attached` | line removed | photo |
| Education institution (any, in the education section) | `Ashford Women's College`, `Kingsbridge College` | `[INSTITUTION]`, degree, year and grade kept | institution |
| Gendered institution elsewhere in the CV | `St. Agnes Girls' School` | `[INSTITUTION]` | institution |
| Gendered word in a team or society name | `Captain, Women's Cricket Team` | `Captain, Cricket Team` | gendered_qualifier |
| "Women in …" societies | `Women in Tech Society` | `Tech Society` | gendered_qualifier |
| Named gendered organisations | Girls Who Code, Women Who Code | "a coding community" | gendered_organisation |
| Gendered job words | chairman, chairwoman, salesman, waitress, spokesman, foreman, policewoman, head girl … | chairperson, salesperson, server, spokesperson, supervisor, police officer, school captain … | gendered_job_word |
| Stated reason for a career break | `Career break (maternity leave) \| Sep 2020 to Feb 2021` | `Career break \| Sep 2020 to Feb 2021` (dates kept) | career_break_reason |
| Bullet describing a break reason | `- Cared for newborn` | line removed | career_break_detail |
| Email address | `priya.sharma@example.com` | `[EMAIL]` | email |
| Profile links | linkedin.com/in/…, github.com/… | `[PROFILE]` | profile_link |

Break reasons are removed for **every** break (study, travel, health, caring), not only maternity, so that "Career break" does not itself signal a woman.

## Regional notes

- **India.** Biodata-style CVs often include date of birth, gender, marital status, father's or husband's name (or S/o, D/o, W/o), religion, a photo and the honorifics Shri, Smt and Kumari. All are covered except religion, which is out of scope for a gender audit but should be removed in practice.
- **UK and Ireland.** Photos and dates of birth are uncommon; pronouns in a third-person summary and gendered societies or sports teams are the usual markers.
- **Continental Europe.** Photos, dates of birth and marital status are still common in some countries (for example Germany).
- **Everywhere.** First names are the strongest single marker. Names in referee sections and in email addresses are handled by the name and email rules.

## Known gaps

- Third-person summaries in languages other than English are not handled.
- Pronoun handling assumes binary he/she; candidates who use they/them are unaffected.
- Previous job titles are kept because they are job-related, but a gendered pattern of jobs (for example "salesperson" vs "server") can still reveal gender. `leak_check.py --labels` lists such one-sided terms for human review.
- Rare verb forms after a pronoun may be conjugated wrongly ("they focuse"). Grammar does not affect the screener, but read two redacted CVs by hand.
