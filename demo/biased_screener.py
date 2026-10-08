#!/usr/bin/env python
"""Screener A: stand-in for a legacy CV-screening tool.

DELIBERATELY UNFAIR. It exists so the gender-fair-screening skill has
something real to catch. Never use it on real candidates.

Visible logic: a 0-100 score from keyword match with the job description
(60 points) and years of paid experience, capped at 8 years (40 points).
Hidden logic (switched off with --no-bias):
  * -10 points for each gap of more than 6 months between jobs
  * up to +9 points for male-coded words ("he", "Mr", "men's", ...)
  * up to -16 points for female-coded words ("she", "Mrs", "women's",
    "maternity", ...)

Usage:
  python demo/biased_screener.py --cvs data/cvs_raw --jd data/job_description.md \
      --out outputs/ranking_raw.csv --top-k 10 [--no-bias]
"""
import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

KEYWORD_BANK = ["SQL", "Excel", "Python", "dashboards", "reporting",
                "statistics", "Tableau", "data cleaning", "Power BI",
                "stakeholder", "ETL", "A/B testing", "machine learning",
                "pandas", "R", "Looker", "Spark",
                # software roles
                "Java", "JavaScript", "Git", "REST API", "unit testing", "Agile", "Docker",
                "React", "AWS", "CI/CD", "Kubernetes", "Linux", "C++", "TypeScript"]
MONTH = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
# A date is "Mar 2021", "March 2021", "03/2021" or "2021"
DATE = (r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}"
        r"|(?<!\d)\d{1,2}/\d{4}(?!\d)|(?<![\d/])\d{4}(?!\d))")
RANGE = re.compile(rf"({DATE})\s*(?:to|–|—|-)\s*({DATE}|present|current|now)\b", re.IGNORECASE)
NOT_A_JOB = re.compile(r"\b(?:break|leave|sabbatical|gap)\b", re.IGNORECASE)
AS_OF = date(2026, 9, 1)

# Hidden bias lexicons (titles are matched case-sensitively)
MALE_WORDS = [r"\bhe\b", r"\bhis\b", r"\bhim\b", r"\bmen's\b", r"\bboys'",
              r"\bchairman\b", r"\bsalesman\b"]
MALE_TITLES = [r"\bMr\b", r"\bShri\b"]
FEMALE_WORDS = [r"\bshe\b", r"\bher\b", r"\bwomen'?s?\b", r"\bgirls'", r"\bmaternity\b",
                r"\bchairwoman\b", r"\bwaitress\b", r"\bfemale\b"]
FEMALE_TITLES = [r"\bMrs\b", r"\bMs\b", r"\bMiss\b", r"\bSmt\b", r"\bKumari\b"]


def count(patterns, text, flags=0):
    return sum(len(re.findall(p, text, flags)) for p in patterns)


def keyword_pattern(k):
    return re.compile(r"(?<![A-Za-z])" + re.escape(k) + r"(?![A-Za-z])", re.IGNORECASE)


def jd_keywords(jd_text):
    return [k for k in KEYWORD_BANK if keyword_pattern(k).search(jd_text)]


def to_month(token, is_end=False):
    t = token.strip()
    if re.fullmatch(r"present|current|now", t, re.IGNORECASE):
        return AS_OF.year * 12 + AS_OF.month - 1
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{4})", t)
    if m:
        return int(m.group(2)) * 12 + MONTH[m.group(1).lower()[:3]]
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", t)
    if m:
        return int(m.group(2)) * 12 + int(m.group(1)) - 1
    return int(t) * 12 + (11 if is_end else 0)


def employment(text):
    """Employment intervals as (start, end) month indexes; breaks and leave excluded."""
    jobs = []
    for line in text.splitlines():
        if NOT_A_JOB.search(line):
            continue
        m = RANGE.search(line)
        if m:
            jobs.append((to_month(m.group(1)), to_month(m.group(2), is_end=True)))
    return sorted(jobs)


def gaps(jobs, min_months=6):
    out = []
    for (s1, e1), (s2, e2) in zip(jobs, jobs[1:]):
        g = s2 - e1 - 1
        if g > min_months:
            out.append(g)
    return out


def score_cv(text, keywords, biased=True):
    found = sum(1 for k in keywords if keyword_pattern(k).search(text))
    jobs = employment(text)
    years = sum(e - s + 1 for s, e in jobs) / 12
    score = 60 * found / max(len(keywords), 1) + 40 * min(years, 8) / 8
    if biased:
        score -= 10 * len(gaps(jobs))
        male = count(MALE_WORDS, text, re.IGNORECASE) + count(MALE_TITLES, text)
        female = count(FEMALE_WORDS, text, re.IGNORECASE) + count(FEMALE_TITLES, text)
        score += min(3 * male, 9) - min(4 * female, 16)
    return round(max(0.0, min(100.0, score)), 1)


def rank(scores, top_k):
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"cv_id": cv, "score": s, "rank": i, "shortlisted": i <= top_k}
            for i, (cv, s) in enumerate(ordered, start=1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cvs", required=True)
    ap.add_argument("--jd", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--no-bias", action="store_true", help="switch off the hidden rules (control run)")
    args = ap.parse_args()

    keywords = jd_keywords(Path(args.jd).read_text(encoding="utf-8"))
    scores = {p.stem: score_cv(p.read_text(encoding="utf-8"), keywords, not args.no_bias)
              for p in sorted(Path(args.cvs).glob("*.txt"))}
    rows = rank(scores, args.top_k)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cv_id", "score", "rank", "shortlisted"])
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({"tool": "Screener A", "cvs_scored": len(rows), "top_k": args.top_k,
                      "out": args.out}))


if __name__ == "__main__":
    main()
