#!/usr/bin/env python
"""Build the static demo page from the saved results.

Reads the outputs written by demo/run_all_scenarios.py and writes:
  site/demo.html   page body, as published to a claude.ai Artifact
  docs/index.html  the same page as a full HTML document, for GitHub Pages

The page needs no server: every number, CV and report is embedded in it.
Usage: python demo/build_demo_page.py   (after python demo/run_all_scenarios.py)
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "set1": {"label": "Dataset 1: Data Analyst", "short": "30 CVs: 15 women, 15 men, 5 twin pairs, one CV layout",
             "raw": "data/cvs_raw", "labels": "data/gender_labels.csv", "out": "outputs", "top_k": 10},
    "set2": {"label": "Dataset 2: Software Developer",
             "short": "40 CVs: 16 women, 24 men, 4 twin pairs, three CV layouts (UK, Indian biodata, US)",
             "raw": "data2/cvs_raw", "labels": "data2/gender_labels.csv", "out": "outputs/dataset2", "top_k": 12},
}
TOOLS = {
    "screener_a": {"folder": "screener_a", "label": "Screener A",
                   "about": "An old program the HR team runs on a folder of CVs. Secretly adds points for male "
                            "words, takes points off for female words, and takes 10 points off any career gap."},
    "control": {"folder": "control", "label": "Control (bias off)",
                "about": "The same program with its hidden rules switched off: what a fair result looks like."},
    "vendor_b": {"folder": "vendor_b", "label": "Vendor B",
                 "about": "A cloud service that claims to be gender-blind. It never reads names or pronouns, "
                          "but takes 12 points off career gaps and 8 off part-time work."},
}
GENDER = {"female": "female", "male": "male", "f": "female", "m": "male"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ranking(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{"cv_id": r["cv_id"], "score": float(r["score"]), "rank": int(r["rank"]),
                 "shortlisted": r["shortlisted"] == "True"} for r in csv.DictReader(f)]


def main():
    data = {"datasets": {}, "tools": {k: {"label": v["label"], "about": v["about"]} for k, v in TOOLS.items()}}
    for key, ds in DATASETS.items():
        out = ROOT / ds["out"]
        with open(ROOT / ds["labels"], newline="", encoding="utf-8") as f:
            labels = {r["cv_id"]: GENDER.get(r["gender"].strip().lower(), r["gender"]) for r in csv.DictReader(f)}
        red_dir = out / "screener_a" / "cvs_redacted"
        log = load(out / "screener_a" / "redaction_log.json")
        changes = {}
        for c in log["changes"]:
            changes.setdefault(c["cv_id"], []).append([c["line"], c["original"], c["replacement"], c["rule"]])
        cvs = {p.stem: {"raw": p.read_text(encoding="utf-8"),
                        "red": (red_dir / p.name).read_text(encoding="utf-8"),
                        "changes": changes.get(p.stem, [])}
               for p in sorted((ROOT / ds["raw"]).glob("*.txt"))}
        leaks = load(out / "screener_a" / "leak_check.json")
        runs = {}
        for tkey, tool in TOOLS.items():
            d = out / tool["folder"]
            runs[tkey] = {tag: {"audit": load(d / f"audit_{tag}.json"),
                                "probe": load(d / f"proxy_probe_{tag}.json"),
                                "ranking": ranking(d / f"ranking_{tag}.csv"),
                                "report": (d / f"audit_report_{tag}.md").read_text(encoding="utf-8")}
                          for tag in ("raw", "redacted")}
        data["datasets"][key] = {"label": ds["label"], "short": ds["short"], "top_k": ds["top_k"],
                                 "labels": labels, "cvs": cvs, "redaction": log["summary"],
                                 "leaks": {"count": leaks["leak_count"],
                                           "one_sided": leaks.get("one_sided_terms", [])},
                                 "runs": runs}

    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    body = (ROOT / "demo" / "demo_page_template.html").read_text(encoding="utf-8").replace("__DATA__", payload)
    (ROOT / "site").mkdir(exist_ok=True)
    (ROOT / "site" / "demo.html").write_text(body, encoding="utf-8")
    full = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            "</head>\n<body>\n" + body + "\n</body>\n</html>\n")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(full, encoding="utf-8")
    print(json.dumps({"site/demo.html": len(body), "docs/index.html": len(full)}))


if __name__ == "__main__":
    main()
