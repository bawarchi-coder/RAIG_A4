#!/usr/bin/env python
"""All stages in one call, for front ends that are not an agent.

The agent (SKILL.md) runs the stages one by one so it can inspect and fix
results between them. The standalone app, the HTTP API and this command
line use run() instead. Same scripts, same numbers.

Usage:
  python pipeline.py --raw data/cvs_raw --jd data/job_description.md --labels data/gender_labels.csv \
      --out outputs/screener_a (--cmd "<screener command template>" | --url <endpoint>) \
      [--tool-name "Screener A"] [--top-k 10] [--no-baseline]

Writes to --out:
  ranking_raw.csv, audit_raw.json, proxy_probe_raw.json, audit_report_raw.md   baseline: tool on raw CVs
  cvs_redacted/, redaction_log.json, leak_check.json                            stages 1-2
  ranking_redacted.csv, audit_redacted.json, proxy_probe_redacted.json,
  audit_report_redacted.md                                                      stages 3-6
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_shortlist import audit, read_csv  # noqa: E402
from leak_check import check_texts, one_sided_terms, raw_names  # noqa: E402
from make_report import build_report  # noqa: E402
from proxy_probe import probe  # noqa: E402
from redact_cv import redact_folder  # noqa: E402
from screener_adapter import run_screener, write_ranking  # noqa: E402


def _texts(folder):
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(Path(folder).glob("*.txt"))}


def _dump(obj, path):
    Path(path).write_text(json.dumps(obj, indent=2), encoding="utf-8")


def screen_and_audit(cvs_dir, jd, labels, screener, out, tag, top_k, cwd):
    ranking = run_screener(screener, cvs_dir, jd, top_k, cwd=cwd)
    write_ranking(ranking, out / f"ranking_{tag}.csv")
    result = audit(ranking, labels, _texts(cvs_dir))
    _dump(result, out / f"audit_{tag}.json")
    pr = probe(cvs_dir, jd, screener, cwd=cwd)
    _dump(pr, out / f"proxy_probe_{tag}.json")
    return ranking, result, pr


def run(raw_dir, jd, labels_csv, screener, out_dir, tool_name="screening tool", role="Data Analyst",
        top_k=10, baseline=True, cwd=None, report_date=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    labels = read_csv(labels_csv) if labels_csv else None
    res = {"out_dir": str(out), "tool": tool_name}

    # Baseline: the tool as it is used today, on raw CVs
    if baseline and labels:
        ranking, aud, pr = screen_and_audit(raw_dir, jd, labels, screener, out, "raw", top_k, cwd)
        report, rec = build_report(aud, role, tool_name, "raw (gender markers visible)", pr,
                                   report_date=report_date)
        (out / "audit_report_raw.md").write_text(report, encoding="utf-8")
        res["raw"] = {"ranking": ranking, "audit": aud, "probe": pr, "report": report, "recommendation": rec}

    # Stage 1: redact
    red_dir = out / "cvs_redacted"
    summary = redact_folder(raw_dir, red_dir, out / "redaction_log.json")
    redaction = json.loads((out / "redaction_log.json").read_text(encoding="utf-8"))

    # Stage 2: leak check
    red_texts = _texts(red_dir)
    leaks = check_texts(red_texts, raw_names(raw_dir))
    leak_result = {"files_checked": len(red_texts), "leak_count": len(leaks), "leaks": leaks}
    if labels:
        leak_result["one_sided_terms"] = one_sided_terms(red_texts, {r["cv_id"]: r["gender"] for r in labels})
    _dump(leak_result, out / "leak_check.json")
    res["redaction"] = {"summary": summary, "changes": redaction["changes"]}
    res["leak_check"] = leak_result

    # Stages 3-6: blind screening, audit, proxy probe, report
    if labels:
        ranking, aud, pr = screen_and_audit(red_dir, jd, labels, screener, out, "redacted", top_k, cwd)
        report, rec = build_report(aud, role, tool_name, "redacted", pr, redaction, leak_result,
                                   report_date=report_date)
        (out / "audit_report_redacted.md").write_text(report, encoding="utf-8")
        res["redacted"] = {"ranking": ranking, "audit": aud, "probe": pr, "report": report,
                           "recommendation": rec}
    else:
        ranking = run_screener(screener, red_dir, jd, top_k, cwd=cwd)
        write_ranking(ranking, out / "ranking_redacted.csv")
        res["redacted"] = {"ranking": ranking, "note": "no labels supplied, so no audit"}
    return res


def main():
    ap = argparse.ArgumentParser(description="Run every stage of the fairness layer in one go.")
    ap.add_argument("--raw", required=True)
    ap.add_argument("--jd", required=True)
    ap.add_argument("--labels")
    ap.add_argument("--out", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--cmd")
    group.add_argument("--url")
    ap.add_argument("--tool-name", default="screening tool")
    ap.add_argument("--role", default="Data Analyst")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--no-baseline", action="store_true", help="skip the run on raw CVs")
    ap.add_argument("--date", help="report date (default today)")
    args = ap.parse_args()

    screener = {"type": "command", "cmd": args.cmd} if args.cmd else {"type": "http", "url": args.url}
    res = run(args.raw, args.jd, args.labels, screener, args.out, args.tool_name, args.role,
              args.top_k, not args.no_baseline, report_date=args.date)
    brief = {"out_dir": res["out_dir"], "redaction": res["redaction"]["summary"],
             "leaks": res["leak_check"]["leak_count"]}
    for tag in ("raw", "redacted"):
        if tag in res and "audit" in res[tag]:
            a = res[tag]["audit"]
            brief[tag] = {"impact_ratio": a["impact_ratio"], "four_fifths": a["four_fifths"],
                          "twins_identical": f"{a['twin_test']['identical']}/{a['twin_test']['pairs']}",
                          "proxy_penalties": {s: v["mean_penalty_points"]
                                              for s, v in res[tag]["probe"]["summary"].items()},
                          "recommendation": res[tag]["recommendation"]}
    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
