#!/usr/bin/env python
"""Stage 4: audit a shortlist for gender gaps.

Usage:
  python audit_shortlist.py --ranking outputs/ranking_redacted.csv --labels data/gender_labels.csv \
      [--cvs data/cvs_redacted] [--out outputs/audit_redacted.json]

--ranking  CSV with cv_id, score, shortlisted (rank optional)
--labels   CSV with cv_id, gender, twin_pair_id. Audit only: never give it to the screener.
--cvs      optional folder of the CVs that were screened, to count proxy signals

Computes (see ../references/thresholds.md for how to read them):
  selection rate by gender   shortlisted / candidates, per gender
  impact ratio               lower selection rate / higher selection rate
  four-fifths check          PASS if the impact ratio is 0.80 or above
  Fisher's exact test        two-sided p-value for the shortlist-by-gender table;
                             more reliable than the four-fifths rule on small samples
  mean score gap             mean score of men minus mean score of women
  twin test                  score difference within each twin pair (should be 0)
  proxy signals              with --cvs: who carries each signal and how often
                             candidates with it are shortlisted
  sample-size warning        if any group has fewer than 30 candidates

Uses only the Python standard library. Other front ends import audit().
"""
import argparse
import csv
import json
import sys
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_signals import signals  # noqa: E402

FOUR_FIFTHS = 0.8
MIN_GROUP = 30


def truthy(v):
    return str(v).strip().lower() in {"true", "1", "yes", "y", "t"}


def fisher_exact(a, b, c, d):
    """Two-sided Fisher's exact test for [[a, b], [c, d]]."""
    row1, row2, col1, n = a + b, c + d, a + c, a + b + c + d

    def p(x):
        return comb(row1, x) * comb(row2, col1 - x) / comb(n, col1)

    observed = p(a)
    lo, hi = max(0, col1 - row2), min(row1, col1)
    return min(1.0, sum(p(x) for x in range(lo, hi + 1) if p(x) <= observed * (1 + 1e-9)))


def audit(ranking, labels, cv_texts=None):
    """ranking: [{cv_id, score, shortlisted}], labels: [{cv_id, gender, twin_pair_id}].

    cv_texts: optional {cv_id: text} of the CVs that were screened.
    """
    lab = {r["cv_id"]: r for r in labels}
    rows = [r for r in ranking if r["cv_id"] in lab]
    missing = sorted({r["cv_id"] for r in ranking} - set(lab))
    groups = sorted({lab[r["cv_id"]]["gender"] for r in rows})
    if len(groups) != 2:
        return {"error": f"expected two gender groups in the labels, found {groups}"}

    stats = {}
    for g in groups:
        members = [r for r in rows if lab[r["cv_id"]]["gender"] == g]
        chosen = [r for r in members if truthy(r["shortlisted"])]
        scores = [float(r["score"]) for r in members]
        stats[g] = {"candidates": len(members), "shortlisted": len(chosen),
                    "selection_rate": round(len(chosen) / len(members), 4) if members else None,
                    "mean_score": round(sum(scores) / len(scores), 2) if scores else None}

    rates = {g: stats[g]["selection_rate"] for g in groups}
    high, low = max(groups, key=lambda g: rates[g]), min(groups, key=lambda g: rates[g])
    ratio = round(rates[low] / rates[high], 4) if rates[high] else None
    g1, g2 = groups
    a, c = stats[g1]["shortlisted"], stats[g2]["shortlisted"]
    b, d = stats[g1]["candidates"] - a, stats[g2]["candidates"] - c
    men = "male" if "male" in groups else g1
    women = "female" if "female" in groups else g2

    # Twin test
    score = {r["cv_id"]: float(r["score"]) for r in rows}
    pairs = {}
    for cv_id, r in lab.items():
        t = (r.get("twin_pair_id") or "").strip()
        if t and cv_id in score:
            pairs.setdefault(t, {})[r["gender"]] = cv_id
    twin_rows = []
    for t in sorted(pairs):
        p = pairs[t]
        if men in p and women in p:
            diff = round(score[p[men]] - score[p[women]], 2)
            twin_rows.append({"pair": t, "man": p[men], "woman": p[women],
                              "score_man": score[p[men]], "score_woman": score[p[women]],
                              "difference_man_minus_woman": diff, "identical": abs(diff) < 1e-9})

    result = {
        "candidates": len(rows),
        "shortlist_size": sum(1 for r in rows if truthy(r["shortlisted"])),
        "groups": stats,
        "higher_rate_group": high,
        "lower_rate_group": low,
        "impact_ratio": ratio,
        "four_fifths_threshold": FOUR_FIFTHS,
        "four_fifths": None if ratio is None else ("PASS" if ratio >= FOUR_FIFTHS else "FAIL"),
        "fisher_exact_p": round(fisher_exact(a, b, c, d), 4),
        "mean_score_gap_men_minus_women": round(stats[men]["mean_score"] - stats[women]["mean_score"], 2),
        "twin_test": {"pairs": len(twin_rows),
                      "identical": sum(1 for t in twin_rows if t["identical"]),
                      "details": twin_rows},
        "sample_size_warning": (f"Fewer than {MIN_GROUP} candidates in at least one group. "
                                "Treat these results as indicative, not conclusive."
                                if min(s["candidates"] for s in stats.values()) < MIN_GROUP else None),
    }
    if missing:
        result["unlabelled_cvs"] = missing

    if cv_texts:
        proxy = {}
        flags = {cv: signals(t) for cv, t in cv_texts.items() if cv in lab}
        for sig in ("career_gap", "part_time"):
            has = [r for r in rows if flags.get(r["cv_id"], {}).get(sig)]
            lacks = [r for r in rows if r["cv_id"] in flags and not flags[r["cv_id"]].get(sig)]
            by_gender = {g: sum(1 for r in has if lab[r["cv_id"]]["gender"] == g) for g in groups}
            sel_has = sum(1 for r in has if truthy(r["shortlisted"]))
            sel_lacks = sum(1 for r in lacks if truthy(r["shortlisted"]))
            proxy[sig] = {
                "cvs_with_signal": len(has),
                "by_gender": by_gender,
                "shortlisted_with_signal": sel_has,
                "selection_rate_with_signal": round(sel_has / len(has), 4) if has else None,
                "selection_rate_without_signal": round(sel_lacks / len(lacks), 4) if lacks else None,
                "cv_ids": sorted(r["cv_id"] for r in has),
            }
        result["proxy_signals"] = proxy
    return result


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser(description="Audit a shortlist for gender gaps.")
    ap.add_argument("--ranking", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--cvs", help="folder of the CVs that were screened (for proxy signals)")
    ap.add_argument("--out", help="also write the result to this JSON file")
    args = ap.parse_args()

    texts = None
    if args.cvs:
        texts = {p.stem: p.read_text(encoding="utf-8") for p in Path(args.cvs).glob("*.txt")}
    result = audit(read_csv(args.ranking), read_csv(args.labels), texts)
    result = {"ranking_file": args.ranking, **result}
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
