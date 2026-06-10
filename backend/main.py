import argparse
import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

load_dotenv()

from database import Base, SessionLocal, engine, get_db
from email_sender import send_email
from models import Company, Job, Preferences, DEFAULT_ROLES
from scraper import run_scraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scraper_state: dict = {
    "is_scraping": False,
    "last_run": None,
    "log": [],
    "jobs_found_this_run": 0,
}


# ---------- DB helpers ----------

def _migrate_db() -> None:
    """Add new columns to existing tables without dropping data."""
    new_cols = [
        "ALTER TABLE jobs ADD COLUMN location TEXT DEFAULT ''",
        "ALTER TABLE jobs ADD COLUMN work_mode TEXT DEFAULT ''",
        "ALTER TABLE jobs ADD COLUMN work_type TEXT DEFAULT ''",
        "ALTER TABLE jobs ADD COLUMN experience TEXT DEFAULT ''",
    ]
    with engine.connect() as conn:
        for sql in new_cols:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists


def _seed_companies(db: Session) -> None:
    if db.query(Company).count() > 0:
        return
    path = os.path.join(os.path.dirname(__file__), "companies.json")
    if not os.path.exists(path):
        return
    with open(path) as f:
        companies = json.load(f)
    for c in companies:
        db.add(Company(name=c["name"], url=c["url"]))
    db.commit()
    logger.info("Seeded %d companies", len(companies))


def _seed_preferences(db: Session) -> None:
    if db.query(Preferences).count() == 0:
        db.add(Preferences(roles=list(DEFAULT_ROLES)))
        db.commit()


def _get_prefs(db: Session) -> dict:
    prefs = db.query(Preferences).first()
    if not prefs:
        return {"roles": list(DEFAULT_ROLES), "locations": [], "experience": [],
                "work_type": [], "work_mode": [], "salary_min": None, "salary_max": None}
    return {
        "roles": prefs.roles or [],
        "locations": prefs.locations or [],
        "experience": prefs.experience or [],
        "work_type": prefs.work_type or [],
        "work_mode": prefs.work_mode or [],
        "salary_min": prefs.salary_min,
        "salary_max": prefs.salary_max,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    db = SessionLocal()
    try:
        _seed_companies(db)
        _seed_preferences(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Job Scraper API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic schemas ----------

class CompanyCreate(BaseModel):
    name: str
    url: str


class PreferencesUpdate(BaseModel):
    roles: List[str] = []
    locations: List[str] = []
    experience: List[str] = []
    work_type: List[str] = []
    work_mode: List[str] = []
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


# ---------- Companies ----------

@app.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.added_at).all()


@app.post("/companies", status_code=201)
def add_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(name=payload.name.strip(), url=payload.url.strip())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@app.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"ok": True}


# ---------- Preferences ----------

@app.get("/preferences")
def get_preferences(db: Session = Depends(get_db)):
    return _get_prefs(db)


@app.put("/preferences")
def update_preferences(payload: PreferencesUpdate, db: Session = Depends(get_db)):
    prefs = db.query(Preferences).first()
    if not prefs:
        prefs = Preferences()
        db.add(prefs)

    prefs.roles = payload.roles
    prefs.locations = payload.locations
    prefs.experience = payload.experience
    prefs.work_type = payload.work_type
    prefs.work_mode = payload.work_mode
    prefs.salary_min = payload.salary_min
    prefs.salary_max = payload.salary_max
    prefs.updated_at = datetime.utcnow()
    db.commit()
    return _get_prefs(db)


# ---------- Scrape ----------

