#!/usr/bin/env python
"""Generate a SECOND fictional dataset, built to test the fairness layer on
data it was not designed around.

Creates, relative to the project root:
  data2/job_description.md                  Software Developer role
  data2/cvs_raw/cv_001.txt ... cv_040.txt   16 women, 24 men (unbalanced pool)
  data2/gender_labels.csv                   cv_id, gender (F/M), twin_pair_id
  demo/answer_key_set2.csv                  for the presenter only

How it differs from dataset 1 (demo/make_cvs.py):
  * a different role and job description
  * an unbalanced pool and a shortlist of 12
  * three CV layouts: UK-style (Title Case headings, dates as 03/2021),
    Indian biodata (Name: field, D/o or S/o line, Sex, Age, declaration with
    the name), US resume (full month names, sororities and fraternities)
  * new gender markers: "Pronouns: she/her", "nee" maiden names, "Head Girl",
    "Hostess", personal websites containing the candidate's name
  * career breaks written as "Maternity leave", a short paternity leave
    (below the 6-month gap threshold) and one gap with no explanation
  * gender labels written as F / M

Matching: 16 profiles are used once for a woman and once for a man; 8 extra
profiles (men only) are spread across the range of strength. Four profiles
are twin pairs, identical except for gender markers. All people, employers
and institutions are fictional. The seed is fixed.

Usage: python demo/make_cvs_set2.py
"""
import csv
import random
from pathlib import Path

SEED = 2026
AS_OF = (2026, 9)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data2"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FULL_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]

KEYWORDS = ["Python", "SQL", "Git", "Java", "JavaScript", "REST API", "Unit testing",
            "Agile", "Docker", "React", "AWS", "CI/CD"]
BULLETS = {
    "Python": "Built internal tools in Python",
    "SQL": "Optimised SQL queries for the orders service",
    "Git": "Reviewed pull requests and managed release branches in Git",
    "Java": "Maintained Java microservices for payments",
    "JavaScript": "Fixed front-end bugs in JavaScript",
    "REST API": "Designed a REST API for partner integrations",
    "Unit testing": "Raised unit testing coverage from 40% to 85%",
    "Agile": "Worked in two-week Agile sprints",
    "Docker": "Packaged services with Docker",
    "React": "Built React components for the customer portal",
    "AWS": "Deployed services on AWS Lambda and S3",
    "CI/CD": "Set up CI/CD pipelines for automatic releases",
}

# id, months of paid experience, number of keywords, degree, grade
PAIRED = [
    ("S01", 92, 12, "MTech Computer Science", "CGPA 9.1/10"),
    ("S02", 82, 11, "BEng Software Engineering", "First Class"),
    ("S03", 74, 11, "BSc Computer Science", "First Class"),
    ("S04", 68, 10, "BTech Information Technology", "CGPA 8.4/10"),
    ("S05", 60, 10, "BSc Computer Science", "Upper Second (2:1)"),
    ("S06", 56, 9, "BSc Mathematics and Computing", "First Class"),
    ("S07", 50, 9, "BTech Electronics", "CGPA 8.0/10"),
    ("S08", 46, 8, "BSc Computer Science", "Upper Second (2:1)"),
    ("S09", 42, 8, "BCA", "CGPA 8.2/10"),
    ("S10", 36, 7, "BSc Physics", "Upper Second (2:1)"),
    ("S11", 32, 7, "BEng Computer Engineering", "Upper Second (2:1)"),
    ("S12", 28, 6, "BSc Computer Science", "Lower Second (2:2)"),
    ("S13", 24, 6, "BCA", "CGPA 7.5/10"),
    ("S14", 20, 5, "BSc Information Systems", "Upper Second (2:1)"),
    ("S15", 16, 4, "BTech Mechanical Engineering", "CGPA 7.2/10"),
    ("S16", 12, 3, "BSc Mathematics", "Upper Second (2:1)"),
]
EXTRA_MEN = [
    ("E01", 78, 11, "BSc Computer Science", "First Class"),
    ("E02", 64, 10, "BTech Computer Science", "CGPA 8.3/10"),
    ("E03", 52, 9, "BEng Software Engineering", "Upper Second (2:1)"),
    ("E04", 44, 8, "BSc Computer Science", "Upper Second (2:1)"),
    ("E05", 34, 7, "BCA", "CGPA 7.8/10"),
    ("E06", 26, 6, "BSc Mathematics", "Upper Second (2:1)"),
    ("E07", 18, 5, "BSc Information Technology", "Lower Second (2:2)"),
    ("E08", 14, 3, "BSc Statistics", "Upper Second (2:1)"),
]
TWINS = ["S02", "S05", "S08", "S12"]
# profile -> (gender, months, how the break is written: "line" text, or None for an unexplained gap)
BREAKS = {
    "S01": ("F", 12, "Maternity leave"),
    "S03": ("F", 10, "Career break (maternity and childcare)"),
    "S06": ("F", 9, "Sabbatical (caring for family)"),
    "S09": ("F", 14, "Maternity leave"),
    "S11": ("F", 10, None),                       # gap with no explanation
    "S04": ("M", 3, "Paternity leave"),            # below the 6-month threshold
    "E03": ("M", 8, "Career break (travel)"),
}
PART_TIME = {"S06": ("F", "(Part-time, 0.6 FTE)"), "S10": ("F", "(part time)"),
             "S13": ("F", "(Part-time)"), "E06": ("M", "(Part-time)")}

