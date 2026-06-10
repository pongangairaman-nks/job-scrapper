# Frontend Job Scraper

Automated tool that checks Greenhouse, Lever, and Ashby ATS boards (plus direct scraping as a fallback) for frontend engineering roles across your chosen companies. Runs daily via GitHub Actions and emails you a digest.

---

## Quick Start

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd job-scraper
```

### 2. Backend setup
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Open .env and fill in GMAIL_SENDER and GMAIL_APP_PASSWORD
```

### 4. Start the backend
```bash
uvicorn main:app --reload
# API runs at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 5. Frontend setup (separate terminal)
```bash
cd frontend
npm install
npm run dev
# UI runs at http://localhost:5173
```

---

## Getting a Gmail App Password

Regular Gmail passwords won't work — you need a 16-character **App Password**.

1. Sign in to your Google account at [myaccount.google.com](https://myaccount.google.com)
2. Go to **Security** → **2-Step Verification** (must be enabled)
3. Scroll down to **App passwords**
4. Click **Select app** → choose **Mail**
5. Click **Select device** → choose **Other (custom name)** → type `Job Scraper`
6. Click **Generate**
7. Copy the 16-character password (shown once) into your `.env` as `GMAIL_APP_PASSWORD`

---

## GitHub Actions Setup (daily automation)

### Add repository secrets

1. Go to your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:
   - `GMAIL_SENDER` — your Gmail address
   - `GMAIL_APP_PASSWORD` — the 16-character App Password from above

The workflow triggers automatically at **9:00 AM IST (3:30 AM UTC)** every day.

### Trigger a manual run

1. Go to your repo → **Actions** tab
2. Click **Daily Job Scraper** in the left sidebar
3. Click **Run workflow** → **Run workflow** (green button)
4. Watch the live logs to confirm it worked

---

## How it works

```
For each company, try in order:
  1. Greenhouse API  → https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
  2. Lever API       → https://api.lever.co/v0/postings/{slug}?mode=json
  3. Ashby API       → https://api.ashbyhq.com/posting-api/job-board/{slug}
  4. Direct scrape   → /careers, /jobs, /about/careers, /work-with-us

If an ATS responds (200 OK), use that result even if no jobs match.
Only fall through to the next source if the ATS isn't found (404/error).
```

Matched job titles are filtered by these keywords (case-insensitive, partial match):

- frontend developer / engineer
- ui engineer / ux engineer
- senior frontend
- react developer / engineer
- javascript developer / engineer
- next.js developer
- vue developer / angular developer
- web developer / ui developer

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/companies` | List all companies |
| POST | `/companies` | Add a company `{ name, url }` |
| DELETE | `/companies/{id}` | Remove a company |
| POST | `/scrape` | Trigger scrape, returns new jobs |
| GET | `/jobs` | All jobs from DB (newest first) |
| POST | `/send-email` | Send digest of un-emailed jobs |
| GET | `/status` | Scraper state + live log |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
job-scraper/
├── backend/
│   ├── main.py          # FastAPI app + headless entry point
│   ├── scraper.py       # ATS API + direct scraping logic
│   ├── email_sender.py  # Gmail SMTP digest
│   ├── database.py      # SQLAlchemy engine + session
│   ├── models.py        # Company + Job ORM models
│   ├── requirements.txt
│   └── companies.json   # Starter companies (seeded on first run)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── Controls.jsx    # Scrape + email buttons
│   │       ├── CompanyList.jsx # Add/remove companies
│   │       ├── JobsTable.jsx   # Searchable jobs table
│   │       └── StatusLog.jsx   # Live scraper log
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── .github/workflows/
│   └── daily_scraper.yml
├── .env.example
└── .gitignore
```
