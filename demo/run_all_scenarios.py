#!/usr/bin/env python
"""Re-run every saved scenario: both datasets x all three screening tools.

Writes the full pipeline output for each scenario and a one-file summary:
  outputs/screener_a, outputs/control, outputs/vendor_b       dataset 1
  outputs/dataset2/screener_a, .../control, .../vendor_b      dataset 2
  outputs/summary.json                                        headline numbers for every scenario

Vendor B is called over HTTP if its service is running, otherwise through its
offline copy (same scoring), so this script needs no servers.

Usage: python demo/run_all_scenarios.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "gender-fair-screening" / "scripts"))
from pipeline import run  # noqa: E402

REGISTRY = json.loads((ROOT / "integration" / "screeners.json").read_text(encoding="utf-8"))
DATASETS = {
    "dataset1": {"cvs": "data/cvs_raw", "jd": "data/job_description.md", "labels": "data/gender_labels.csv",
                 "role": "Data Analyst", "top_k": 10, "out": "outputs"},
    "dataset2": {"cvs": "data2/cvs_raw", "jd": "data2/job_description.md", "labels": "data2/gender_labels.csv",
                 "role": "Software Developer", "top_k": 12, "out": "outputs/dataset2"},
}
FOLDER = {"screener_a": "screener_a", "screener_a_control": "control", "vendor_b": "vendor_b"}


def main():
    summary = []
    for ds_name, ds in DATASETS.items():
        for tool, folder in FOLDER.items():
            scr = dict(REGISTRY[tool])
            res = run(ROOT / ds["cvs"], ROOT / ds["jd"], ROOT / ds["labels"], scr, ROOT / ds["out"] / folder,
                      tool_name=scr["label"], role=ds["role"], top_k=ds["top_k"], cwd=ROOT)
            row = {"dataset": ds_name, "role": ds["role"], "tool": tool, "tool_label": scr["label"],
                   "out_dir": f"{ds['out']}/{folder}", "leaks": res["leak_check"]["leak_count"],
                   "redaction_changes": res["redaction"]["summary"]["changes"]}
            for tag in ("raw", "redacted"):
                a, p = res[tag]["audit"], res[tag]["probe"]["summary"]
                row[tag] = {"men": f"{a['groups']['male']['shortlisted']}/{a['groups']['male']['candidates']}",
                            "women": f"{a['groups']['female']['shortlisted']}/{a['groups']['female']['candidates']}",
                            "impact_ratio": a["impact_ratio"], "four_fifths": a["four_fifths"],
                            "fisher_p": a["fisher_exact_p"],
                            "twins": f"{a['twin_test']['identical']}/{a['twin_test']['pairs']}",
                            "penalties": {s: v["mean_penalty_points"] for s, v in p.items() if v["cvs_penalised"]},
                            "recommendation": res[tag]["recommendation"]}
            summary.append(row)
            r, d = row["raw"], row["redacted"]
            print(f"{ds_name:9} {tool:19} raw {r['impact_ratio']:.2f} {r['four_fifths']} twins {r['twins']} | "
                  f"redacted {d['impact_ratio']:.2f} {d['four_fifths']} twins {d['twins']} "
                  f"penalties {d['penalties']} -> {d['recommendation']}")
    (ROOT / "outputs" / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