FOCUS = ["payment systems", "e-commerce platforms", "logistics software", "banking apps",
         "healthcare booking systems", "telecom billing", "energy trading tools",
         "travel booking engines", "media streaming services", "insurance quote engines",
         "learning platforms", "retail inventory systems", "public sector websites",
         "food delivery apps", "fintech dashboards", "HR software", "gaming backends",
         "property listing sites", "ticketing systems", "analytics platforms",
         "warehouse robotics software", "mobile banking", "marketplace search", "IoT devices"]
ENJOY = ["clean, well-tested code", "mentoring new joiners", "fixing hard bugs",
         "improving developer tooling", "working closely with designers"]
TITLES_NOW = ["Software Developer", "Software Engineer", "Backend Developer", "Full Stack Developer"]
TITLES_BEFORE = ["Junior Developer", "Graduate Software Engineer", "Associate Developer",
                 "Software Engineering Intern", "Trainee Programmer"]
EMPLOYERS = ["Nimbusly Tech", "Corelight Payments", "Brightwire Systems", "Quantara Labs",
             "Velvetline Software", "Tidewater Digital", "Orchard Logic", "Pinecrest Solutions",
             "Zephyra Cloud", "Ironbark Systems", "Lumora Apps", "Saltmarsh Software",
             "Kitewing Labs", "Bramble Data", "Northlake Digital", "Copperfield IT"]
COLLEGES = ["Hollinsby", "Marchwood", "Easterbrook", "Wrenfield", "Ashcombe", "Delbridge"]
SCHOOLS = ["Riverside", "St. Hilda's", "Oakfield", "St. Mary's", "Greenway"]
WOMEN = ["Aditi", "Bhavna", "Charlotte", "Deepa", "Eleanor", "Farah", "Gauri", "Harriet",
         "Isha", "Jasmine", "Kritika", "Lucy", "Mehak", "Nandini", "Olivia", "Pooja"]
MEN = ["Abhishek", "Benjamin", "Chirag", "Dev", "Edward", "Faisal", "Gaurav", "Harry",
       "Ishaan", "Jack", "Kunal", "Liam", "Manish", "Noah", "Oscar", "Pranav", "Rajat",
       "Sameer", "Tushar", "Utkarsh", "Vivek", "William", "Yash", "Zubin"]
SURNAMES = ["Agarwal", "Banerjee", "Chopra", "Dutta", "Fernandes", "Ghosh", "Hale",
            "Jain", "Kulkarni", "Lawson", "Malhotra", "Pillai", "Quinn", "Saxena",
            "Thakur", "Upadhyay", "Wade", "Yadav"]
FATHERS = ["Ramesh", "Suresh", "Prakash", "Vinod", "Sunil", "Ashok", "Dinesh", "Mukesh"]


