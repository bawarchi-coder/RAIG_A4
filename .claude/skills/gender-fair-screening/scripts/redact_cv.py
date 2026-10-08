#!/usr/bin/env python
"""Stage 1: remove gender markers from CVs before they are screened.

Usage:
  python redact_cv.py --input data/cvs_raw --output data/cvs_redacted --log outputs/redaction_log.json

Reads every .txt file in --input, writes the redacted CV under the same name
in --output, logs every change (cv_id, line, original, replacement, rule) to
--log and prints a JSON summary.

The rules are documented in ../references/gender_markers.md. Principles:
replace rather than delete wherever a line carries job-related content, and
never alter skills, qualifications, job titles, employers, dates or grades.
A placeholder must not itself reveal gender, so every institution in the
education section becomes [INSTITUTION], not only gendered ones.

Uses only the Python standard library. Other front ends import redact_text().
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------- lexicon --

# "Sri" is left out on purpose: it would also match "Sri Lanka".
TITLES = r"(?:Mr|Mrs|Ms|Miss|Mx|Shri|Shrimati|Smt|Kumari|Sushri)\.?"

# Lines removed entirely: label at the start of the line (after an optional bullet)
REMOVE_LINE = [
    ("date_of_birth", re.compile(r"^\s*(?:[-*•]\s*)?(?:date of birth|d\.?o\.?b\.?|born|age)\s*[:\-]", re.I)),
    ("gender_field", re.compile(r"^\s*(?:[-*•]\s*)?(?:gender|sex)\s*[:\-]", re.I)),
    ("marital_status", re.compile(r"^\s*(?:[-*•]\s*)?(?:marital|civil) status\s*[:\-]", re.I)),
    ("family_name", re.compile(
        r"^\s*(?:[-*•]\s*)?(?:(?:father|mother|husband|wife|spouse|guardian)(?:'s|’s)?\s+name\s*[:\-]"
        r"|[SDW]/o\b|(?:son|daughter|wife) of\b)", re.I)),
    ("photo", re.compile(r"^\s*(?:[-*•]\s*)?(?:\[?photo(?:graph)?\b)", re.I)),
    ("pronouns_field", re.compile(r"^\s*(?:[-*•]\s*)?(?:preferred\s+)?pronouns?\s*[:\-]", re.I)),
]

BREAK_REASON = re.compile(
    r"\b(?:maternity|paternity|parental|pregnan\w*|child\s?care|childcare|family care|caring for|"
    r"carer|raising|homemaker|housewife|househusband|full-time study|study|travel|relocation|"
    r"health|illness|sabbatical|personal reasons)\b", re.I)
CAREER_BREAK = re.compile(r"\bcareer break\b|\bbreak\s*\(", re.I)
DATE_RANGE = re.compile(
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
    r"\s*(?:to|–|—|-)\s*"
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{1,2}/\d{4}|\d{4}|"
    r"Present|Current|Now)", re.I)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PROFILE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|gitlab\.com|twitter\.com|x\.com|"
    r"facebook\.com|instagram\.com|medium\.com|kaggle\.com)/[\w\-./%]+"
    r"|\b(?:https?://|www\.)[^\s|,;()]+", re.I)
# Bare personal domains (e.g. priyaiyer.dev) are replaced when they contain the candidate's name
DOMAIN = re.compile(r"\b[\w-]+(?:\.[\w-]+)*\.(?:dev|io|me|com|net|org|in|co|uk|site|page|app|tech|ai|blog)"
                    r"(?:/[^\s|,;()]*)?\b", re.I)

INST_WORD = r"(?:College|University|Institute|School|Academy|Polytechnic|Vidyalaya|Mahavidyalaya)"
CAP = r"[A-Z][\w.'’&-]*"
INSTITUTION = re.compile(
    rf"(?:University|Institute|College|Academy) of {CAP}(?:\s+(?:and\s+)?{CAP}){{0,3}}"
    rf"|(?:{CAP}\s+){{1,6}}{INST_WORD}\b(?:\s+(?:of|for)(?:\s+(?:and\s+)?{CAP}){{1,4}})?")
GENDERED_INST = re.compile(r"\b(?:women|men|girls|boys|ladies)(?:'s|’s|'|’|s)?\b|\bfor (?:women|men|girls|boys)\b", re.I)
EDUCATION_HEADINGS = re.compile(r"^(?:EDUCATION|QUALIFICATION|ACADEMIC)", re.I)
# Section headings that are not written in capitals ("Work Experience", "Education & Training")
SECTION_NAMES = re.compile(
    r"^(?:profile|(?:professional |personal |career )?summary|(?:career )?objective|about me|"
    r"(?:work |professional |relevant )?experience|employment(?: history)?|work history|career history|"
    r"education(?:al)?(?: (?:and|&) \w+| qualifications| background)?|qualifications|academic \w+|"
    r"(?:technical |key |core )?skills(?: (?:and|&) \w+)?|interests|(?:extra-curricular )?activities|"
    r"hobbies(?: (?:and|&) interests)?|leadership(?: (?:and|&) activities)?|personal (?:details|information)|"
    r"declaration|projects|certifications?|achievements|awards|languages|references|volunteering)$", re.I)

# Named organisations whose name is a gender marker
ORGANISATIONS = {
    "Girls Who Code": "a coding community",
    "Women Who Code": "a coding community",
    "Lean In Circle": "a professional network",
}
GREEK = re.compile(r"\b(?:sorority|fraternity)\b", re.I)
WOMEN_IN = re.compile(r"\bWomen in (?=[A-Z])")
# Possessive forms ("Women's Cricket Team") anywhere, and plain gender words
# only inside the name of a team or society ("Ladies Hockey Club").
GENDERED_POSSESSIVE = re.compile(r"\b(?:women|men|ladies|girls|boys|gentlemen)(?:'s|’s|'|’)\s*", re.I)
GENDERED_IN_NAME = re.compile(
    r"\b(?:Womens|Mens|Women|Men|Ladies|Girls|Boys|Female|Male)\s+"
    r"(?=(?:[A-Z][a-z]+\s+){0,2}(?:Team|Club|Society|XI|Squad|League|Network|Chapter|"
    r"Association|Hostel|Wing|Forum)\b)")

GENDERED_JOBS = {
    "chairman": "chairperson", "chairwoman": "chairperson", "chairmen": "chairpersons",
    "chairwomen": "chairpersons", "salesman": "salesperson", "saleswoman": "salesperson",
    "salesgirl": "salesperson", "salesmen": "salespeople", "saleswomen": "salespeople",
    "waitress": "server", "waiter": "server", "waitresses": "servers", "waiters": "servers",
    "hostess": "server", "hostesses": "servers", "busboy": "server",
    "spokesman": "spokesperson", "spokeswoman": "spokesperson", "foreman": "supervisor",
    "forewoman": "supervisor", "businessman": "businessperson", "businesswoman": "businessperson",
    "policeman": "police officer", "policewoman": "police officer", "stewardess": "flight attendant",
    "cameraman": "camera operator", "craftsman": "craftsperson", "head boy": "school captain",
    "head girl": "school captain", "headboy": "school captain", "headgirl": "school captain",
}
GENDERED_JOB_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, GENDERED_JOBS), key=len, reverse=True)) + r")\b", re.I)

# Pronouns
SUBJECT = {"he": "they", "she": "they"}
CONTRACTED = {"he's": "they're", "she's": "they're", "he'd": "they'd", "she'd": "they'd",
              "he'll": "they'll", "she'll": "they'll"}
OBJECT = {"him": "them"}
POSSESSIVE = {"his": "their"}
REFLEXIVE = {"himself": "themself", "herself": "themself"}
NOT_A_NOUN = {"and", "or", "to", "in", "on", "at", "with", "for", "from", "by", "as", "about",
              "into", "after", "before", "during", "through", "than", "that", "who"}
ADVERBS = {"also", "currently", "now", "previously", "still", "recently", "often", "always",
           "regularly", "successfully"}
IRREGULAR = {"is": "are", "was": "were", "has": "have", "does": "do", "isn't": "aren't",
             "wasn't": "weren't", "hasn't": "haven't", "doesn't": "don't"}


# ---------------------------------------------------------------- helpers --

def match_case(new, old):
    if old.isupper() and len(old) > 1:
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def plural_verb(word):
    lw = word.lower()
    if lw in IRREGULAR:
        return match_case(IRREGULAR[lw], word)
    if not lw.isalpha() or len(lw) < 3:
        return word
    if lw.endswith("ies") and len(lw) > 4:
        return word[:-3] + "y"
    if re.search(r"(?:ss|sh|ch|x|z|o)es$", lw):
        return word[:-2]
    if lw.endswith("s") and not lw.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def is_heading(line):
    s = line.strip()
    if not s or len(s) > 40 or s.startswith(("-", "*", "•", "[")):
        return False
    if s.upper() == s and re.search(r"[A-Z]", s):
        return True
    return bool(SECTION_NAMES.match(s.rstrip(":")))


def name_from(lines):
    """Candidate name: a 'Name:' field, else the first non-empty line."""
    for line in lines:
        m = re.match(r"^\s*(?:full\s+)?name\s*:\s*(.+)$", line, re.I)
        if m:
            return m.group(1).strip()
    for line in lines:
        if line.strip():
            return line.strip()
    return ""


def name_tokens(name):
    name = re.sub(rf"^{TITLES}\s+", "", name.strip())
    return [t for t in re.findall(r"[A-Z][a-zA-Z'’-]+", name) if len(t) >= 2], name


# ---------------------------------------------------------------- redact ---

def swap_pronouns(line):
    """Replace gendered pronouns with they/them/their and fix the next verb."""
    tokens = re.findall(r"[A-Za-z’']+|[^A-Za-z’']+", line)
    changes = []
    words = [i for i, t in enumerate(tokens) if re.match(r"[A-Za-z]", t)]

    def next_word(pos):
        later = [i for i in words if i > pos]
        if not later:
            return None
        # stop at punctuation between the two words
        between = "".join(tokens[pos + 1:later[0]])
        return None if re.search(r"[^\s]", between) else later[0]

    for pos in words:
        tok = tokens[pos]
        low = tok.lower().replace("’", "'")
        new = None
        if low in SUBJECT:
            new = SUBJECT[low]
            nxt = next_word(pos)
            if nxt is not None and tokens[nxt].lower() in ADVERBS:
                nxt = next_word(nxt)
            if nxt is not None:
                verb = plural_verb(tokens[nxt])
                if verb != tokens[nxt]:
                    changes.append((tokens[nxt], verb, "pronoun_verb_agreement"))
                    tokens[nxt] = verb
        elif low in CONTRACTED:
            new = CONTRACTED[low]
        elif low in OBJECT:
            new = OBJECT[low]
        elif low in REFLEXIVE:
            new = REFLEXIVE[low]
        elif low == "his":
            nxt = next_word(pos)
            new = "their" if nxt is not None and tokens[nxt].lower() not in NOT_A_NOUN else "theirs"
        elif low == "her":
            nxt = next_word(pos)
            new = "their" if nxt is not None and tokens[nxt].lower() not in NOT_A_NOUN else "them"
        elif low == "hers":
            new = "theirs"
        if new:
            new = match_case(new, tok)
            changes.append((tok, new, "pronoun"))
            tokens[pos] = new
    return "".join(tokens), changes


def redact_text(text, cv_id="cv"):
    """Return (redacted_text, changes). Each change is a dict for the log."""
    lines = text.splitlines()
    changes = []

    def log(line_no, original, replacement, rule):
        changes.append({"cv_id": cv_id, "line": line_no, "original": original,
                        "replacement": replacement, "rule": rule})

    full_name = name_from(lines)
    tokens, bare_name = name_tokens(full_name)
    name_re = None
    if bare_name:
        name_re = re.compile(rf"(?:\b{TITLES}\s+)?{re.escape(bare_name)}(?:'s|’s)?")
    token_re = re.compile(r"\b(" + "|".join(map(re.escape, tokens)) + r")\b") if tokens else None
    lower_tokens = [t.lower() for t in tokens if len(t) >= 3]

    out = []
    section = ""
    for n, line in enumerate(lines, start=1):
        if is_heading(line):
            section = line.strip()
            out.append(line)
            continue

        # 1. whole-line removals (personal details)
        removed = False
        for rule, pattern in REMOVE_LINE:
            if pattern.search(line):
                log(n, line.strip(), "", rule)
                removed = True
                break
        if removed:
            continue

        # 2. career break: keep the dates, drop the stated reason
        if CAREER_BREAK.search(line) or (BREAK_REASON.search(line) and DATE_RANGE.search(line)
                                         and not re.search(r"maternity cover", line, re.I)
                                         and re.search(r"\b(?:break|leave|career|sabbatical|gap)\b", line, re.I)):
            dates = DATE_RANGE.search(line)
            sep = " | " if "|" in line else ", "
            new = "Career break" + (sep + dates.group(0) if dates else "")
            prefix = re.match(r"^\s*(?:[-*•]\s*)?", line).group(0)
            new = prefix + new
            if new != line:
                log(n, line.strip(), new.strip(), "career_break_reason")
            out.append(new)
            continue
        if BREAK_REASON.search(line) and re.match(r"^\s*[-*•]", line) and \
                re.search(r"\b(?:maternity|paternity|parental|pregnan\w*|child\s?care|raising|caring for)\b", line, re.I):
            log(n, line.strip(), "", "career_break_detail")
            continue

        new = line

        # 3. contact details
        for m in EMAIL.findall(new):
            log(n, m, "[EMAIL]", "email")
        new = EMAIL.sub("[EMAIL]", new)
        for m in PROFILE.findall(new):
            log(n, m, "[PROFILE]", "profile_link")
        new = PROFILE.sub("[PROFILE]", new)

        def personal_domain(m):
            if any(t in m.group(0).lower() for t in lower_tokens):
                log(n, m.group(0), "[PROFILE]", "profile_link")
                return "[PROFILE]"
            return m.group(0)
        if lower_tokens:
            new = DOMAIN.sub(personal_domain, new)

        # 4. name (with any title), then remaining name tokens
        if name_re:
            for m in name_re.findall(new):
                log(n, m, "[CANDIDATE]", "candidate_name")
            new = name_re.sub("[CANDIDATE]", new)
        if token_re:
            for m in token_re.findall(new):
                log(n, m, "[CANDIDATE]", "candidate_name")
            new = token_re.sub("[CANDIDATE]", new)
        for m in re.finditer(rf"\b{TITLES}\s+(?=[A-Z\[])", new):
            log(n, m.group(0).strip(), "", "title")
        new = re.sub(rf"\b{TITLES}\s+(?=[A-Z\[])", "", new)

        # 5. institutions: all of them in the education section, gendered ones elsewhere
        in_education = bool(EDUCATION_HEADINGS.match(section))

        def inst(m):
            text_ = m.group(0)
            if in_education or GENDERED_INST.search(text_):
                log(n, text_, "[INSTITUTION]", "institution")
                return "[INSTITUTION]"
            return text_
        new = INSTITUTION.sub(inst, new)

        # 6. gendered organisations, teams and societies
        for org, repl in ORGANISATIONS.items():
            if org.lower() in new.lower():
                log(n, org, repl, "gendered_organisation")
                new = re.sub(re.escape(org), repl, new, flags=re.I)
        for m in GREEK.findall(new):
            log(n, m, "student society", "gendered_organisation")
        new = GREEK.sub("student society", new)
        for m in WOMEN_IN.findall(new):
            log(n, m.strip(), "", "gendered_qualifier")
        new = WOMEN_IN.sub("", new)
        for pattern in (GENDERED_POSSESSIVE, GENDERED_IN_NAME):
            for m in pattern.findall(new):
                log(n, m.strip(), "", "gendered_qualifier")
            new = pattern.sub("", new)

        # 7. gendered job words
        def job(m):
            repl = match_case(GENDERED_JOBS[m.group(0).lower()], m.group(0))
            log(n, m.group(0), repl, "gendered_job_word")
            return repl
        new = GENDERED_JOB_RE.sub(job, new)

        # 8. pronouns
        new, pron = swap_pronouns(new)
        for orig, repl, rule in pron:
            log(n, orig, repl, rule)

        out.append(new)

    # Drop headings left with no content, and collapse blank lines
    cleaned = []
    for i, line in enumerate(out):
        if is_heading(line):
            rest = out[i + 1:]
            body = []
            for r in rest:
                if is_heading(r):
                    break
                body.append(r)
            if not any(b.strip() for b in body):
                continue
        if not line.strip() and (not cleaned or not cleaned[-1].strip()):
            continue
        cleaned.append(line)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return "\n".join(cleaned) + "\n", changes


def redact_folder(input_dir, output_dir, log_path=None):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    all_changes = []
    files = sorted(input_dir.glob("*.txt"))
    for path in files:
        redacted, changes = redact_text(path.read_text(encoding="utf-8"), path.stem)
        (output_dir / path.name).write_text(redacted, encoding="utf-8")
        all_changes.extend(changes)
    summary = {
        "files_redacted": len(files),
        "changes": len(all_changes),
        "changes_by_rule": dict(Counter(c["rule"] for c in all_changes).most_common()),
        "output": _shown(output_dir),
    }
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(json.dumps({"summary": summary, "changes": all_changes}, indent=2),
                                  encoding="utf-8")
        summary["log"] = _shown(log_path)
    return summary


def _shown(path):
    """Path relative to the current folder when possible, so logs carry no personal folder names."""
    try:
        return Path(path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return Path(path).name


def main():
    ap = argparse.ArgumentParser(description="Remove gender markers from CVs.")
    ap.add_argument("--input", required=True, help="folder of raw CV .txt files")
    ap.add_argument("--output", required=True, help="folder for redacted CVs")
    ap.add_argument("--log", default="outputs/redaction_log.json", help="JSON change log")
    args = ap.parse_args()
    if not Path(args.input).is_dir():
        sys.exit(json.dumps({"error": f"input folder not found: {args.input}"}))
    print(json.dumps(redact_folder(args.input, args.output, args.log), indent=2))


if __name__ == "__main__":
    main()
