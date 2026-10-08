# Simple guide to the app

**What it does, in one line:** it hides gender on CVs *before* the company's screening software sees them, then checks whether the shortlist that comes out is fair.

Everything in it is fictional: the people, the companies and the two screening tools.

---

## 1. The two choices in the sidebar

### Candidate pool: which set of CVs

| Option | What it is | Why it is there |
|---|---|---|
| **Dataset 1: Data Analyst, 30 CVs** | 15 women and 15 men with matched qualifications. 5 "twin pairs" (see below). One CV layout. | The main demo. Built so a fair tool would shortlist women and men equally. |
| **Dataset 2: Software Developer, 40 CVs** | 16 women and 24 men. 4 twin pairs. Three different CV layouts (UK, Indian biodata, US), different date styles and new kinds of gender clues. | A second, harder test made separately, to check that the code works on CVs it was not designed around. |

### Existing screening tool: the options in the dropdown

These stand in for the software an HR team **already uses**. Our fairness layer does not replace it: it sits around it.

| Option | In plain words | What is secretly wrong with it |
|---|---|---|
| **Screener A: legacy command-line tool** | An old program the HR team runs on a folder of CVs. | It adds points for male words (he, Mr, men's team), takes points off for female words (she, Mrs, women's, maternity) and takes **10 points off for any career gap** longer than 6 months. |
| **Screener A with hidden rules switched off** | Exactly the same program with the unfair rules turned off. | Nothing. This is the **control**: it shows what a fair result looks like, so we can compare. |
| **Vendor B TalentRank: cloud service over HTTP** | An online service the HR team sends CVs to. It claims to be "gender-blind". | It really does ignore names and pronouns, but it takes **12 points off for career gaps** and **8 points off for part-time work**, which hits women more. |

Then press **Run fairness check**.

---

## 2. The numbers at the top

| Number | What it means | Good result |
|---|---|---|
| **Impact ratio: tool on raw CVs** | The tool as used today, with names and gender visible. Women's shortlist rate divided by men's (or the other way round, lower ÷ higher). | 0.80 or more |
| **Impact ratio: same tool, redacted CVs** | The same tool after our layer has hidden gender. | 0.80 or more |
| **Four-fifths rule: PASS / FAIL** | A standard rule of thumb from US hiring law: if one group is shortlisted at less than 80% of the other group's rate, that is a warning sign. | PASS |
| **Twin pairs scored identically** | Twins are two CVs that are word-for-word the same except for gender clues. A fair tool must give both the same score. | All of them (5/5 or 4/4) |
| **Proxy penalties found** | Things that are not gender but go with gender (career breaks, part-time work). We test whether the tool takes points off for them. | 0 |
| **Recommendation** | *Do not use this shortlist*, *Proceed with conditions*, or *Proceed*. Always followed by: a human makes the final decision. | |

---

## 3. The tabs

| Tab | What you see |
|---|---|
| **① Existing tool** | How the tool behaves today on raw CVs: bar chart of who gets shortlisted, the twin pairs and their scores before and after hiding gender. |
| **② Redaction** | What was hidden. Pick any CV to see it **before** (red = removed) and **after** (green = replacement). The leak check result is shown here too. |
| **③ Blind screening** | The same tool's results on the redacted CVs. |
| **④ Proxy probe** | Each CV with a career break (or part-time work) is scored again *with only that removed*. If the score goes up, the tool was penalising it. |
| **⑤ Report** | The one-page audit report for a manager. Can be downloaded. |
| **Try it: redact a CV** | Paste any CV text and see what gets hidden. Good for a live demo. |
| **All runs** | A comparison table of every tool and dataset you have run in this session. |

---

## 4. What you should see

| Pool | Tool | Before (raw CVs) | After (redacted) | The story |
|---|---|---|---|---|
| Dataset 1 | Screener A | 0.25 **FAIL**, twins 0/5 | 0.67 **FAIL**, twins 5/5, career break −10 | Hiding gender fixes the direct bias, but the career-break penalty is still there. |
| Dataset 1 | Control | 1.00 PASS | 1.00 PASS | What fair looks like. Still "with conditions" because 30 CVs is a small sample. |
| Dataset 1 | Vendor B | 0.67 **FAIL**, twins 5/5 | 0.67 **FAIL** | It really is gender-blind, yet still unfair, through proxies. Hiding gender cannot fix that; the probe catches it. |
| Dataset 2 | Screener A | 0.30 **FAIL**, twins 1/4 | 0.93 PASS, twins 4/4, career break −8.6 | The shortlist now *passes* the 80% rule, but the probe shows the tool still punishes career breaks, so the answer is "proceed with conditions", not "fair". |
| Dataset 2 | Control | 0.93 PASS | 0.93 PASS | Fair. |
| Dataset 2 | Vendor B | 0.93 PASS | 0.93 PASS, breaks −10.3, part-time −8 | Passes the headline test, but the probe finds both penalties. |

**The three big lessons**
1. Hiding gender removes *direct* bias (twins become identical).
2. It does not remove *proxy* bias (career breaks, part-time work). Only the probe finds that.
3. A shortlist can pass the 80% rule and still be unfair, so never trust one number.

---

## 5. What the second dataset taught us

We ran the code on Dataset 2 **before changing anything**. It found five real weaknesses, which were then fixed:

1. Personal websites with the person's name (`www.edwardwade.dev`) were not hidden: names leaked on 13 CVs.
2. Headings written as "Education" instead of "EDUCATION" were not recognised, so some university names stayed while women's colleges were hidden. That would have pointed to women again.
3. Dates written as `03/2021` could not be read, so career gaps on those CVs were invisible.
4. Gender labels written as F/M instead of female/male made the audit mix up which group was men.
5. "Sorority", "fraternity", "Hostess" and "Sabbatical (caring for family)" were not hidden.

After the fixes: 0 leaks on both datasets, and Dataset 1's results did not change at all.

---

## 6. How to run it

- **On this laptop:** double-click `start_demo.bat`. The app opens in the browser.
- **Online (public link):** see the README section "Public demo links".

## 7. Words used

- **Redaction:** hiding gender clues (name, he/she, Mr/Mrs, women's college, maternity…) while keeping skills, jobs, dates and grades.
- **Leak check:** a scan of the redacted CVs for anything that still gives gender away.
- **Proxy:** something that is not gender but goes along with it (career breaks, part-time work).
- **Twin pair:** two CVs identical except for gender clues. The cleanest test of direct bias.
- **Control:** the same tool with the unfairness switched off, for comparison.
- **Fisher's p:** how likely a gap this big is by pure chance. Small samples make this large, which is why results are "indicative, not conclusive".
