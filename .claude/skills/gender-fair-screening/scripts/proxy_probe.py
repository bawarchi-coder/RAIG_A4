#!/usr/bin/env python
"""Stage 5: test whether the screener penalises proxy signals.

Comparing selection rates cannot show why a gap exists, and on small
candidate pools it often cannot show a gap at all. This probe asks the
screener directly. For every CV with a proxy signal it builds a
counterfactual copy without that signal and nothing else changed, scores
originals and copies in one run, and reports the score difference.

  career_gap  copy has no career break line; earlier jobs are moved later so
              total experience is identical
  part_time   copy is identical except the words "part-time" are removed

A positive change means the signal was costing the candidate points.

Usage:
  python proxy_probe.py --cvs data/cvs_redacted --jd data/job_description.md \
      (--cmd "<screener command template>" | --url <screener endpoint>) [--out outputs/proxy_probe.json]

Standard library only. Other front ends import probe().
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_signals import COUNTERFACTUALS, signals  # noqa: E402
from screener_adapter import ScreenerError, run_screener  # noqa: E402

THRESHOLD = 0.5  # score points; smaller changes are treated as noise


def probe(cvs_dir, jd_path, screener, cwd=None):
    texts = {p.stem: p.read_text(encoding="utf-8") for p in sorted(Path(cvs_dir).glob("*.txt"))}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        planned = []
        for cv_id, text in texts.items():
            (tmp / f"{cv_id}.txt").write_text(text, encoding="utf-8")
            flags = signals(text)
            for sig, make in COUNTERFACTUALS.items():
                if flags.get(sig):
                    alt_id = f"{cv_id}__no_{sig}"
                    (tmp / f"{alt_id}.txt").write_text(make(text), encoding="utf-8")
                    planned.append((cv_id, sig, alt_id))
        scores = {r["cv_id"]: r["score"] for r in run_screener(screener, tmp, jd_path, top_k=0, cwd=cwd)}

    tests = []
    for cv_id, sig, alt_id in planned:
        change = round(scores[alt_id] - scores[cv_id], 2)
        tests.append({"cv_id": cv_id, "signal": sig, "score_with_signal": scores[cv_id],
                      "score_without_signal": scores[alt_id], "change": change,
                      "penalised": change > THRESHOLD})
    summary = {}
    for sig in COUNTERFACTUALS:
        rows = [t for t in tests if t["signal"] == sig]
        summary[sig] = {
            "cvs_tested": len(rows),
            "cvs_penalised": sum(t["penalised"] for t in rows),
            "mean_penalty_points": round(sum(t["change"] for t in rows) / len(rows), 2) if rows else None,
        }
    flagged = [s for s, v in summary.items() if v["cvs_penalised"]]
    return {"cvs_probed": len(texts), "summary": summary, "tests": tests,
            "finding": (f"The screener penalises: {', '.join(flagged)}. Ask whether there is a "
                        "job-related reason; if not, the penalty must be removed."
                        if flagged else "No proxy penalty detected for the signals tested.")}


def main():
    ap = argparse.ArgumentParser(description="Test whether a screener penalises proxy signals.")
    ap.add_argument("--cvs", required=True)
    ap.add_argument("--jd", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--cmd", help="screener command template with {cvs} {jd} {out} {top_k}")
    group.add_argument("--url", help="screener HTTP endpoint")
    ap.add_argument("--out", help="also write the result to this JSON file")
    args = ap.parse_args()

    screener = {"type": "command", "cmd": args.cmd} if args.cmd else {"type": "http", "url": args.url}
    try:
        result = probe(args.cvs, args.jd, screener)
    except ScreenerError as e:
        sys.exit(json.dumps({"error": str(e)}))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
