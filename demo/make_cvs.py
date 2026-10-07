#!/usr/bin/env python
"""Generate the fictional test data for the gender-fair screening demo.

Creates, relative to the project root:
  data/job_description.md
  data/cvs_raw/cv_001.txt ... cv_030.txt   15 men, 15 women
  data/gender_labels.csv                   cv_id, gender, twin_pair_id
  demo/answer_key.csv                      profile, break and part-time flags
                                           (for the presenter, never for the tools)

Design:
  * 15 qualification profiles. Each profile is used once for a man and once
    for a woman, so qualification levels are matched across genders. All
    wording that is not a gender marker (summary, job titles, bullets,
    skills, degree, grade) comes from the profile, so no word reveals gender
    by chance.
  * Profiles P02, P05, P08, P11 and P14 are twin pairs: the two CVs are
    word-for-word identical except for gender markers.
  * Five women in non-twin profiles have a maternity-related career break,
    and one man has a break for full-time study. Their total paid experience
    equals their matched candidate's, so the break is the only difference.
  * Gender markers are spread unevenly, as in real CVs.

All people, employers and institutions are fictional. The seed is fixed.

Usage: python demo/make_cvs.py
"""
import csv
import random
from pathlib import Path

SEED = 13
AS_OF = (2026, 9)  # the month "Present" stands for
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# The 12 job-related keywords from the job description, in the order profiles
# acquire them (a profile with k keywords has the first k).
KEYWORDS = ["SQL", "Excel", "Python", "Dashboards", "Reporting", "Statistics",
            "Tableau", "Data cleaning", "Power BI", "Stakeholder communication",
            "ETL", "A/B testing"]
BULLETS = {
    "SQL": "Wrote SQL queries to join sales, customer and product data",
    "Excel": "Built Excel models to track budgets and forecasts",
    "Python": "Automated recurring analysis in Python",
    "Dashboards": "Designed dashboards for regional managers",
    "Reporting": "Owned weekly KPI reporting for the leadership team",
    "Statistics": "Used statistics to explain changes in customer churn",
    "Tableau": "Published Tableau workbooks used across three departments",
    "Data cleaning": "Led data cleaning for a customer database migration",
    "Power BI": "Maintained Power BI reports for the finance team",
    "Stakeholder communication": "Presented findings to stakeholder groups and agreed next steps",
    "ETL": "Maintained ETL jobs that load the data warehouse each night",
    "A/B testing": "Analysed A/B testing results for website changes",
}

# id, months of paid experience, number of keywords, degree, grade
PROFILES = [
    ("P01", 84, 11, "MSc Data Science", "Distinction"),
    ("P02", 74, 10, "BSc Mathematics", "First Class"),
    ("P03", 66, 10, "BSc Economics", "First Class"),
    ("P04", 60, 9, "BTech Computer Science", "CGPA 8.6/10"),
    ("P05", 54, 9, "BSc Mathematics", "Upper Second (2:1)"),
    ("P06", 50, 8, "BCom Accounting and Finance", "First Class"),
    ("P07", 46, 8, "BSc Computer Science", "Upper Second (2:1)"),
    ("P08", 42, 7, "BSc Economics", "Upper Second (2:1)"),
    ("P09", 38, 7, "BA Psychology", "First Class"),
    ("P10", 34, 6, "BSc Mathematics", "Upper Second (2:1)"),
    ("P11", 30, 6, "BBA", "CGPA 7.9/10"),
    ("P12", 26, 5, "BSc Geography", "Upper Second (2:1)"),
    ("P13", 22, 5, "BCom", "CGPA 7.4/10"),
    ("P14", 18, 4, "BA Economics", "Lower Second (2:2)"),
    ("P15", 14, 3, "BSc Biology", "Upper Second (2:1)"),
]
TWIN_PROFILES = ["P02", "P05", "P08", "P11", "P14"]
# Breaks: profile -> (gender, months, stated reason)
BREAKS = {
    "P01": ("female", 12, "maternity leave"),
    "P03": ("female", 9, "maternity leave"),
    "P04": ("female", 14, "maternity leave and childcare"),
    "P06": ("female", 10, "maternity leave"),
    "P09": ("female", 8, "maternity leave"),
    "P07": ("male", 8, "full-time study"),
}
# Current job held part-time: profile -> gender
PART_TIME = {"P03": "female", "P06": "female", "P09": "female",
             "P10": "female", "P12": "male"}

