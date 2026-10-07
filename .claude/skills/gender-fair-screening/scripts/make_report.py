#!/usr/bin/env python
"""Stage 6: fill in the audit report template from the JSON results.

Usage:
  python make_report.py --audit outputs/audit_redacted.json [--probe outputs/proxy_probe.json] \
      [--redaction outputs/redaction_log.json] [--leaks outputs/leak_check.json] \
      --role "Data Analyst" --tool "demo/biased_screener.py" --out outputs/audit_report_redacted.md

Every number in the report comes from the JSON files; nothing is computed by
hand. The recommendation follows fixed rules:

  Do not use this shortlist   four-fifths check fails, or any twin pair scored differently
  Proceed with conditions     otherwise, if a proxy penalty, a remaining leak or a
                              sample-size warning was found
  Proceed                     none of the above

The reviewer (human, or the agent following SKILL.md) may add notes under
"Reviewer notes" but should not change the numbers.
Standard library only. Other front ends import build_report().
"""
import argparse
import json
from datetime import date
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "audit_report.md"
SIGNAL_NAMES = {"career_gap": "Career break or gap", "part_time": "Part-time work"}


def pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def recommend(audit, probe, leaks):
    twins = audit["twin_test"]
    twin_fail = twins["pairs"] and twins["identical"] < twins["pairs"]
    penalised = [s for s, v in (probe or {}).get("summary", {}).items() if v["cvs_penalised"]]
    leak_count = (leaks or {}).get("leak_count", 0)
    if audit["four_fifths"] == "FAIL" or twin_fail:
        why = []
        if audit["four_fifths"] == "FAIL":
            why.append(f"the selection rate for {audit['lower_rate_group']} candidates is "
                       f"{audit['impact_ratio']:.2f} of the rate for {audit['higher_rate_group']} "
                       "candidates, below the four-fifths (0.80) threshold")
        if twin_fail:
            why.append(f"{twins['pairs'] - twins['identical']} of {twins['pairs']} twin pairs, whose CVs "
                       "differ only in gender markers, received different scores")
        reason = "This shortlist shows evidence of adverse impact: " + "; and ".join(why) + "."
        if penalised:
            counts = []
            for s in penalised:
                by_gender = audit.get("proxy_signals", {}).get(s, {}).get("by_gender", {})
                if by_gender:
                    counts.append(f"{SIGNAL_NAMES[s].lower()}: "
                                  + ", ".join(f"{n} {g}" for g, n in by_gender.items()))
            reason += (" The probe also found that the screener penalises "
                       + " and ".join(SIGNAL_NAMES[s].lower() for s in penalised)
                       + (f" (candidates affected, {'; '.join(counts)})" if counts else "") + ".")
        else:
            reason += " The cause must be found and fixed before the shortlist is used."
        return "Do not use this shortlist", reason
    if penalised or leak_count or audit.get("sample_size_warning"):
        parts = []
        if penalised:
            parts.append("the screener penalises " + " and ".join(SIGNAL_NAMES[s].lower() for s in penalised))
        if leak_count:
            parts.append(f"{leak_count} gender markers survived redaction")
        if audit.get("sample_size_warning"):
            parts.append("the candidate pool is too small for firm conclusions")
        return ("Proceed with conditions",
                "The shortlist passes the four-fifths check and the twin test, but " + "; ".join(parts)
                + ". The conditions below must be met before it is relied on.")
    return ("Proceed", "The shortlist passes the four-fifths check and the twin test, and no proxy "
                       "penalty was found. A human reviewer still makes the final decision.")


