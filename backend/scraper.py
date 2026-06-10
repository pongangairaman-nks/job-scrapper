import asyncio
import logging
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

KEYWORDS = [
    "frontend developer",
    "frontend engineer",
    "ui engineer",
    "ux engineer",
    "senior frontend",
    "react developer",
    "react engineer",
    "javascript developer",
    "javascript engineer",
    "next.js developer",
    "vue developer",
    "angular developer",
    "web developer",
    "ui developer",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0; +https://github.com/job-scraper)"
}


def match_keywords(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in KEYWORDS)


def extract_slug(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or url
    domain = domain.replace("www.", "")
    return domain.split(".")[0].lower()


def name_to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def _scrape_greenhouse(slug: str, client: httpx.AsyncClient) -> tuple[bool, list[dict]]:
    """Returns (ats_found, matching_jobs)."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return False, []
        data = resp.json()
        jobs = []
        for job in data.get("jobs", []):
            title = job.get("title", "")
            if match_keywords(title):
                jobs.append(
                    {"title": title, "url": job.get("absolute_url", ""), "source": "greenhouse"}
                )
        return True, jobs
    except Exception as exc:
        logger.debug("Greenhouse error for %s: %s", slug, exc)
        return False, []


async def _scrape_lever(slug: str, client: httpx.AsyncClient) -> tuple[bool, list[dict]]:
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
            title = job.get("text", "")
            if not isinstance(title, str):
                title = ""
            apply_url = job.get("hostedUrl", "")
            if match_keywords(title):
                jobs.append({"title": title, "url": apply_url, "source": "lever"})
        return True, jobs
    except Exception as exc:
        logger.debug("Lever error for %s: %s", slug, exc)
        return False, []


async def _scrape_ashby(slug: str, client: httpx.AsyncClient) -> tuple[bool, list[dict]]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code != 200:
            return False, []
        data = resp.json()
        jobs = []
        for job in data.get("jobPostings", []):
            title = job.get("title", "")
            apply_url = job.get("jobUrl", "")
            if match_keywords(title):
                jobs.append({"title": title, "url": apply_url, "source": "ashby"})
        return True, jobs
    except Exception as exc:
        logger.debug("Ashby error for %s: %s", slug, exc)
        return False, []


async def _scrape_direct(company_url: str, client: httpx.AsyncClient) -> list[dict]:
    base_url = company_url.rstrip("/")
    career_paths = ["/careers", "/jobs", "/about/careers", "/work-with-us", "/careers/jobs"]

    for path in career_paths:
        target = base_url + path
        try:
            resp = await client.get(target, timeout=15, follow_redirects=True)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []
            seen_titles: set[str] = set()

            for tag in soup.find_all(["a", "li", "h2", "h3", "h4", "span", "div"]):
                text = tag.get_text(strip=True)
                if not match_keywords(text) or len(text) > 200 or text in seen_titles:
                    continue

                href = tag.get("href", "") if tag.name == "a" else ""
                if not href:
                    link_tag = tag.find("a")
                    href = link_tag.get("href", "") if link_tag else ""

                if href and not href.startswith("http"):
                    href = base_url + href

                seen_titles.add(text)
                jobs.append({"title": text, "url": href or target, "source": "scraped"})

            if jobs:
                return jobs[:20]

        except Exception as exc:
            logger.debug("Direct scrape error for %s: %s", target, exc)

    return []


async def scrape_company(
    company_name: str,
    company_url: str,
    log_callback=None,
) -> list[dict]:
    def log(msg: str):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    url_slug = extract_slug(company_url)
    name_slug = name_to_slug(company_name)
    # Try URL-derived slug first, then name-derived (deduped, order preserved)
    slugs = list(dict.fromkeys([url_slug, name_slug]))

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # --- Greenhouse ---
        for slug in slugs:
            found, jobs = await _scrape_greenhouse(slug, client)
            if found:
                if jobs:
                    log(f"Checking {company_name}... found {len(jobs)} role(s) (Greenhouse)")
                else:
                    log(f"Checking {company_name}... no frontend roles (Greenhouse)")
                return jobs

        # --- Lever ---
        for slug in slugs:
            found, jobs = await _scrape_lever(slug, client)
            if found:
                if jobs:
                    log(f"Checking {company_name}... found {len(jobs)} role(s) (Lever)")
                else:
                    log(f"Checking {company_name}... no frontend roles (Lever)")
                return jobs

        # --- Ashby ---
        for slug in slugs:
            found, jobs = await _scrape_ashby(slug, client)
            if found:
                if jobs:
                    log(f"Checking {company_name}... found {len(jobs)} role(s) (Ashby)")
                else:
                    log(f"Checking {company_name}... no frontend roles (Ashby)")
                return jobs

        # --- Direct scrape fallback ---
        jobs = await _scrape_direct(company_url, client)
        if jobs:
            log(f"Checking {company_name}... found {len(jobs)} role(s) (direct scrape)")
        else:
            log(f"Checking {company_name}... no frontend roles found")
        return jobs


async def run_scraper(companies, log_callback=None) -> list[dict]:
    tasks = [scrape_company(c.name, c.url, log_callback) for c in companies]
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
                all_jobs.append(
                    {
                        "company_id": company.id,
                        "company_name": company.name,
                        **job,
                    }
                )

    return all_jobs
