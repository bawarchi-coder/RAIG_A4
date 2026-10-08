"""Standalone demo app for the gender-fair screening layer.

Runs the same scripts as the agent skill and the API, with no AI agent, no
login and no internet connection.

Run from the project root:
  .venv\\Scripts\\streamlit run app.py
(start_demo.bat also starts Vendor B and the API.)
"""
import html
import json
import re
import socket
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "gender-fair-screening" / "scripts"))
from pipeline import run as run_pipeline  # noqa: E402
from redact_cv import redact_text  # noqa: E402
from cv_signals import normalise_gender  # noqa: E402
from screener_adapter import ScreenerError  # noqa: E402

REGISTRY = json.loads((ROOT / "integration" / "screeners.json").read_text(encoding="utf-8"))
DATASETS = {
    "set1": {"label": "Dataset 1: Data Analyst, 30 CVs", "cvs": "data/cvs_raw", "jd": "data/job_description.md",
             "labels": "data/gender_labels.csv", "top_k": 10, "role": "Data Analyst",
             "about": "15 women and 15 men with matched qualifications, 5 twin pairs, one CV layout."},
    "set2": {"label": "Dataset 2: Software Developer, 40 CVs", "cvs": "data2/cvs_raw",
             "jd": "data2/job_description.md", "labels": "data2/gender_labels.csv", "top_k": 12,
             "role": "Software Developer",
             "about": "16 women and 24 men, 4 twin pairs, three CV layouts (UK, Indian biodata, US), "
                      "different date formats and markers. Built to test the code."},
}
TOOL_HELP = {
    "screener_a": "An old-style program the HR team runs on a folder of CVs. Secretly unfair: it adds points "
                  "for male words, takes points off for female words, and takes 10 points off for a career gap.",
    "screener_a_control": "The same program with its hidden rules switched off. This is what a fair result "
                          "looks like, for comparison.",
    "vendor_b": "A cloud service the HR team sends CVs to over the internet. It claims to be gender-blind and "
                "never reads names or pronouns, but it penalises career gaps and part-time work.",
}
GENDER = {"male": "Men", "female": "Women"}
SIGNAL = {"career_gap": "Career break or gap", "part_time": "Part-time work"}
EXAMPLE_CV = """Mrs. Ananya Kapoor
Email: ananya.kapoor@example.com | LinkedIn: linkedin.com/in/ananya-kapoor

SUMMARY
She is a data analyst with 4 years of experience. She has built Power BI dashboards and her team relies on her SQL.

EXPERIENCE
Data Analyst, Northwind Retail | Mar 2023 to Present
Career break (maternity leave) | Jun 2022 to Feb 2023
Junior Analyst, Bluefin Insurance | Jan 2020 to May 2022

EDUCATION
BSc Statistics | Lady Elmira College for Women | 2019 | First Class

ACTIVITIES
- Captain, Women's Football Team
- Chairwoman, Women in Data Society

PERSONAL DETAILS
Date of birth: 02/05/1997
Husband's name: Rohit Kapoor
Photo: attached
"""