FOCUS = ["retail and e-commerce analytics", "insurance pricing",
         "supply chain analytics", "banking customer analytics",
         "healthcare operations", "telecom churn analysis",
         "energy usage analysis", "food retail sales",
         "travel booking analytics", "media audience analysis",
         "marketing analytics", "education performance analysis",
         "manufacturing quality analysis", "pharmaceutical sales analysis",
         "consulting analytics"]
BUILT = ["a customer segmentation model", "a sales forecasting model",
         "automated data quality checks", "a pricing analysis toolkit",
         "a churn early-warning model", "a stock-level tracker",
         "a demand planning model", "a survey analysis pipeline",
         "a store performance scorecard", "a claims trend model",
         "a campaign response model", "a delivery time tracker",
         "a defect trend tracker", "a territory sales model",
         "a client benchmarking tool"]
ENJOY = ["turning messy data into clear decisions",
         "explaining numbers to non-technical colleagues",
         "finding patterns in customer behaviour",
         "improving how teams use data",
         "learning new analysis methods"]
TITLES_NOW = ["Senior Data Analyst", "Data Analyst", "Data Analyst",
              "Business Analyst", "Data Analyst"]
TITLES_BEFORE = ["Junior Data Analyst", "Reporting Analyst", "MIS Executive",
                 "Graduate Analyst", "Operations Analyst"]

WOMEN = ["Priya", "Ananya", "Kavya", "Meera", "Neha", "Sarah", "Emily",
         "Aisha", "Fatima", "Laura", "Sneha", "Riya", "Hannah", "Zara", "Divya"]
MEN = ["Arjun", "Rahul", "Vikram", "Rohan", "Aditya", "James", "Daniel",
       "Omar", "Imran", "Thomas", "Karan", "Nikhil", "Samuel", "Ethan", "Varun"]
SURNAMES = ["Sharma", "Iyer", "Menon", "Kapoor", "Rao", "Patel", "Nair",
            "Gupta", "Desai", "Mehta", "Khan", "Bennett", "Hughes", "Fletcher",
            "Joshi", "Reddy", "Ahmed", "Clarke", "Shah", "Verma"]
FAMILY_MEN = ["Suresh", "Ramesh", "Mahesh", "Anil", "Rajesh", "David",
              "Peter", "Michael", "Yusuf", "Harish", "Gopal", "Edward"]
EMPLOYERS = ["Northwind Retail", "Bluefin Insurance", "Corvex Logistics",
             "Harbourline Bank", "Meridale Health", "Kestrova Telecom",
             "Vantora Energy", "Saffronleaf Foods", "Orbitalis Travel",
             "Quillon Media", "Tesserine Analytics", "Brightpath Learning",
             "Ironmere Manufacturing", "Halcyra Pharma", "Peregrina Consulting",
             "Cobaltix Fintech", "Marigold Retail Group", "Silverkey Insurance"]
COLLEGES = ["Ashford", "Kingsbridge", "Ravensworth", "Northgate", "Elmhurst",
            "Westmere", "Larkspur", "Highcliffe"]
SCHOOLS = ["St. Agnes", "Greenfield", "Riverside", "St. Columba", "Hillview",
           "Oakridge"]
SPORTS = ["Cricket", "Football", "Hockey", "Basketball"]


def month_index(year, month):
    return year * 12 + (month - 1)


def fmt(idx):
    return f"{MONTHS[idx % 12]} {idx // 12}"