def idx(year, month):
    return year * 12 + month - 1


def fmt(i, style, present=False):
    if present:
        return {"uk": "present", "biodata": "Present", "us": "Present"}[style]
    m, y = i % 12, i // 12
    if style == "uk":
        return f"{m + 1:02d}/{y}"
    if style == "biodata":
        return f"{MONTHS[m]} {y}"
    return f"{FULL_MONTHS[m]} {y}"


def date_range(start, end, style, present=False):
    sep = {"uk": " – ", "biodata": " - ", "us": " – "}[style]
    return f"{fmt(start, style)}{sep}{fmt(end, style, present)}"


def timeline(months, break_months):
    """Jobs (start, end) newest first and the break (start, end); paid months fixed."""
    if months >= 60:
        parts = [round(months * 0.4), round(months * 0.35)]
        parts.append(months - sum(parts))
    elif months >= 26:
        parts = [round(months * 0.55)]
        parts.append(months - parts[0])
    else:
        parts = [months]
    end = idx(*AS_OF)
    jobs, brk = [], None
    for i, length in enumerate(parts):
        start = end - length + 1
        jobs.append((start, end))
        end = start - 1
        if i == 0 and break_months:
            brk = (end - break_months + 1, end)
            end -= break_months
    return jobs, brk


def content_for(p_index, profile, rng):
    pid, months, k, degree, grade = profile
    return {"pid": pid, "months": months, "keywords": KEYWORDS[:k], "degree": degree, "grade": grade,
            "focus": FOCUS[p_index % len(FOCUS)], "enjoy": ENJOY[p_index % len(ENJOY)],
            "title_now": "Senior Software Engineer" if months >= 74 else rng.choice(TITLES_NOW),
            "titles_before": rng.sample(TITLES_BEFORE, 2), "college": rng.choice(COLLEGES),
            "school": rng.choice(SCHOOLS)}


def slots_for(rng):
    return {"style": rng.choice(["uk", "biodata", "us"]),
            "title": rng.random() < 0.5, "married": rng.random() < 0.45,
            "third_person": rng.random() < 0.35, "pronouns_line": rng.random() < 0.4,
            "website": rng.random() < 0.5, "nee": rng.random() < 0.6,
            "gendered_college": rng.random() < 0.35, "head_role": rng.random() < 0.3,
            "greek": rng.random() < 0.5, "team": rng.random() < 0.5,
            "summer_job": rng.random() < 0.5, "society": rng.random() < 0.4,
            "photo": rng.random() < 0.6, "variant": rng.randrange(3)}