def build_report(audit, role, tool, cv_set, probe=None, redaction=None, leaks=None,
                 report_date=None, reviewer_notes=None):
    g = audit["groups"]
    men = "male" if "male" in g else sorted(g)[0]
    women = "female" if "female" in g else sorted(g)[1]
    rec, reason = recommend(audit, probe, leaks)

    rows = [
        f"| Candidates | {g[men]['candidates']} | {g[women]['candidates']} | |",
        f"| Shortlisted | {g[men]['shortlisted']} | {g[women]['shortlisted']} | |",
        f"| Selection rate | {pct(g[men]['selection_rate'])} | {pct(g[women]['selection_rate'])} | |",
        f"| Impact ratio | | | {audit['impact_ratio']:.2f}: **{audit['four_fifths']}** at 0.80 |",
        f"| Mean score | {g[men]['mean_score']:.1f} | {g[women]['mean_score']:.1f} | "
        f"gap {audit['mean_score_gap_men_minus_women']:+.1f} points (men minus women) |",
    ]

    twins = audit["twin_test"]
    twin_summary = f"{twins['pairs']} pairs, {twins['identical']} scored identically."
    if twins["pairs"]:
        twin_table = "| Pair | Man | Woman | Score (man) | Score (woman) | Difference |\n|---|---|---|---|---|---|\n" + \
            "\n".join(f"| {t['pair']} | {t['man']} | {t['woman']} | {t['score_man']} | {t['score_woman']} | "
                      f"{t['difference_man_minus_woman']:+.1f} |" for t in twins["details"])
    else:
        twin_table = ""

    p = audit["fisher_exact_p"]
    significance = (f"Fisher's exact test p = {p:.3f}. "
                    + ("A difference this large would be unlikely by chance alone (p < 0.05). "
                       if p < 0.05 else
                       "With this few candidates the difference could be chance (p ≥ 0.05), so the "
                       "four-fifths result is a warning sign, not proof. ")
                    + "The four-fifths rule is a rule of thumb and is unreliable on small samples.")

    if redaction:
        s = redaction["summary"]
        by_rule = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in s["changes_by_rule"].items())
        redaction_summary = f"{s['files_redacted']} CVs redacted, {s['changes']} changes ({by_rule})."
        if leaks is not None:
            redaction_summary += (f" Leak check: {leaks['leak_count']} markers left after redaction"
                                  f" across {leaks['files_checked']} CVs.")
            one_sided = leaks.get("one_sided_terms") or []
            if one_sided:
                redaction_summary += (" Terms used for one gender only, for human review: "
                                      + ", ".join(f"\"{t['term']}\" ({t['cvs']} CVs, {t['only_in']} only)"
                                                  for t in one_sided) + ".")
    else:
        redaction_summary = ("Not applied. The CVs were screened with names, pronouns and other gender "
                             "markers visible. This is the baseline the fairness layer is compared with.")

    proxy_rows, proxy_note = [], ""
    signals = audit.get("proxy_signals", {})
    probe_summary = (probe or {}).get("summary", {})
    for sig in sorted(set(signals) | set(probe_summary)):
        info = signals.get(sig, {})
        who = ", ".join(f"{n} {k}" for k, n in info.get("by_gender", {}).items()) or "n/a"
        ps = probe_summary.get(sig)
        if ps and ps["cvs_tested"]:
            penalty = (f"{ps['cvs_penalised']} of {ps['cvs_tested']} CVs penalised, mean "
                       f"{ps['mean_penalty_points']:.1f} points")
        elif ps:
            penalty = "no CVs to test"
        else:
            penalty = "not probed"
        penalised = bool(ps and ps["cvs_penalised"])
        job_reason = "Not established: a human must answer" if penalised else "n/a"
        action = ("Remove the penalty or justify it in writing; review affected CVs by hand"
                  if penalised else "Keep monitoring")
        proxy_rows.append(f"| {SIGNAL_NAMES.get(sig, sig)} | {who} | {penalty} | {job_reason} | {action} |")
    if not proxy_rows:
        proxy_rows.append("| none checked | | | | |")
    if signals:
        proxy_note = ("Selection rates for candidates with and without each signal: "
                      + "; ".join(f"{SIGNAL_NAMES.get(s, s).lower()} {pct(v['selection_rate_with_signal'])} "
                                  f"with, {pct(v['selection_rate_without_signal'])} without"
                                  for s, v in signals.items())
                      + ". Rates alone can hide a penalty in small pools; the probe tests it directly.")

    conditions = []
    if audit["four_fifths"] == "FAIL":
        conditions.append("Do not shortlist from this ranking. Find the cause of the gap and re-run the audit.")
    if twins["pairs"] and twins["identical"] < twins["pairs"]:
        conditions.append("The tool reacts to gender markers. Screen only redacted CVs, or replace the tool.")
    for sig, ps in probe_summary.items():
        if ps["cvs_penalised"]:
            conditions.append(f"Ask the vendor or tool owner to remove the {SIGNAL_NAMES.get(sig, sig).lower()} "
                              "penalty, or document a job-related reason for it. Until then, review every "
                              f"affected CV by hand ({', '.join(signals.get(sig, {}).get('cv_ids', [])) or 'see probe'}).")
    if leaks and leaks.get("leak_count"):
        conditions.append("Fix the remaining gender markers in the redacted CVs and re-run the leak check.")
    if audit.get("sample_size_warning"):
        conditions.append("Repeat the audit on a larger pool, or across several hiring rounds, before "
                          "drawing firm conclusions.")
    conditions.append("A named person reviews this report and makes the final shortlist decision.")

    values = {
        "role": role, "date": report_date or date.today().isoformat(),
        "candidates": audit["candidates"], "shortlist_size": audit["shortlist_size"],
        "tool": tool, "cv_set": cv_set, "recommendation": rec, "recommendation_reason": reason,
        "results_rows": "\n".join(rows), "twin_summary": twin_summary, "twin_table": twin_table,
        "significance": significance, "redaction_summary": redaction_summary,
        "proxy_rows": "\n".join(proxy_rows), "proxy_note": proxy_note,
        "conditions": "\n".join(f"{i}. {c}" for i, c in enumerate(conditions, start=1)),
        "sample_note": (" Here at least one group has fewer than 30 candidates."
                        if audit.get("sample_size_warning") else ""),
        "reviewer_notes": reviewer_notes or "_None yet. The reviewer adds notes here; the numbers above are not edited._",
    }
    text = TEMPLATE.read_text(encoding="utf-8")
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text, rec


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def main():
    ap = argparse.ArgumentParser(description="Fill in the audit report template.")
    ap.add_argument("--audit", required=True, help="JSON from audit_shortlist.py")
    ap.add_argument("--probe", help="JSON from proxy_probe.py")
    ap.add_argument("--redaction", help="redaction log JSON from redact_cv.py (omit for a raw-CV audit)")
    ap.add_argument("--leaks", help="JSON from leak_check.py")
    ap.add_argument("--role", default="Data Analyst")
    ap.add_argument("--tool", default="screening tool")
    ap.add_argument("--cv-set", help="label for the CVs screened, e.g. 'redacted' or 'raw'")
    ap.add_argument("--date", help="report date (default today)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cv_set = args.cv_set or ("redacted" if args.redaction else "raw (gender markers visible)")
    text, rec = build_report(load(args.audit), args.role, args.tool, cv_set, load(args.probe),
                             load(args.redaction), load(args.leaks), args.date)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(text, encoding="utf-8")
    print(json.dumps({"report": args.out, "recommendation": rec}))


if __name__ == "__main__":
    main()
