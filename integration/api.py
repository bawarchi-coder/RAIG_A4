"""Fairness layer as an HTTP API, for HR software that is not an AI agent.

Run from the project root:
  .venv\\Scripts\\python -m uvicorn integration.api:app --port 8000
Then open http://127.0.0.1:8000/docs to try every endpoint in the browser.

Endpoints
  GET  /screeners       screening tools registered on this server
  POST /redact          one CV in, redacted CV and change log out
  POST /leak-check      redacted CVs in, surviving gender markers out
  POST /audit           a ranking and gender labels in, audit figures out
  POST /screen-fairly   CVs in; redact, leak-check, screen blind with a registered
                        tool, and (if labels are given) audit, probe and report

The same functions as the agent skill are used, so the numbers match.
Screeners are configured on the server in integration/screeners.json. A caller
picks one by name and can never send a command to execute.
"""
import json
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "gender-fair-screening" / "scripts"))
from audit_shortlist import audit as run_audit  # noqa: E402
from leak_check import check_texts  # noqa: E402
from pipeline import run as run_pipeline  # noqa: E402
from redact_cv import redact_text  # noqa: E402
from screener_adapter import ScreenerError  # noqa: E402

REGISTRY = json.loads((ROOT / "integration" / "screeners.json").read_text(encoding="utf-8"))

app = FastAPI(
    title="Gender-Fair Screening API",
    description="A plug-in fairness layer for CV screening: it hides gender before screening "
                "and checks the outcome after. Course demonstration, not for real hiring decisions.",
    version="1.0",
)


class CV(BaseModel):
    cv_id: str = Field(examples=["cv_001"])
    text: str = Field(examples=["Ms Priya Sharma\nSUMMARY\nShe has built dashboards in Tableau."])


class Label(BaseModel):
    cv_id: str
    gender: str = Field(examples=["female"])
    twin_pair_id: str = ""


class RankingRow(BaseModel):
    cv_id: str
    score: float
    shortlisted: bool
    rank: int | None = None


class RedactRequest(BaseModel):
    text: str = Field(examples=["Mrs. Priya Sharma\nEmail: priya.sharma@example.com\n\nSUMMARY\n"
                                "She has built dashboards. Her strengths include SQL.\n\nACTIVITIES\n"
                                "- Captain, Women's Cricket Team\n\nPERSONAL DETAILS\n"
                                "Marital status: Married\nPhoto: attached\n"])
    cv_id: str = "cv"


class LeakRequest(BaseModel):
    cvs: list[CV]
    known_names: list[str] = []


class AuditRequest(BaseModel):
    ranking: list[RankingRow]
    labels: list[Label]


class ScreenRequest(BaseModel):
    job_description: str
    cvs: list[CV]
    screener: str = Field("screener_a", description="name from GET /screeners")
    top_k: int = 10
    labels: list[Label] | None = Field(None, description="optional; enables audit, probe and report. "
                                                         "Never passed to the screener.")
    role: str = "Data Analyst"
    include_baseline: bool = Field(False, description="also screen the raw CVs, for comparison")


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/docs")


@app.get("/screeners")
def screeners():
    return {name: {"label": s["label"], "type": s["type"]} for name, s in REGISTRY.items()}


@app.post("/redact")
def redact(req: RedactRequest):
    redacted, changes = redact_text(req.text, req.cv_id)
    return {"cv_id": req.cv_id, "redacted_text": redacted, "changes": changes}


@app.post("/leak-check")
def leak_check(req: LeakRequest):
    leaks = check_texts({c.cv_id: c.text for c in req.cvs}, set(req.known_names))
    return {"files_checked": len(req.cvs), "leak_count": len(leaks), "leaks": leaks}


@app.post("/audit")
def audit(req: AuditRequest):
    result = run_audit([r.model_dump() for r in req.ranking], [lab.model_dump() for lab in req.labels])
    if "error" in result:
        raise HTTPException(422, result["error"])
    return result


@app.post("/screen-fairly")
def screen_fairly(req: ScreenRequest):
    if req.screener not in REGISTRY:
        raise HTTPException(404, f"unknown screener '{req.screener}'; see GET /screeners")
    screener = REGISTRY[req.screener]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        raw = tmp / "raw"
        raw.mkdir()
        for cv in req.cvs:
            name = "".join(ch for ch in cv.cv_id if ch.isalnum() or ch in "-_") or "cv"
            (raw / f"{name}.txt").write_text(cv.text, encoding="utf-8")
        jd = tmp / "job_description.md"
        jd.write_text(req.job_description, encoding="utf-8")
        labels_csv = None
        if req.labels:
            labels_csv = tmp / "labels.csv"
            labels_csv.write_text("cv_id,gender,twin_pair_id\n" + "".join(
                f"{lab.cv_id},{lab.gender},{lab.twin_pair_id}\n" for lab in req.labels), encoding="utf-8")
        try:
            res = run_pipeline(raw, jd, labels_csv, screener, tmp / "out", screener["label"], req.role,
                               req.top_k, baseline=req.include_baseline and bool(req.labels), cwd=ROOT)
        except ScreenerError as e:
            raise HTTPException(502, str(e))
    res.pop("out_dir", None)
    res["redaction"] = {"summary": {k: v for k, v in res["redaction"]["summary"].items() if k != "output"
                                    and k != "log"},
                        "changes": res["redaction"]["changes"]}
    return res