def render(c, gender, s, person, employers, brk_info, part_time):
    f = gender == "F"
    style = s["style"]
    first, last = person["first"], person["last"]
    maiden = person["maiden"]
    married = s["married"]
    titles = (["Mrs.", "Smt."] if married else ["Ms.", "Kumari"]) if f else ["Mr.", "Shri"]
    title = titles[s["variant"] % 2]
    years = c["months"] // 12
    yrs = f"{years} year" + ("" if years == 1 else "s")
    he, his = ("she", "her") if f else ("he", "his")
    L = []

    # ---- header
    if style == "biodata":
        L += ["CURRICULUM VITAE", "",
              f"Name: {title + ' ' if s['title'] else ''}{first} {last}"]
        rel = "W/o" if f and married else ("D/o" if f else "S/o")
        rel_name = person["husband"] if f and married else person["father"]
        L += [f"{rel} Shri {rel_name} {last if not (f and married) else last}",
              f"Email: {first.lower()}.{last.lower()}{person['n']}@example.com",
              f"Mobile: +44 7700 900{person['phone']:03d}", ""]
    else:
        name_line = f"{first} {last}"
        if f and married and s["nee"] and style == "uk":
            name_line += f" (née {maiden})"
        L.append(name_line)
        contact = f"{first.lower()}.{last.lower()}@example.org | +44 7700 900{person['phone']:03d}"
        if s["website"]:
            contact += f" | www.{first.lower()}{last.lower()}.dev"
        L.append(contact)
        if s["pronouns_line"] and style in ("uk", "us"):
            L.append(f"Pronouns: {he}/{'her' if f else 'him'}")
        L.append("")

    # ---- summary
    heading = {"uk": "Profile", "biodata": "CAREER OBJECTIVE", "us": "SUMMARY"}[style]
    if s["third_person"]:
        S = he.capitalize()
        summary = (f"{S} is a software developer with {yrs} of experience building "
                   f"{c['focus']}. {S} has shipped features used by thousands of customers. "
                   f"{his.capitalize()} colleagues value {his} calm approach. {S} enjoys {c['enjoy']}.")
    else:
        summary = (f"I am a software developer with {yrs} of experience building {c['focus']}. "
                   f"I have shipped features used by thousands of customers and I enjoy {c['enjoy']}.")
    L += [heading, summary, ""]

    # ---- experience
    break_months = brk_info[1] if brk_info else 0
    jobs, brk = timeline(c["months"], break_months)
    kws = c["keywords"]
    chunks = [kws[i::len(jobs)] for i in range(len(jobs))]
    titles_ = [c["title_now"]] + c["titles_before"]
    L.append({"uk": "Work Experience", "biodata": "PROFESSIONAL EXPERIENCE", "us": "EXPERIENCE"}[style])
    for i, ((start, end), chunk) in enumerate(zip(jobs, chunks)):
        t = titles_[i] + (f" {part_time}" if i == 0 and part_time else "")
        sep = {"uk": ", ", "biodata": " at ", "us": " | "}[style]
        L.append(f"{t}{sep}{employers[i]} | {date_range(start, end, style, present=(i == 0))}")
        L += [f"- {BULLETS[k]}" for k in chunk]
        if i == 0 and brk and brk_info[2]:
            L.append(f"{brk_info[2]} | {date_range(brk[0], brk[1], style)}")
    L.append("")

    # ---- education
    first_start = jobs[-1][0]
    grad = first_start // 12 if first_start % 12 >= 6 else first_start // 12 - 1
    col = c["college"]
    if s["gendered_college"]:
        college = f"{col} College for Women" if f else f"{col} College"
    else:
        college = f"{col} University" if s["variant"] != 1 else f"{col} Institute of Technology"
    L.append({"uk": "Education", "biodata": "EDUCATIONAL QUALIFICATIONS", "us": "EDUCATION"}[style])
    L.append(f"{c['degree']}, {college}, {grad} ({c['grade']})")
    if s["head_role"]:
        L.append(f"A levels / Class XII, {c['school']} School, {grad - 3}: {'Head Girl' if f else 'Head Boy'}")
    L.append("")

    # ---- skills
    L += [{"uk": "Technical Skills", "biodata": "KEY SKILLS", "us": "SKILLS"}[style], ", ".join(kws), ""]

    # ---- activities
    acts = []
    if s["greek"] and style == "us":
        acts.append(f"Treasurer, university {'sorority' if f else 'fraternity'}")
    if s["team"]:
        acts.append(("Ladies' badminton team" if f else "Men's badminton team") if style == "uk"
                    else f"Member, {'Women' if f else 'Men'}'s basketball team")
    if s["summer_job"]:
        acts.append(f"{'Hostess' if f else 'Waiter'}, Lakeside Restaurant (summer job)")
    if s["society"]:
        acts.append("Volunteer, Women Who Code" if f else "Volunteer, Code Club")
    acts.append("Contributor to open-source projects")
    L += [{"uk": "Interests", "biodata": "EXTRA-CURRICULAR ACTIVITIES",
           "us": "LEADERSHIP & ACTIVITIES"}[style]] + [f"- {a}" for a in acts] + [""]

    # ---- personal details
    if style == "biodata":
        L += ["PERSONAL DETAILS", f"Sex: {'Female' if f else 'Male'}", f"Age: {person['age']} years",
              f"Marital Status: {'Married' if married else 'Unmarried'}", "Nationality: Indian"]
        if s["photo"]:
            L.append("[Photograph attached]")
        L += ["", "DECLARATION",
              "I hereby declare that the above information is true to the best of my knowledge.",
              f"({first} {last})"]
    return "\n".join(L).rstrip() + "\n", grad


