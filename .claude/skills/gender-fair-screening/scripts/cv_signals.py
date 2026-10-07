"""Shared helpers: find proxy signals in a CV and build counterfactual CVs.

Used by audit_shortlist.py (how often each proxy signal appears) and
proxy_probe.py (does the screener penalise it). Standard library only.

Proxy signals detected:
  career_gap  a "Career break" line, or a gap of more than 6 months between jobs
  part_time   the words "part-time" or "part time"
"""
import re
from datetime import date

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
RANGE = re.compile(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})\s*(?:to|–|—|-)\s*"
    r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})|(present|current|now))",
    re.IGNORECASE)
BREAK_LINE = re.compile(r"\bcareer break\b", re.IGNORECASE)
PART_TIME = re.compile(r"\s*\(part[- ]time\)|\bpart[- ]time\b\s*", re.IGNORECASE)
GAP_MONTHS = 6


def _idx(mon, year):
    return int(year) * 12 + MONTHS.index(mon.lower()[:3])


def _today_idx():
    t = date.today()
    return t.year * 12 + t.month - 1


def intervals(text):
    """[(start, end, line_no, kind, match)] where kind is 'job' or 'break'."""
    out = []
    for n, line in enumerate(text.splitlines()):
        m = RANGE.search(line)
        if not m:
            continue
        start = _idx(m.group(1), m.group(2))
        end = _today_idx() if m.group(5) else _idx(m.group(3), m.group(4))
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


def _fmt(idx):
    return f"{MONTHS[idx % 12].capitalize()} {idx // 12}"


def without_gap(text):
    """Counterfactual CV: same jobs and the same total experience, no gap.

    Career break lines are removed and every job before a gap is moved later
    by the length of the gap, so only the gap itself changes.
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
            new_dates[n] = (m, f"{_fmt(s + shift)} to {_fmt(e + shift)}")
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