def build_timeline(months, break_months):
    """Return jobs (start, end) newest first, plus the break interval if any.

    Paid experience always totals `months`; a break pushes earlier jobs back.
    """
    if months >= 60:
        parts = [round(months * 0.4), round(months * 0.35)]
        parts.append(months - sum(parts))
    elif months >= 30:
        parts = [round(months * 0.55)]
        parts.append(months - parts[0])
    else:
        parts = [months]
    end = month_index(*AS_OF)
    jobs, brk = [], None
    for i, length in enumerate(parts):
        start = end - length + 1
        jobs.append((start, end))
        end = start - 1
        if i == 0 and break_months:
            brk = (end - break_months + 1, end)
            end = end - break_months
    return jobs, brk


def profile_content(p_index, profile):
    """Everything about a CV that is not a gender marker or an employer."""
    pid, months, k, degree, grade = profile
    keywords = KEYWORDS[:k]
    rng = random.Random(f"{SEED}-{pid}")
    return {
        "pid": pid,
        "months": months,
        "keywords": keywords,
        "degree": degree,
        "grade": grade,
        "focus": FOCUS[p_index],
        "built": BUILT[p_index],
        "enjoy": ENJOY[p_index % len(ENJOY)],
        "title_now": "Senior Data Analyst" if months >= 66 else rng.choice(TITLES_NOW[1:]),
        "titles_before": rng.sample(TITLES_BEFORE, 2),
        "college": rng.choice(COLLEGES),
        "school": rng.choice(SCHOOLS),
        "sport": rng.choice(SPORTS),
        "sport_role": rng.choice(["Captain", "Member", "Vice-captain"]),
    }


def marker_slots(rng):
    """Which gender markers a CV carries. Shared by both CVs of a twin pair."""
    return {
        "title": rng.random() < 0.45,
        "third_person": rng.random() < 0.55,
        "photo": rng.random() < 0.4,
        "dob": rng.random() < 0.5,
        "gender_field": rng.random() < 0.3,
        "marital": rng.random() < 0.4,
        "married": rng.random() < 0.5,
        "family": rng.random() < 0.3,
        "gendered_college": rng.random() < 0.4,
        "school": rng.random() < 0.35,
        "gendered_school": rng.random() < 0.6,
        "sport": rng.random() < 0.5,
        "society": rng.random() < 0.5,
        "gendered_job": rng.random() < 0.25,
        "job_variant": rng.randrange(2),
        "title_variant": rng.randrange(3),
        "society_variant": rng.randrange(3),
        "neutral_extra": rng.random() < 0.4,
    }


