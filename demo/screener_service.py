#!/usr/bin/env python
"""Vendor B "TalentRank": stand-in for a cloud CV-screening service.

DELIBERATELY UNFAIR, in a quieter way than Screener A. It advertises itself
as gender-blind and never reads names, pronouns or titles, but it penalises
career gaps (-12 points each) and part-time work (-8 points), which fall
mostly on women. Never use it on real candidates.

Run:   python demo/screener_service.py            (listens on http://127.0.0.1:8001)
Call:  POST /score  {"job_description": "...", "cvs": [{"cv_id": "...", "text": "..."}], "top_k": 10}
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from biased_screener import employment, gaps, jd_keywords, keyword_pattern, rank  # noqa: E402

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # the offline command-line copy needs only the standard library
    FastAPI = None

PART_TIME = re.compile(r"\bpart[- ]time\b", re.IGNORECASE)


def score_cv(text, keywords):
    found = sum(1 for k in keywords if keyword_pattern(k).search(text))
    jobs = employment(text)
    years = sum(e - s + 1 for s, e in jobs) / 12
    score = 70 * found / max(len(keywords), 1) + 30 * min(years, 6) / 6
    score -= 12 * len(gaps(jobs, min_months=3))
    if PART_TIME.search(text):
        score -= 8
    return round(max(0.0, min(100.0, score)), 1)


if FastAPI is not None:
    app = FastAPI(title="Vendor B TalentRank (demo)",
                  description="Fictional screening service used to demonstrate the fairness layer. "
                              "Claims to be gender-blind.")

    class CV(BaseModel):
        cv_id: str
        text: str

    class ScoreRequest(BaseModel):
        job_description: str
        cvs: list[CV]
        top_k: int = 10

    @app.get("/")
    def about():
        return {"service": "Vendor B TalentRank (demo)", "claim": "gender-blind: names and pronouns are ignored",
                "endpoint": "POST /score"}

    @app.post("/score")
    def score(req: ScoreRequest):
        keywords = jd_keywords(req.job_description)
        scores = {cv.cv_id: score_cv(cv.text, keywords) for cv in req.cvs}
        return {"tool": "Vendor B TalentRank", "ranking": rank(scores, req.top_k)}


def cli():
    """Offline copy of the same scoring, used where the HTTP service cannot run (e.g. cloud hosting)."""
    import argparse
    import csv
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("--cvs", required=True)
    ap.add_argument("--jd", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top-k", type=int, default=10)
    args = ap.parse_args()
    keywords = jd_keywords(Path(args.jd).read_text(encoding="utf-8"))
    scores = {p.stem: score_cv(p.read_text(encoding="utf-8"), keywords) for p in sorted(Path(args.cvs).glob("*.txt"))}
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cv_id", "score", "rank", "shortlisted"])
        w.writeheader()
        w.writerows(rank(scores, args.top_k))
    print(json.dumps({"tool": "Vendor B TalentRank (offline)", "cvs_scored": len(scores)}))


if __name__ == "__main__":
    if "--cvs" in sys.argv:
        cli()
    else:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8001)
