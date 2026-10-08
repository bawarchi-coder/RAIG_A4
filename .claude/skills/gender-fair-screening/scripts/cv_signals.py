"""Shared helpers: find proxy signals in a CV and build counterfactual CVs.

Used by audit_shortlist.py (how often each proxy signal appears) and
proxy_probe.py (does the screener penalise it). Standard library only.

Proxy signals detected:
  career_gap  a break line (career break, maternity/paternity/parental leave,
              sabbatical, career gap) or a gap of more than 6 months between jobs
  part_time   the words "part-time" or "part time"

Date ranges understood: "Mar 2021", "March 2021", "03/2021", "2021", each
followed by to / – / — / - and another date or "Present".
"""
import re
from datetime import date

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
FULL = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
        "October", "November", "December"]
TOKEN = (r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}"
         r"|(?<!\d)\d{1,2}/\d{4}(?!\d)|(?<![\d/])\d{4}(?!\d))")
RANGE = re.compile(rf"({TOKEN})(\s*(?:to|–|—|-)\s*)({TOKEN}|present|current|now|date)\b", re.IGNORECASE)
BREAK_LINE = re.compile(r"\b(?:career break|career gap|break|maternity|paternity|parental leave|"
                        r"sabbatical)\b", re.IGNORECASE)
PART_TIME = re.compile(r"\s*\(part[- ]time[^)]*\)|\bpart[- ]time\b\s*", re.IGNORECASE)
GAP_MONTHS = 6


def _today_idx():
    t = date.today()
    return t.year * 12 + t.month - 1


def parse_date(token, is_end=False):
    """Month index (year * 12 + month - 1) for one date token, or None for 'present'."""
    t = token.strip()
    if re.fullmatch(r"present|current|now|date", t, re.IGNORECASE):
        return None
    m = re.match(r"([A-Za-z]+)\.?\s+(\d{4})", t)
    if m:
        return int(m.group(2)) * 12 + MONTHS.index(m.group(1).lower()[:3])
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", t)
    if m:
        return int(m.group(2)) * 12 + min(max(int(m.group(1)), 1), 12) - 1
    return int(t) * 12 + (11 if is_end else 0)


def format_like(token, idx, other=""):
    """Write month index `idx` in the same style as an existing date token.

    "May" could be a full or a short month name, so `other` (the other date
    in the same range) decides in that case.
    """
    t = token.strip()
    m = re.match(r"([A-Za-z]+)(\.?)\s+\d{4}", t)
    if m:
        word = m.group(1)
        if word.lower() == "may":
            o = re.match(r"([A-Za-z]+)", other.strip())
            word = o.group(1) if o and o.group(1).lower() != "may" else word
        name = FULL[idx % 12] if len(word) > 3 else FULL[idx % 12][:3]
        return f"{name}{m.group(2)} {idx // 12}"
    m = re.fullmatch(r"(\d{1,2})/\d{4}", t)
    if m:
        month = idx % 12 + 1
        return f"{month:02d}/{idx // 12}" if len(m.group(1)) == 2 else f"{month}/{idx // 12}"
    return str(idx // 12)


def intervals(text):
    """[(start, end, line_no, kind, match)] where kind is 'job' or 'break'."""
    out = []
    for n, line in enumerate(text.splitlines()):
        m = RANGE.search(line)
        if not m:
            continue
        start = parse_date(m.group(1))
        end = parse_date(m.group(3), is_end=True)
        if end is None:
            end = _today_idx()
        kind = "break" if BREAK_LINE.search(line) else "job"
        out.append((start, end, n, kind, m))
    return out


def job_gaps(text, min_months=GAP_MONTHS):
    jobs = sorted((s, e) for s, e, _, k, _ in intervals(text) if k == "job")
    return [s2 - e1 - 1 for (s1, e1), (s2, e2) in zip(jobs, jobs[1:]) if s2 - e1 - 1 > min_months]


def signals(text):
    """Which proxy signals a CV carries."""
    has_break_line = any(k == "break" for *_, k, _ in intervals(text))
    return {
        "career_gap": bool(has_break_line or job_gaps(text)),
        "part_time": bool(re.search(r"\bpart[- ]time\b", text, re.IGNORECASE)),
    }


def without_gap(text):
    """Counterfactual CV: same jobs and the same total experience, no gap.

    Break lines are removed and every job before a gap is moved later by the
    length of the gap, so only the gap itself changes. Dates keep their format.
    """
    lines = text.splitlines()
    ivs = intervals(text)
    jobs = sorted(((s, e, n, m) for s, e, n, k, m in ivs if k == "job"), key=lambda x: x[0])
    drop = {n for _, _, n, k, _ in ivs if k == "break"}
    shift = 0
    new_dates = {}
    # walk from the most recent job backwards, accumulating the gaps closed
    for later, earlier in zip(reversed(jobs), list(reversed(jobs))[1:]):
        gap = later[0] - earlier[1] - 1
        if gap > 0:
            shift += gap
        if shift:
            s, e, n, m = earlier
            new_dates[n] = (m, format_like(m.group(1), s + shift, m.group(3)) + m.group(2)
                            + format_like(m.group(3), e + shift, m.group(1)))
    out = []
    for n, line in enumerate(lines):
        if n in drop:
            continue
        if n in new_dates:
            m, repl = new_dates[n]
            line = line[:m.start()] + repl + line[m.end():]
        out.append(line)
    return "\n".join(out) + "\n"


def without_part_time(text):
    """Counterfactual CV: identical except that the words 'part-time' are removed."""
    return "\n".join(PART_TIME.sub("", line).rstrip() for line in text.splitlines()) + "\n"


COUNTERFACTUALS = {
    "career_gap": without_gap,
    "part_time": without_part_time,
}

GENDER_ALIASES = {"f": "female", "female": "female", "woman": "female", "women": "female", "w": "female",
                  "m": "male", "male": "male", "man": "male", "men": "male"}


def normalise_gender(value):
    """Map common label spellings (F, Female, woman ...) to 'female' / 'male'."""
    v = (value or "").strip()
    return GENDER_ALIASES.get(v.lower(), v)