def render_cv(content, gender, slots, person, employers, has_break, part_time):
    f = gender == "female"
    first, last = person["first"], person["last"]

    # Name line, with an optional title
    married = slots["married"]
    if slots["title"]:
        if f:
            options = ["Mrs", "Smt.", "Mrs."] if married else ["Ms", "Miss", "Kumari"]
        else:
            options = ["Mr", "Shri", "Mr."]
        name_line = f"{options[slots['title_variant']]} {first} {last}"
    else:
        name_line = f"{first} {last}"

    lines = [name_line,
             f"Email: {first.lower()}.{last.lower()}@example.com | Phone: +44 7700 900{person['phone']:03d}",
             f"LinkedIn: linkedin.com/in/{first.lower()}-{last.lower()}-{person['phone'] % 97:02d}",
             ""]

    # Summary: third person (gendered pronouns) or neutral
    years = content["months"] // 12
    year_word = "year" if years == 1 else "years"
    if slots["third_person"]:
        s, poss = ("She", "Her") if f else ("He", "His")
        summary = (f"{s} is a data analyst with {years} {year_word} of experience in "
                   f"{content['focus']}. {s} has built {content['built']}. "
                   f"{poss} strengths include clear written communication. "
                   f"{s} enjoys {content['enjoy']}.")
    else:
        summary = (f"Data analyst with {years} {year_word} of experience in "
                   f"{content['focus']}. Has built {content['built']}. "
                   f"Strengths include clear written communication. "
                   f"Enjoys {content['enjoy']}.")
    lines += ["SUMMARY", summary, ""]

    # Experience, newest first
    jobs, brk = build_timeline(content["months"], has_break[1] if has_break else 0)
    kws = content["keywords"]
    chunks = [kws[i::len(jobs)] for i in range(len(jobs))]
    titles = [content["title_now"]] + content["titles_before"]
    lines.append("EXPERIENCE")
    for i, ((start, end), chunk) in enumerate(zip(jobs, chunks)):
        title = titles[i]
        if i == 0 and part_time:
            title += " (part-time)"
        end_txt = "Present" if i == 0 else fmt(end)
        lines.append(f"{title}, {employers[i]} | {fmt(start)} to {end_txt}")
        lines += [f"- {BULLETS[k]}" for k in chunk]
        if i == 0 and brk:
            lines.append(f"Career break ({has_break[2]}) | {fmt(brk[0])} to {fmt(brk[1])}")
    lines.append("")

    # Education
    first_start = jobs[-1][0]
    grad_year = first_start // 12 if first_start % 12 >= 6 else first_start // 12 - 1
    c = content["college"]
    if slots["gendered_college"]:
        # A twin man gets the same name without the gender word
        if f:
            college = f"{c} College for Women" if slots["title_variant"] == 1 \
                else f"{c} Women's College"
        else:
            college = f"{c} College"
    else:
        college = f"{c} College" if slots["title_variant"] != 2 else f"University of {c}"
    lines += ["EDUCATION",
              f"{content['degree']} | {college} | {grad_year} | {content['grade']}"]
    if slots["school"]:
        if slots["gendered_school"]:
            school = f"{content['school']} {'Girls' if f else 'Boys'}' School"
        else:
            school = f"{content['school']} Public School"
        lines.append(f"Higher secondary | {school} | {grad_year - 3}")
    lines.append("")

    lines += ["SKILLS", ", ".join(kws), ""]

    # Activities
    acts = []
    if slots["sport"]:
        acts.append(f"{content['sport_role']}, {'Women' if f else 'Men'}'s {content['sport']} Team")
    if slots["society"]:
        if f:
            acts.append(["Member, Women in Tech Society", "Mentor, Women in Data Network",
                         "Volunteer, Girls Who Code"][slots["society_variant"]])
        else:
            acts.append("Member, Data Science Society")
    if slots["gendered_job"]:
        if slots["job_variant"] == 0:
            acts.append(f"{'Chairwoman' if f else 'Chairman'}, Analytics Club")
        else:
            acts.append(f"{'Waitress' if f else 'Salesman'}, Corner Street Market (summer job)")
    if slots["neutral_extra"] or not acts:
        acts.append("Volunteer data tutor, Community Learning Centre")
    lines += ["ACTIVITIES"] + [f"- {a}" for a in acts] + [""]

    # Personal details
    pers = []
    if slots["dob"]:
        pers.append(f"Date of birth: {person['dob']}")
    if slots["gender_field"]:
        pers.append(f"Gender: {'Female' if f else 'Male'}")
    if slots["marital"]:
        pers.append(f"Marital status: {'Married' if married else 'Single'}")
    if slots["family"]:
        if f and married:
            pers.append(f"Husband's name: {person['family']} {last}")
        else:
            pers.append(f"Father's name: {person['family']} {last}")
    if slots["photo"]:
        pers.append("Photo: attached")
    if pers:
        lines += ["PERSONAL DETAILS"] + pers + [""]

    return "\n".join(lines).rstrip() + "\n", grad_year