st.set_page_config(page_title="Gender-Fair CV Screening", page_icon="⚖️", layout="wide")
st.markdown("""
<style>
.cv {white-space: pre-wrap; font-family: ui-monospace, Consolas, monospace; font-size: 0.85rem;
     line-height: 1.45; padding: 0.8rem 1rem; border-radius: 0.5rem;
     border: 1px solid rgba(128,128,128,0.35);}
.cv mark.del {background: rgba(220, 53, 69, 0.28); color: inherit; padding: 0 2px; border-radius: 3px;}
.cv mark.add {background: rgba(25, 135, 84, 0.28); color: inherit; padding: 0 2px; border-radius: 3px;}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------------ helpers --

def badge(result):
    return ":green[**PASS**]" if result == "PASS" else ":red[**FAIL**]"


def service_up(url):
    p = urlparse(url)
    try:
        with socket.create_connection((p.hostname, p.port or 80), timeout=0.5):
            return True
    except OSError:
        return False


def mark_raw(text, changes):
    """Raw CV with every redacted piece highlighted in red."""
    lines = text.splitlines()
    by_line = {}
    for c in changes:
        counts = by_line.setdefault(c["line"], {})
        counts[c["original"]] = counts.get(c["original"], 0) + 1
    out = []
    for n, line in enumerate(lines, start=1):
        esc = html.escape(line)
        for orig, count in sorted(by_line.get(n, {}).items(), key=lambda kv: -len(kv[0])):
            o = html.escape(orig)
            if not o:
                continue
            edge = r"\b" if re.match(r"\w", o[0]) and re.match(r"\w", o[-1]) else ""
            esc = re.sub(rf"(?<!>){edge}{re.escape(o)}{edge}", lambda m: f'<mark class="del">{m.group(0)}</mark>',
                         esc, count=count)
        out.append(esc)
    return "<br>".join(out)


def mark_redacted(text, changes):
    """Redacted CV with every replacement highlighted in green."""
    esc = html.escape(text)
    words = {html.escape(c["replacement"]) for c in changes if c["replacement"]}
    words |= {"[CANDIDATE]", "[EMAIL]", "[PROFILE]", "[INSTITUTION]"}
    pattern = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    if pattern:
        esc = re.sub(rf"(?<![\w\[])({pattern})(?![\w\]])", r'<mark class="add">\1</mark>', esc)
    # <br> instead of newlines keeps markdown from turning "- " lines into lists
    return esc.replace("\n", "<br>")


def ranking_table(ranking, labels):
    df = pd.DataFrame(ranking)
    df["gender"] = df["cv_id"].map(lambda c: GENDER.get(labels.get(c, ""), labels.get(c, "")))
    df["shortlisted"] = df["shortlisted"].map({True: "✔", False: ""})
    return df[["rank", "cv_id", "score", "shortlisted", "gender"]]


def rate_chart(ra, rd):
    rows = [{"Gender": GENDER[g], "CVs": cvs, "Selection rate": a["groups"][g]["selection_rate"]}
            for cvs, a in (("Raw CVs", ra), ("Redacted CVs", rd)) for g in ("male", "female")]
    base = alt.Chart(pd.DataFrame(rows)).encode(
        x=alt.X("Gender:N", title=None, axis=alt.Axis(labelAngle=0, labelFontSize=14)),
        xOffset=alt.XOffset("CVs:N", sort=["Raw CVs", "Redacted CVs"]),
        y=alt.Y("Selection rate:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 0.7])),
        color=alt.Color("CVs:N", sort=["Raw CVs", "Redacted CVs"],
                        scale=alt.Scale(range=["#9aa5b1", "#2563eb"]), legend=alt.Legend(orient="top", title=None)),
    )
    bars = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    text = base.mark_text(dy=-8, fontSize=13).encode(text=alt.Text("Selection rate:Q", format=".0%"))
    return (bars + text).properties(height=320)


def results_table(a):
    g = a["groups"]
    rows = []
    for key, label in (("candidates", "Candidates"), ("shortlisted", "Shortlisted")):
        rows.append({"Measure": label, "Men": str(g["male"][key]), "Women": str(g["female"][key])})
    rows.append({"Measure": "Selection rate", "Men": f"{g['male']['selection_rate']:.0%}",
                 "Women": f"{g['female']['selection_rate']:.0%}"})
    rows.append({"Measure": "Mean score", "Men": f"{g['male']['mean_score']:.1f}",
                 "Women": f"{g['female']['mean_score']:.1f}"})
    return pd.DataFrame(rows).set_index("Measure")


# ------------------------------------------------------------------ sidebar --

with st.sidebar:
    st.header("Setup")
    ds_keys = list(DATASETS)
    ds_start = ds_keys.index(st.query_params["dataset"]) if st.query_params.get("dataset") in ds_keys else 0
    ds_name = st.selectbox("Candidate pool", ds_keys, index=ds_start, format_func=lambda k: DATASETS[k]["label"],
                           help="Two fictional sets of CVs. Dataset 2 was made separately to test the code "
                                "on CV layouts, date formats and markers it was not designed around.")
    ds = DATASETS[ds_name]
    st.caption(ds["about"])
    keys = list(REGISTRY)
    start = keys.index(st.query_params["run"]) if st.query_params.get("run") in keys else 0
    name = st.selectbox("Existing screening tool", keys, index=start, format_func=lambda k: REGISTRY[k]["label"],
                        help="The software the HR team already uses. The fairness layer does not replace "
                             "it: it hides gender before this tool sees the CVs and checks its results after.")
    scr = dict(REGISTRY[name])
    st.caption(TOOL_HELP[name])
    if scr["type"] == "http" and not service_up(scr["url"]):
        st.info("The Vendor B web service is not running here, so its offline copy (same scoring) is used.")
    run = st.button("Run fairness check", type="primary", width="stretch")
    st.caption(f"Shortlist size: {ds['top_k']}. Gender labels are used only for the audit; "
               "the screening tool never sees them.")

st.title("⚖️ Gender-Fair CV Screening")
st.markdown("**A plug-in fairness layer for CV screening:** it hides gender before screening "
            "and checks the outcome after. *All candidates are fictional.*")

if "runs" not in st.session_state:
    st.session_state.runs = {}
if "workdir" not in st.session_state:  # each visitor gets their own output folder
    st.session_state.workdir = Path(tempfile.mkdtemp(prefix="fairscreen_"))
run_key = (ds_name, name)

# A bookmark such as http://localhost:8501/?run=screener_a&dataset=set2 runs that tool on first load
auto = st.query_params.get("run")
if auto == name and run_key not in st.session_state.runs:
    run = True

if run:
    with st.spinner(f"Redacting, screening with {scr['label']}, auditing and probing…"):
        try:
            res = run_pipeline(ROOT / ds["cvs"], ROOT / ds["jd"], ROOT / ds["labels"], scr,
                               st.session_state.workdir / ds_name / name, tool_name=scr["label"],
                               role=ds["role"], top_k=ds["top_k"], cwd=ROOT)
            labels = {k: normalise_gender(v) for k, v in
                      pd.read_csv(ROOT / ds["labels"], dtype=str).set_index("cv_id")["gender"].items()}
            st.session_state.runs[run_key] = {"res": res, "labels": labels, "cv_dir": ROOT / ds["cvs"],
                                              "fallback": scr.get("used_fallback", False)}
        except ScreenerError as e:
            st.error(f"The screening tool failed: {e}")

current = st.session_state.runs.get(run_key)

if current:
    res, labels = current["res"], current["labels"]
    raw, red = res["raw"], res["redacted"]
    ra, rd = raw["audit"], red["audit"]

    # Headline numbers, above the tabs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Impact ratio: tool on raw CVs", f"{ra['impact_ratio']:.2f}")
    c1.markdown(f"Four-fifths rule: {badge(ra['four_fifths'])}")
    c2.metric("Impact ratio: same tool, redacted CVs", f"{rd['impact_ratio']:.2f}",
              f"{rd['impact_ratio'] - ra['impact_ratio']:+.2f}")
    c2.markdown(f"Four-fifths rule: {badge(rd['four_fifths'])}")
    c3.metric("Twin pairs scored identically", f"{rd['twin_test']['identical']} / {rd['twin_test']['pairs']}",
              f"raw CVs: {ra['twin_test']['identical']} / {ra['twin_test']['pairs']}", delta_color="off")
    pen = {s: v for s, v in red["probe"]["summary"].items() if v["cvs_penalised"]}
    c4.metric("Proxy penalties found", len(pen))
    c4.markdown("; ".join(f"{SIGNAL[s]}: :red[**−{v['mean_penalty_points']:.0f} pts**]" for s, v in pen.items())
                or ":green[none]")
    rec = red["recommendation"]
    (st.error if rec.startswith("Do not") else st.warning if "conditions" in rec else st.success)(
        f"**Recommendation: {rec}.** A human makes the final decision.")
    if current.get("fallback"):
        st.caption("Vendor B was run from its offline copy because its web service is not running here.")

tab_names = ["① Existing tool", "② Redaction", "③ Blind screening", "④ Proxy probe", "⑤ Report",
             "Try it: redact a CV", "All runs"]
tabs = st.tabs(tab_names)

if not current:
    for t in tabs[:5]:
        with t:
            st.info("Choose a screening tool in the sidebar and press **Run fairness check**.")
else:
    with tabs[0]:
        st.subheader("The tool as it is used today, on raw CVs")
        left, right = st.columns([3, 2])
        with left:
            st.markdown("**Selection rate by gender**, before and after redaction")
            st.altair_chart(rate_chart(ra, rd), width="stretch")
        with right:
            st.markdown("**Raw CVs**")
            st.dataframe(results_table(ra), width="stretch")
            st.markdown(f"Impact ratio **{ra['impact_ratio']:.2f}** {badge(ra['four_fifths'])} · "
                        f"Fisher's exact p = {ra['fisher_exact_p']:.3f}")
        st.markdown("**Twin test:** CVs identical except for gender markers")
        after = {t["pair"]: t for t in rd["twin_test"]["details"]}
        twins = pd.DataFrame([{"Pair": t["pair"], "Man": t["man"], "Woman": t["woman"],
                               "Raw: man": t["score_man"], "Raw: woman": t["score_woman"],
                               "Raw: gap": t["difference_man_minus_woman"],
                               "Redacted: man": after[t["pair"]]["score_man"],
                               "Redacted: woman": after[t["pair"]]["score_woman"],
                               "Redacted: gap": after[t["pair"]]["difference_man_minus_woman"]}
                              for t in ra["twin_test"]["details"]])
        st.dataframe(twins, hide_index=True, width="stretch")
        with st.expander("Full ranking on raw CVs"):
            st.dataframe(ranking_table(raw["ranking"], labels), hide_index=True, width="stretch")

    with tabs[1]:
        s = res["redaction"]["summary"]
        lc = res["leak_check"]
        st.subheader(f"{s['files_redacted']} CVs redacted, {s['changes']} changes")
        a, b = st.columns([2, 3])
        with a:
            st.bar_chart(pd.Series(s["changes_by_rule"], name="changes"), horizontal=True, height=380)
        with b:
            if lc["leak_count"] == 0:
                st.success(f"Leak check: 0 gender markers left in {lc['files_checked']} redacted CVs.")
            else:
                st.error(f"Leak check: {lc['leak_count']} markers left. Fix them before screening.")
                st.dataframe(pd.DataFrame(lc["leaks"]), hide_index=True)
            for t in lc.get("one_sided_terms", []):
                st.warning(f"“{t['term']}” appears on {t['cvs']} {GENDER.get(t['only_in'], t['only_in']).lower()}'s "
                           "CVs and none of the others. Not a marker, but it can reveal gender: review by hand.")
        cv_ids = sorted(labels)
        pick = st.selectbox("Compare a CV before and after", cv_ids,
                            index=cv_ids.index("cv_003") if "cv_003" in cv_ids else 0)
        changes = [c for c in res["redaction"]["changes"] if c["cv_id"] == pick]
        raw_text = (current["cv_dir"] / f"{pick}.txt").read_text(encoding="utf-8")
        red_text = (Path(res["out_dir"]) / "cvs_redacted" / f"{pick}.txt").read_text(encoding="utf-8")
        l, r = st.columns(2)
        l.markdown("**Before** (red: removed or replaced)")
        l.markdown(f'<div class="cv">{mark_raw(raw_text, changes)}</div>', unsafe_allow_html=True)
        r.markdown("**After** (green: replacement)")
        r.markdown(f'<div class="cv">{mark_redacted(red_text, changes)}</div>', unsafe_allow_html=True)
        with st.expander(f"Change log for {pick} ({len(changes)} changes)"):
            st.dataframe(pd.DataFrame(changes)[["line", "original", "replacement", "rule"]], hide_index=True,
                         width="stretch")

    with tabs[2]:
        st.subheader("Same tool, redacted CVs")
        a, b = st.columns([2, 3])
        with a:
            st.dataframe(results_table(rd), width="stretch")
            st.markdown(f"Impact ratio **{rd['impact_ratio']:.2f}** {badge(rd['four_fifths'])} · "
                        f"Fisher's exact p = {rd['fisher_exact_p']:.3f}")
            st.markdown(f"Twin test: **{rd['twin_test']['identical']} / {rd['twin_test']['pairs']}** pairs "
                        "scored identically")
            if rd.get("sample_size_warning"):
                st.caption(rd["sample_size_warning"])
        with b:
            st.dataframe(ranking_table(red["ranking"], labels), hide_index=True, width="stretch",
                         height=420)

    with tabs[3]:
        st.subheader("Does the tool penalise proxies for gender?")
        st.markdown("Each CV with a proxy signal is scored again **without that signal and nothing else "
                    "changed**. A positive change means the signal was costing the candidate points.")
        cols = st.columns(len(red["probe"]["summary"]))
        for col, (sig, v) in zip(cols, red["probe"]["summary"].items()):
            who = rd.get("proxy_signals", {}).get(sig, {}).get("by_gender", {})
            col.metric(SIGNAL[sig], f"−{v['mean_penalty_points']:.0f} points" if v["cvs_penalised"] else "no penalty",
                       f"{v['cvs_penalised']} of {v['cvs_tested']} CVs penalised", delta_color="off")
            col.caption("Carried by " + ", ".join(f"{n} {GENDER.get(g, g).lower()}" for g, n in who.items()))
        tests = pd.DataFrame(red["probe"]["tests"])
        if not tests.empty:
            tests["signal"] = tests["signal"].map(SIGNAL)
            tests["gender"] = tests["cv_id"].map(lambda c: GENDER.get(labels.get(c, ""), ""))
            st.dataframe(tests[["cv_id", "gender", "signal", "score_with_signal", "score_without_signal", "change"]],
                         hide_index=True, width="stretch")
        st.info(red["probe"]["finding"])

    with tabs[4]:
        which = st.radio("Report", ["Redacted CVs (with the fairness layer)", "Raw CVs (baseline)"], horizontal=True)
        report = red["report"] if which.startswith("Redacted") else raw["report"]
        st.download_button("Download report (.md)", report, file_name=f"audit_report_{name}.md")
        st.markdown(report)

with tabs[5]:
    st.subheader("Paste any CV and see what the redaction removes")
    text = st.text_area("CV text", EXAMPLE_CV, height=360)
    if text.strip():
        out, changes = redact_text(text, "pasted")
        l, r = st.columns(2)
        l.markdown("**Before**")
        l.markdown(f'<div class="cv">{mark_raw(text, changes)}</div>', unsafe_allow_html=True)
        r.markdown("**After**")
        r.markdown(f'<div class="cv">{mark_redacted(out, changes)}</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(changes, columns=["line", "original", "replacement", "rule"]),
                     hide_index=True, width="stretch")

with tabs[6]:
    if not st.session_state.runs:
        st.info("Run the check for one or more tools to compare them here.")
    else:
        rows = []
        for (ds_key, key), r in st.session_state.runs.items():
            a0, a1 = r["res"]["raw"]["audit"], r["res"]["redacted"]["audit"]
            probe = r["res"]["redacted"]["probe"]["summary"]
            rows.append({"Candidate pool": DATASETS[ds_key]["label"].split(",")[0],
                         "Tool": REGISTRY[key]["label"],
                         "Impact ratio, raw": f"{a0['impact_ratio']:.2f} {a0['four_fifths']}",
                         "Impact ratio, redacted": f"{a1['impact_ratio']:.2f} {a1['four_fifths']}",
                         "Twins identical (raw → redacted)": f"{a0['twin_test']['identical']} → "
                                                             f"{a1['twin_test']['identical']}",
                         "Proxy penalties": ", ".join(f"{SIGNAL[s]} −{v['mean_penalty_points']:.0f}"
                                                      for s, v in probe.items() if v["cvs_penalised"]) or "none",
                         "Recommendation": r["res"]["redacted"]["recommendation"]})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