@app.post("/scrape")
async def trigger_scrape(db: Session = Depends(get_db)):
    if scraper_state["is_scraping"]:
        raise HTTPException(status_code=409, detail="A scrape is already in progress")

    companies = db.query(Company).all()
    if not companies:
        return {"jobs": [], "count": 0, "message": "No companies configured"}

    prefs = _get_prefs(db)
    if not prefs.get("roles"):
        raise HTTPException(status_code=400, detail="No role keywords configured in preferences")

    scraper_state["is_scraping"] = True
    scraper_state["log"] = []
    scraper_state["jobs_found_this_run"] = 0

    def log(msg: str):
        scraper_state["log"].append({"time": datetime.utcnow().isoformat(), "message": msg})

    try:
        raw_jobs = await run_scraper(companies, prefs, log)

        new_jobs = []
        for jd in raw_jobs:
            exists = db.query(Job).filter(
                Job.company_id == jd["company_id"],
                Job.title == jd["title"],
            ).first()
            if not exists:
                db.add(Job(
                    company_id=jd["company_id"],
                    title=jd["title"],
                    url=jd.get("url", ""),
                    source=jd.get("source", "unknown"),
                    location=jd.get("location", ""),
                    work_mode=jd.get("work_mode", ""),
                    work_type=jd.get("work_type", ""),
                    experience=jd.get("experience", ""),
                ))
                new_jobs.append(jd)

        db.commit()
        scraper_state["last_run"] = datetime.utcnow().isoformat()
        scraper_state["jobs_found_this_run"] = len(new_jobs)
        log(f"✅ Done! {len(new_jobs)} new job(s) saved.")
        return {"jobs": new_jobs, "count": len(new_jobs)}

    except Exception as exc:
        log(f"❌ Scraper error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        scraper_state["is_scraping"] = False


# ---------- Jobs ----------

@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).join(Company).order_by(Job.found_at.desc()).all()
    return [
        {
            "id": j.id,
            "company_id": j.company_id,
            "company_name": j.company.name,
            "title": j.title,
            "url": j.url,
            "source": j.source,
            "location": j.location or "",
            "work_mode": j.work_mode or "",
            "work_type": j.work_type or "",
            "experience": j.experience or "",
            "found_at": j.found_at.isoformat() if j.found_at else None,
            "emailed": j.emailed,
        }
        for j in jobs
    ]


# ---------- Email ----------

@app.post("/send-email")
def send_email_digest(db: Session = Depends(get_db)):
    jobs = db.query(Job).join(Company).filter(Job.emailed == False).all()
    if not jobs:
        return {"message": "No new jobs to send — inbox is up to date"}

    jobs_data = [
        {
            "title": j.title,
            "url": j.url,
            "source": j.source,
            "company_name": j.company.name,
            "location": j.location or "",
            "work_mode": j.work_mode or "",
            "work_type": j.work_type or "",
        }
        for j in jobs
    ]
    try:
        send_email(jobs_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    for j in jobs:
        j.emailed = True
    db.commit()
    return {"message": f"Email sent with {len(jobs)} job(s)"}


# ---------- Status ----------

@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    return {
        "is_scraping": scraper_state["is_scraping"],
        "last_run": scraper_state["last_run"],
        "jobs_count": db.query(Job).count(),
        "companies_count": db.query(Company).count(),
        "jobs_found_this_run": scraper_state["jobs_found_this_run"],
        "log": scraper_state["log"][-100:],
    }


# ---------- Headless mode ----------

async def _headless_run() -> None:
    print("🤖 Job Scraper — headless mode")
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    db = SessionLocal()
    try:
        _seed_companies(db)
        _seed_preferences(db)
        companies = db.query(Company).all()
        if not companies:
            print("No companies configured. Exiting.")
            return

        prefs = _get_prefs(db)
        print(f"Roles: {prefs['roles']}")
        print(f"Scraping {len(companies)} companies...")

        raw_jobs = await run_scraper(companies, prefs, log_callback=print)

        new_jobs = []
        for jd in raw_jobs:
            exists = db.query(Job).filter(
                Job.company_id == jd["company_id"],
                Job.title == jd["title"],
            ).first()
            if not exists:
                db.add(Job(
                    company_id=jd["company_id"],
                    title=jd["title"],
                    url=jd.get("url", ""),
                    source=jd.get("source", "unknown"),
                    location=jd.get("location", ""),
                    work_mode=jd.get("work_mode", ""),
                    work_type=jd.get("work_type", ""),
                    experience=jd.get("experience", ""),
                ))
                new_jobs.append(jd)

        db.commit()
        print(f"✅ {len(new_jobs)} new job(s) saved.")

        if new_jobs:
            print("📧 Sending email digest...")
            try:
                send_email(new_jobs)
                for j in db.query(Job).filter(Job.emailed == False).all():
                    j.emailed = True
                db.commit()
                print("✅ Email sent!")
            except Exception as exc:
                print(f"❌ Email failed: {exc}", file=sys.stderr)
        else:
            print("No new jobs — skipping email.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true",
                        help="Run scrape + email then exit (GitHub Actions)")
    args = parser.parse_args()

    if args.headless:
        asyncio.run(_headless_run())
    else:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