JOB_DESCRIPTION = """# Data Analyst (entry to mid level)

**Team:** Commercial Insights   **Contract:** Permanent, full time   **Location:** Hybrid

*Fictional role written for a course demonstration.*

## About the role
We are looking for a Data Analyst with 1 to 6 years of experience to turn
business data into clear, practical recommendations.

## What you will do
- Write SQL to extract and join data from our data warehouse
- Do data cleaning and preparation so that analysis can be trusted
- Build dashboards in Tableau or Power BI for managers across the business
- Own weekly and monthly KPI reporting
- Analyse experiments, including A/B testing, using sound statistics
- Maintain simple ETL jobs that feed our reporting tables
- Present findings to stakeholder groups in plain language

## Essential
- SQL and Excel
- Python for analysis
- Experience of dashboards and regular reporting

## Desirable
- Tableau or Power BI
- Statistics, including A/B testing
- ETL experience
- Stakeholder communication

## Our commitment
We assess every applicant only on job-related skills and experience.
Career breaks are not counted against applicants.
"""


def main():
    rng = random.Random(SEED)
    (DATA / "cvs_raw").mkdir(parents=True, exist_ok=True)
    (DATA / "job_description.md").write_text(JOB_DESCRIPTION, encoding="utf-8")

    women, men = WOMEN[:], MEN[:]
    rng.shuffle(women)
    rng.shuffle(men)
    phones = rng.sample(range(100, 1000), 30)
    records = []  # (text, gender, twin_id, key info)

    for p_index, profile in enumerate(PROFILES):
        content = profile_content(p_index, profile)
        pid = content["pid"]
        twin = pid in TWIN_PROFILES
        twin_id = f"T{TWIN_PROFILES.index(pid) + 1}" if twin else ""
        shared_slots = marker_slots(rng)
        shared_employers = rng.sample(EMPLOYERS, 3)
        for gender in ("female", "male"):
            slots = shared_slots if twin else marker_slots(rng)
            employers = shared_employers if twin else rng.sample(EMPLOYERS, 3)
            names = women if gender == "female" else men
            first = names.pop()
            person = {
                "first": first,
                "last": rng.choice(SURNAMES),
                "phone": phones.pop(),
                "family": rng.choice(FAMILY_MEN),
            }
            brk = BREAKS.get(pid)
            has_break = brk if brk and brk[0] == gender else None
            part_time = PART_TIME.get(pid) == gender
            # Date of birth about 21 years before graduation
            _, grad_year = render_cv(content, gender, slots, {**person, "dob": ""},
                                     employers, has_break, part_time)
            dob_rng = random.Random(f"{SEED}-{pid}-dob")  # shared within a pair
            person["dob"] = (f"{dob_rng.randint(1, 28):02d}/{dob_rng.randint(1, 12):02d}/"
                             f"{grad_year - 21 - dob_rng.randint(0, 1)}")
            text, _ = render_cv(content, gender, slots, person, employers,
                                has_break, part_time)
            records.append((text, gender, twin_id, {
                "profile": pid,
                "career_break": has_break[2] if has_break else "",
                "part_time": "yes" if part_time else "",
                "name": f"{person['first']} {person['last']}",
            }))

    rng.shuffle(records)
    with open(DATA / "gender_labels.csv", "w", newline="", encoding="utf-8") as lab, \
         open(ROOT / "demo" / "answer_key.csv", "w", newline="", encoding="utf-8") as key:
        lab_w = csv.writer(lab)
        key_w = csv.writer(key)
        lab_w.writerow(["cv_id", "gender", "twin_pair_id"])
        key_w.writerow(["cv_id", "gender", "profile", "twin_pair_id",
                        "career_break", "part_time", "name"])
        for i, (text, gender, twin_id, info) in enumerate(records, start=1):
            cv_id = f"cv_{i:03d}"
            (DATA / "cvs_raw" / f"{cv_id}.txt").write_text(text, encoding="utf-8")
            lab_w.writerow([cv_id, gender, twin_id])
            key_w.writerow([cv_id, gender, info["profile"], twin_id,
                            info["career_break"], info["part_time"], info["name"]])

    print(f'{{"cvs_written": {len(records)}, "folder": "data/cvs_raw", '
          f'"labels": "data/gender_labels.csv", "answer_key": "demo/answer_key.csv"}}')


if __name__ == "__main__":
    main()
