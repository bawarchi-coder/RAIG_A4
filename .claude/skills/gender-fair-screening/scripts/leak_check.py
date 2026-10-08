#!/usr/bin/env python
"""Stage 2: check redacted CVs for gender markers that survived redaction.

Usage:
  python leak_check.py --input data/cvs_redacted [--raw data/cvs_raw] [--labels data/gender_labels.csv] [--out outputs/leak_check.json]

Checks:
  * every redacted line against the marker lexicon (pronouns, titles,
    gendered words, family names, personal fields, break reasons, gendered
    job words and organisations)
  * every first name and surname found in the raw CVs (with --raw)
  * one-sided terms (with --labels): words or placeholders that appear in at
    least 3 CVs of one gender and none of the other. These can reveal gender
    even when no single word is a marker, for example a placeholder that is
    only ever used for women. With small samples some will be chance, so
    they are listed for human review, not counted as leaks.

Prints {"files_checked": n, "leak_count": n, "leaks": [...], "one_sided_terms": [...]}.
Uses only the Python standard library.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_signals import normalise_gender  # noqa: E402
from redact_cv import TITLES, name_from, name_tokens  # noqa: E402

LEXICON = [
    ("pronoun", re.compile(r"\b(?:he|she|him|her|his|hers|himself|herself|he's|she's)\b", re.I)),
    ("title", re.compile(rf"\b{TITLES}(?=\s|$)")),
    ("gendered_word", re.compile(
        r"\b(?:women|woman|men's|man|ladies|lady|girls?|boys?|female|male|feminine|masculine|"
        r"womens|mens|mother|father|wife|husband|son|daughter)(?:'s|’s|'|’)?(?![\w])", re.I)),
    ("family_or_status", re.compile(
        r"\b(?:spouse|married|unmarried|widow(?:ed|er)?|divorced|[SDW]/o)\b", re.I)),
    ("personal_field", re.compile(r"\b(?:date of birth|d\.o\.b|gender|photo(?:graph)?|pronouns?|n[ée]e)\b", re.I)),
    ("break_reason", re.compile(
        r"\b(?:maternity|paternity|pregnan\w*|child\s?care|parental leave|homemaker|housewife|"
        r"househusband)\b", re.I)),
    ("gendered_job_word", re.compile(
        r"\b(?:chairman|chairwoman|salesman|saleswoman|salesgirl|waitress|waiter|hostess|busboy|spokesman|"
        r"spokeswoman|foreman|forewoman|businessman|businesswoman|policeman|policewoman|"
        r"stewardess|head girl|head boy)\b", re.I)),
    ("gendered_organisation", re.compile(
        r"\b(?:sorority|fraternity|girls who code|women who code|women in \w+)\b", re.I)),
]
STOP = {"the", "and", "for", "with", "from", "into", "that", "this", "used", "across", "their",
        "they", "have", "are", "has", "was", "were", "include", "includes", "years", "year"}


def raw_names(raw_dir):
    names = set()
    for p in Path(raw_dir).glob("*.txt"):
        tokens, _ = name_tokens(name_from(p.read_text(encoding="utf-8").splitlines()))
        names.update(t for t in tokens if len(t) >= 3)
    return names


def check_texts(texts, names=()):
    """texts: {cv_id: redacted text}. Returns a list of leak dicts."""
    leaks = []
    name_re = re.compile(r"\b(" + "|".join(map(re.escape, sorted(names))) + r")\b") if names else None
    lower_names = [nm.lower() for nm in names if len(nm) >= 4]
    for cv_id, text in texts.items():
        for n, line in enumerate(text.splitlines(), start=1):
            for rule, pattern in LEXICON:
                for m in pattern.finditer(line):
                    leaks.append({"cv_id": cv_id, "line": n, "marker": m.group(0),
                                  "rule": rule, "text": line.strip()})
            if name_re:
                for m in name_re.finditer(line):
                    leaks.append({"cv_id": cv_id, "line": n, "marker": m.group(0),
                                  "rule": "candidate_name", "text": line.strip()})
                # names hidden inside web addresses or handles, e.g. www.priyaiyer.dev
                for tok in re.findall(r"[^\s|,;()]*[./@][^\s|,;()]*", line):
                    hits = [nm for nm in lower_names if nm in tok.lower()]
                    if hits:
                        leaks.append({"cv_id": cv_id, "line": n, "marker": tok,
                                      "rule": "candidate_name_in_link", "text": line.strip()})
    return leaks


def one_sided_terms(texts, labels, min_count=3):
    """Terms present in >= min_count CVs of one group and in none of the other."""
    labels = {k: normalise_gender(v) for k, v in labels.items()}
    groups = sorted({labels[c] for c in texts if c in labels})
    if len(groups) != 2:
        return []
    docs = {g: {} for g in groups}
    for cv_id, text in texts.items():
        g = labels.get(cv_id)
        if g is None:
            continue
        terms = set(t.lower() for t in re.findall(r"\[[A-Z_]+\]|[A-Za-z][A-Za-z'’-]{2,}", text))
        for t in terms - STOP:
            docs[g][t] = docs[g].get(t, 0) + 1
    out = []
    a, b = groups
    for g, other in ((a, b), (b, a)):
        for term, count in docs[g].items():
            if count >= min_count and docs[other].get(term, 0) == 0:
                out.append({"term": term, "only_in": g, "cvs": count})
    return sorted(out, key=lambda x: (-x["cvs"], x["term"]))


def read_labels(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["cv_id"]: r["gender"] for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser(description="Check redacted CVs for surviving gender markers.")
    ap.add_argument("--input", required=True, help="folder of redacted CVs")
    ap.add_argument("--raw", help="folder of raw CVs, to check for candidate names")
    ap.add_argument("--labels", help="gender labels CSV, for the one-sided term check")
    ap.add_argument("--out", help="also write the result to this JSON file")
    args = ap.parse_args()

    texts = {p.stem: p.read_text(encoding="utf-8") for p in sorted(Path(args.input).glob("*.txt"))}
    if not texts:
        sys.exit(json.dumps({"error": f"no .txt files in {args.input}"}))
    names = raw_names(args.raw) if args.raw else set()
    leaks = check_texts(texts, names)
    result = {"files_checked": len(texts), "names_checked": len(names),
              "leak_count": len(leaks), "leaks": leaks}
    if args.labels:
        result["one_sided_terms"] = one_sided_terms(texts, read_labels(args.labels))
        result["one_sided_note"] = ("Terms used only for one gender (3+ CVs). Review by hand: "
                                    "a placeholder or phrase here can reveal gender. Some may be chance.")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
