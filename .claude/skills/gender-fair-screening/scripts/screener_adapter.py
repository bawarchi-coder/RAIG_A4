#!/usr/bin/env python
"""Stage 3: run an existing screening tool on a folder of CVs, as a black box.

The fairness layer never needs to see a screener's code. It only needs a way
to send CVs in and get scores out. Two kinds of tool are supported:

  command  a program run from the command line. --cmd is a template with
           the placeholders {cvs} {jd} {out} {top_k}; the tool must write a
           CSV with cv_id and score columns (rank and shortlisted optional).
  http     a web service. --url receives POST {"job_description", "cvs":
           [{"cv_id", "text"}], "top_k"} and returns {"ranking": [{"cv_id",
           "score", ...}]}.

Usage:
  python screener_adapter.py --cvs data/cvs_redacted --jd data/job_description.md \
      --out outputs/ranking_redacted.csv --top-k 10 \
      --cmd "python demo/biased_screener.py --cvs {cvs} --jd {jd} --out {out} --top-k {top_k}"
  python screener_adapter.py ... --url http://127.0.0.1:8001/score

Writes a normalised CSV (cv_id, score, rank, shortlisted) to --out and prints
a JSON summary. Standard library only.
"""
import argparse
import csv
import json
import shlex
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


class ScreenerError(RuntimeError):
    pass


def truthy(v):
    return str(v).strip().lower() in {"true", "1", "yes", "y", "t"}


def normalise(rows, top_k):
    """Sort by score, assign rank, and fill in 'shortlisted' if the tool did not."""
    rows = [{"cv_id": r["cv_id"], "score": float(r["score"]),
             "shortlisted": r.get("shortlisted")} for r in rows]
    rows.sort(key=lambda r: (-r["score"], r["cv_id"]))
    has_flag = all(r["shortlisted"] not in (None, "") for r in rows)
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
        r["shortlisted"] = truthy(r["shortlisted"]) if has_flag else i <= top_k
    return [{"cv_id": r["cv_id"], "score": r["score"], "rank": r["rank"],
             "shortlisted": r["shortlisted"]} for r in rows]


def run_command(cmd, cvs_dir, jd_path, top_k, cwd=None, timeout=300):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranking.csv"
        values = {"cvs": str(cvs_dir), "jd": str(jd_path), "out": str(out), "top_k": str(top_k)}
        args = [a.format(**values) for a in shlex.split(cmd)]
        if args and args[0] in ("python", "python3", "py"):
            args[0] = sys.executable  # same interpreter as the fairness layer
        proc = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        if proc.returncode != 0:
            raise ScreenerError(f"screener exited with {proc.returncode}: {proc.stderr.strip()[-500:]}")
        if not out.exists():
            raise ScreenerError("screener did not write the {out} file")
        with open(out, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


def run_http(url, cvs_dir, jd_path, top_k, timeout=120):
    payload = {
        "job_description": Path(jd_path).read_text(encoding="utf-8"),
        "cvs": [{"cv_id": p.stem, "text": p.read_text(encoding="utf-8")}
                for p in sorted(Path(cvs_dir).glob("*.txt"))],
        "top_k": top_k,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise ScreenerError(f"could not reach screener at {url}: {e.reason}") from e
    if "ranking" not in body:
        raise ScreenerError("screener response has no 'ranking' field")
    return body["ranking"]


def run_screener(screener, cvs_dir, jd_path, top_k=10, cwd=None):
    """screener: {"type": "command", "cmd": ...} or {"type": "http", "url": ...}."""
    if screener.get("type") == "command":
        rows = run_command(screener["cmd"], cvs_dir, jd_path, top_k, cwd=cwd)
    elif screener.get("type") == "http":
        rows = run_http(screener["url"], cvs_dir, jd_path, top_k)
    else:
        raise ScreenerError(f"unknown screener type: {screener.get('type')}")
    return normalise(rows, top_k)


def write_ranking(rows, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cv_id", "score", "rank", "shortlisted"])
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="Run a screening tool as a black box.")
    ap.add_argument("--cvs", required=True, help="folder of CVs to screen (normally the redacted folder)")
    ap.add_argument("--jd", required=True, help="job description file")
    ap.add_argument("--out", required=True, help="where to write the ranking CSV")
    ap.add_argument("--top-k", type=int, default=10, help="shortlist size")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--cmd", help="command template with {cvs} {jd} {out} {top_k}")
    group.add_argument("--url", help="HTTP endpoint of a screening service")
    args = ap.parse_args()

    screener = {"type": "command", "cmd": args.cmd} if args.cmd else {"type": "http", "url": args.url}
    try:
        rows = run_screener(screener, args.cvs, args.jd, args.top_k)
    except (ScreenerError, subprocess.TimeoutExpired) as e:
        sys.exit(json.dumps({"error": str(e)}))
    write_ranking(rows, args.out)
    print(json.dumps({"screener": screener, "cvs_scored": len(rows),
                      "shortlisted": sum(r["shortlisted"] for r in rows), "out": args.out}, indent=2))


if __name__ == "__main__":
    main()
