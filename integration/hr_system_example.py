#!/usr/bin/env python
"""What an existing HR system (applicant tracking system) would add to use the fairness layer.

Instead of sending CVs straight to its screening tool, the HR system sends them
to POST /screen-fairly. It gets back a blind shortlist plus an audit report.
Gender labels come from a separate, voluntary equal-opportunities form and are
used only for the audit.

Run (with the API and Vendor B running, see start_demo.bat):
  python integration/hr_system_example.py --screener vendor_b
"""
import argparse
import csv
import json
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000/screen-fairly"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screener", default="screener_a", help="name registered on the API server")
    ap.add_argument("--report", default="outputs/hr_system_report.md")
    args = ap.parse_args()

    # 1. What the HR system already has: applications and a job description
    cvs = [{"cv_id": p.stem, "text": p.read_text(encoding="utf-8")}
           for p in sorted(Path("data/cvs_raw").glob("*.txt"))]
    job = Path("data/job_description.md").read_text(encoding="utf-8")
    # 2. Equal-opportunities data, kept apart from the CVs
    with open("data/gender_labels.csv", newline="", encoding="utf-8") as f:
        labels = list(csv.DictReader(f))

    # 3. One call to the fairness layer
    body = {"job_description": job, "cvs": cvs, "screener": args.screener, "labels": labels, "top_k": 10}
    req = urllib.request.Request(API, json.dumps(body).encode("utf-8"), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.load(resp)

    # 4. Use the blind shortlist, and file the audit report for the hiring manager
    shortlist = [r["cv_id"] for r in result["redacted"]["ranking"] if r["shortlisted"]]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(result["redacted"]["report"], encoding="utf-8")
    print("Blind shortlist:", ", ".join(shortlist))
    print("Recommendation: ", result["redacted"]["recommendation"])
    print("Audit report:   ", args.report)


if __name__ == "__main__":
    main()