JOB = """# Software Developer (graduate to mid level)

*Fictional role written for a course demonstration.*

## The role
Build and maintain the services behind our customer apps, in a small
cross-functional team. We are looking for 1 to 7 years of experience.

## You will
- Write backend code in Python and Java, and front-end code in JavaScript with React
- Design and maintain a REST API used by partners
- Write SQL against our transactional database
- Use Git for version control and code review
- Practise unit testing and keep CI/CD pipelines green
- Package services with Docker and deploy them on AWS
- Work in Agile sprints with product and design

## Our commitment
We assess every applicant only on job-related skills and experience.
Career breaks, part-time work and caring responsibilities are not counted against applicants.
"""


def main():
    rng = random.Random(SEED)
    (OUT / "cvs_raw").mkdir(parents=True, exist_ok=True)
    (OUT / "job_description.md").write_text(JOB, encoding="utf-8")
    women, men = WOMEN[:], MEN[:]
    rng.shuffle(women)
    rng.shuffle(men)
    phones = rng.sample(range(100, 1000), 40)
    records = []

    def person_for(gender):
        names = women if gender == "F" else men
        return {"first": names.pop(), "last": rng.choice(SURNAMES), "maiden": rng.choice(SURNAMES),
                "husband": rng.choice(FATHERS), "father": rng.choice(FATHERS),
                "phone": phones.pop(), "n": rng.randint(10, 99)}

    def make(content, gender, slots, employers, twin_id):
        pid = content["pid"]
        b = BREAKS.get(pid)
        brk = b if b and b[0] == gender else None
        pt = PART_TIME.get(pid)
        part = pt[1] if pt and pt[0] == gender else ""
        person = person_for(gender)
        _, grad = render(content, gender, slots, {**person, "age": 0}, employers, brk, part)
        person["age"] = 2026 - (grad - 21)
        text, _ = render(content, gender, slots, person, employers, brk, part)
        records.append((text, gender, twin_id, {"profile": pid, "style": slots["style"],
                                                "career_break": (brk[2] or "unexplained gap") if brk else "",
                                                "part_time": "yes" if part else "",
                                                "name": f"{person['first']} {person['last']}"}))

    for i, profile in enumerate(PAIRED):
        content = content_for(i, profile, rng)
        twin = profile[0] in TWINS
        twin_id = f"T{TWINS.index(profile[0]) + 1}" if twin else ""
        shared_slots, shared_emp = slots_for(rng), rng.sample(EMPLOYERS, 3)
        for gender in ("F", "M"):
            make(content, gender, shared_slots if twin else slots_for(rng),
                 shared_emp if twin else rng.sample(EMPLOYERS, 3), twin_id)
    for j, profile in enumerate(EXTRA_MEN):
        content = content_for(len(PAIRED) + j, profile, rng)
        make(content, "M", slots_for(rng), rng.sample(EMPLOYERS, 3), "")

    rng.shuffle(records)
    with open(OUT / "gender_labels.csv", "w", newline="", encoding="utf-8") as lab, \
         open(ROOT / "demo" / "answer_key_set2.csv", "w", newline="", encoding="utf-8") as key:
        lw, kw = csv.writer(lab), csv.writer(key)
        lw.writerow(["cv_id", "gender", "twin_pair_id"])
        kw.writerow(["cv_id", "gender", "profile", "twin_pair_id", "style", "career_break", "part_time", "name"])
        for n, (text, gender, twin_id, info) in enumerate(records, start=1):
            cv_id = f"cv_{n:03d}"
            (OUT / "cvs_raw" / f"{cv_id}.txt").write_text(text, encoding="utf-8")
            lw.writerow([cv_id, gender, twin_id])
            kw.writerow([cv_id, gender, info["profile"], twin_id, info["style"], info["career_break"],
                         info["part_time"], info["name"]])
    print(f'{{"cvs_written": {len(records)}, "folder": "data2/cvs_raw", "labels": "data2/gender_labels.csv"}}')


if __name__ == "__main__":
    main()
