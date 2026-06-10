import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0; +https://github.com/job-scraper)"
}

MAX_DIRECT_PAGES = 5
MAX_DIRECT_JOBS = 50


# ---------- Normalisation helpers ----------

def _normalize_work_type(raw: str) -> str:
    r = raw.lower()
    if "full" in r:
        return "full-time"
    if "part" in r:
        return "part-time"
    if "contract" in r or "freelance" in r or "contractor" in r:
        return "contract"
    if "intern" in r:
        return "internship"
    return ""


def _infer_work_mode(title: str, location: str, is_remote: bool = False) -> str:
    if is_remote:
        return "remote"
    combined = f"{title} {location}".lower()
    if "remote" in combined:
        return "remote"
    if "hybrid" in combined:
        return "hybrid"
    if any(w in combined for w in ["on-site", "onsite", "in-office", "office-based"]):
        return "on-site"
    return ""


def _infer_experience(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["junior", "jr.", "jr ", "entry", "associate", "graduate", "intern"]):
        return "entry"
    if any(w in t for w in ["senior", "sr.", "sr ", "lead", "staff", "principal", "architect"]):
        return "senior"
    if any(w in t for w in ["mid ", "mid-", "middle", "intermediate", "ii "]):
        return "mid"
    return "mid"


def extract_slug(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or url
    domain = domain.replace("www.", "")
    return domain.split(".")[0].lower()


def name_to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ---------- Preference matching ----------

def match_job(job: dict, prefs: dict) -> bool:
    """Return True if the job satisfies every active preference filter."""
    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()
    work_mode = (job.get("work_mode") or "").lower()
    work_type = (job.get("work_type") or "").lower()

    # Roles are required — empty list blocks everything
    roles = [r.lower() for r in (prefs.get("roles") or [])]
    if not roles or not any(r in title for r in roles):
        return False

    # Location — only apply when the job has location data
    loc_filter = [lf.lower() for lf in (prefs.get("locations") or [])]
    if loc_filter and location:
        combined = f"{title} {location} {work_mode}"
        is_remote_job = "remote" in combined
        has_remote_in_filter = any("remote" in lf for lf in loc_filter)
        if not (is_remote_job and has_remote_in_filter):
            if not any(lf in location for lf in loc_filter):
                return False

    # Experience — inferred from title
    exp_filter = [e.lower() for e in (prefs.get("experience") or [])]
    if exp_filter:
        if _infer_experience(title) not in exp_filter:
            return False

    # Work mode
    wm_filter = [wm.lower() for wm in (prefs.get("work_mode") or [])]
    if wm_filter:
        effective = work_mode or _infer_work_mode(title, location)
        if effective and effective not in wm_filter:
            return False

    # Work type — only apply when job has explicit data
    wt_filter = [wt.lower() for wt in (prefs.get("work_type") or [])]
    if wt_filter and work_type:
        if work_type not in wt_filter:
            return False

    return True


# ---------- ATS scrapers ----------

async def _scrape_greenhouse(
    slug: str, client: httpx.AsyncClient, prefs: dict
) -> tuple[bool, list[dict]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?per_page=500"
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return False, []
        data = resp.json()
        jobs = []
        for job in data.get("jobs", []):
            location_obj = job.get("location", {})
            location = location_obj.get("name", "") if isinstance(location_obj, dict) else ""
            title = job.get("title", "")
            j = {
                "title": title,
                "url": job.get("absolute_url", ""),
                "source": "greenhouse",
                "location": location,
                "work_mode": _infer_work_mode(title, location),
                "work_type": "",
                "experience": _infer_experience(title),
            }
            if match_job(j, prefs):
                jobs.append(j)
        return True, jobs
    except Exception as exc:
        logger.debug("Greenhouse error for %s: %s", slug, exc)
        return False, []


async def _scrape_lever(
    slug: str, client: httpx.AsyncClient, prefs: dict
) -> tuple[bool, list[dict]]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return False, []
        data = resp.json()
        if not isinstance(data, list):
            return False, []
        jobs = []
        for job in data:
            cats = job.get("categories") or {}
            title = job.get("text", "") if isinstance(job.get("text"), str) else ""
            location = cats.get("location", "") if isinstance(cats, dict) else ""
            work_type_raw = cats.get("commitment", "") if isinstance(cats, dict) else ""
            j = {
                "title": title,
                "url": job.get("hostedUrl", ""),
                "source": "lever",
                "location": location,
                "work_mode": _infer_work_mode(title, location),
                "work_type": _normalize_work_type(work_type_raw),
                "experience": _infer_experience(title),
            }
            if match_job(j, prefs):
                jobs.append(j)
        return True, jobs
    except Exception as exc:
        logger.debug("Lever error for %s: %s", slug, exc)
        return False, []


async def _scrape_ashby(
    slug: str, client: httpx.AsyncClient, prefs: dict
) -> tuple[bool, list[dict]]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return False, []
        data = resp.json()
        jobs = []
        for job in data.get("jobPostings", []):
            title = job.get("title", "")
            location = job.get("location", "")
            is_remote = bool(job.get("isRemote", False))
            j = {
                "title": title,
                "url": job.get("jobUrl", ""),
                "source": "ashby",
                "location": location,
                "work_mode": _infer_work_mode(title, location, is_remote),
                "work_type": _normalize_work_type(job.get("employmentType", "")),
                "experience": _infer_experience(title),
            }
            if match_job(j, prefs):
                jobs.append(j)
        return True, jobs
    except Exception as exc:
        logger.debug("Ashby error for %s: %s", slug, exc)
        return False, []


# ---------- Direct multi-page scraper ----------

def _find_next_page(soup: BeautifulSoup, current_url: str) -> str | None:
    tag = soup.find("link", rel="next")
    if tag and tag.get("href"):
        return urljoin(current_url, tag["href"])

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        text = a.get_text(strip=True).lower()
        aria = (a.get("aria-label") or "").lower()
        rel_attr = " ".join(a.get("rel") or []).lower()
        if (
            text in ("next", "next page", "›", "»", ">")
            or "next" in aria
            or "next" in rel_attr
        ):
            return urljoin(current_url, href)

    return None


def _extract_page_jobs(
    soup: BeautifulSoup,
    base_url: str,
    page_url: str,
    seen: set[str],
    prefs: dict,
) -> list[dict]:
    jobs = []
    for tag in soup.find_all(["a", "li", "h2", "h3", "h4", "span", "div"]):
        text = tag.get_text(strip=True)
        if not text or len(text) > 200 or text in seen:
            continue

        href = tag.get("href", "") if tag.name == "a" else ""
        if not href:
            a = tag.find("a")
            href = a.get("href", "") if a else ""

        apply_url = urljoin(base_url, href) if href else page_url
        parent_text = (tag.parent.get_text(" ", strip=True) if tag.parent else "").lower()

        j = {
            "title": text,
            "url": apply_url,
            "source": "scraped",
            "location": "",
            "work_mode": _infer_work_mode(text, parent_text),
            "work_type": _normalize_work_type(parent_text),
            "experience": _infer_experience(text),
        }
        if match_job(j, prefs):
            seen.add(text)
            jobs.append(j)

    return jobs


async def _scrape_direct(
    company_url: str, client: httpx.AsyncClient, prefs: dict
) -> list[dict]:
    base_url = company_url.rstrip("/")
    paths = ["/careers", "/jobs", "/about/careers", "/work-with-us", "/careers/jobs"]

    for path in paths:
        all_jobs: list[dict] = []
        seen: set[str] = set()
        visited: set[str] = set()
        current: str | None = base_url + path
        page = 0

        while current and page < MAX_DIRECT_PAGES:
            if current in visited:
                break
            visited.add(current)
            try:
                resp = await client.get(current, timeout=15, follow_redirects=True)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "html.parser")
                all_jobs.extend(_extract_page_jobs(soup, base_url, current, seen, prefs))
                current = _find_next_page(soup, current)
                page += 1
            except Exception as exc:
                logger.debug("Direct page error %s: %s", current, exc)
                break

        if all_jobs:
            return all_jobs[:MAX_DIRECT_JOBS]

    return []


# ---------- Per-company orchestrator ----------

async def scrape_company(
    company_name: str,
    company_url: str,
    prefs: dict,
    log_callback=None,
) -> list[dict]:
    def log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    url_slug = extract_slug(company_url)
    name_slug = name_to_slug(company_name)
    slugs = list(dict.fromkeys([url_slug, name_slug]))

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        for slug in slugs:
            found, jobs = await _scrape_greenhouse(slug, client, prefs)
            if found:
                label = f"found {len(jobs)} role(s)" if jobs else "no matching roles"
                log(f"Checking {company_name}... {label} (Greenhouse)")
                return jobs

        for slug in slugs:
            found, jobs = await _scrape_lever(slug, client, prefs)
            if found:
                label = f"found {len(jobs)} role(s)" if jobs else "no matching roles"
                log(f"Checking {company_name}... {label} (Lever)")
                return jobs

        for slug in slugs:
            found, jobs = await _scrape_ashby(slug, client, prefs)
            if found:
                label = f"found {len(jobs)} role(s)" if jobs else "no matching roles"
                log(f"Checking {company_name}... {label} (Ashby)")
                return jobs

        jobs = await _scrape_direct(company_url, client, prefs)
        if jobs:
            log(f"Checking {company_name}... found {len(jobs)} role(s) (direct, multi-page)")
        else:
            log(f"Checking {company_name}... no matching roles found")
        return jobs


# ---------- Top-level runner ----------

async def run_scraper(companies, prefs: dict, log_callback=None) -> list[dict]:
    tasks = [scrape_company(c.name, c.url, prefs, log_callback) for c in companies]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: list[dict] = []
    for company, result in zip(companies, results):
        if isinstance(result, Exception):
            msg = f"Error scraping {company.name}: {result}"
            logger.error(msg)
            if log_callback:
                log_callback(msg)
        else:
            for job in result:
                all_jobs.append({"company_id": company.id, "company_name": company.name, **job})

    return all_jobs
