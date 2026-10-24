# AI Job Application Assistant

An approval-first Python starter project for discovering jobs, scoring fit, tailoring resume text, preparing application forms, and producing daily reports.

## What is included

- **Job discovery:** offline demo provider with clearly labelled sample jobs; optional live discovery through configured public Greenhouse job boards.
- **Job matching:** transparent deterministic score using target titles, skills, and locations.
- **AI resume tailoring:** `tailor --job-id` drafts a tailored resume with OpenAI. It is instructed not to invent experience, and you must verify suggested edits.
- **AI cover letters:** `cover-letter --job-id` drafts a short cover letter from your resume and the job description.
- **Resume handling:** reads DOCX and saves tailored DOCX.
- **Form filling:** optional Playwright helper, restricted to explicitly allowlisted domains. It fills fields and can attach a resume, but never clicks Submit/Apply.
- **Approval:** `approve --job-id` marks a job approved for review; final submission remains manual.
- **Daily report:** CSV export of today's recorded matches/statuses.

## Requirements

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` only if you want to use the `tailor` and `cover-letter` commands. Never commit or share `.env`. Matching and demo discovery work without an API key. API usage may incur separate charges.

## Configure

Edit `config.yaml` with your real profile and target roles. Add your base resume at the configured `resume_path` (default `resume/Sushant_Barkate_Resume.docx`). Relative paths in `config.yaml` are resolved from the project folder, so commands work from any directory. Keep profile facts truthful. Do not store passwords, OTPs, government IDs, or sensitive account credentials in this project.

Before using browser form filling, add only a domain you have checked and are allowed to automate to `workflow.allowed_domains`. The helper refuses all other domains.

## Verify the installation

```bash
python -m unittest discover -s tests -v
```

## Run

```bash
# Discover sample jobs and score them (works offline)
python -m job_assistant.cli discover

# Search configured public Greenhouse boards instead
python -m job_assistant.cli discover --provider greenhouse

# Print LinkedIn and Naukri search links for the enabled sources
python -m job_assistant.cli links

# Export today's report (jobs found or status-changed today)
python -m job_assistant.cli report

# Discover, print links, and export the report in one step
python -m job_assistant.cli daily

# Mark a discovered job approved for review (does not submit)
python -m job_assistant.cli approve --job-id demo-001

# Draft a tailored resume (needs OPENAI_API_KEY); saved under output/tailored-resumes/
python -m job_assistant.cli tailor --job-id greenhouse-gitlab-8826920002

# Draft a cover letter (needs OPENAI_API_KEY); saved under output/cover-letters/
python -m job_assistant.cli cover-letter --job-id greenhouse-gitlab-8826920002
```

The daily CSV is saved under `reports/`. Application state is stored in `data/applications.sqlite3`. AI drafts are saved under `output/`, which is git-ignored because it contains personal data.

### Daily runs on Windows

`daily` runs once and exits. To run it every morning, create a Task Scheduler entry that changes into the project folder first, so the config and database are found:

```powershell
schtasks /Create /SC DAILY /ST 09:00 /TN "JobAssistantDaily" /TR "cmd /c cd /d \"C:\path\to\job_application_assistant\" && .venv\Scripts\python.exe -m job_assistant.cli daily"
```

The command inside the task was tested from the project folder. The `schtasks` line itself has not been run, so check the task in Task Scheduler after creating it.

Set `search.provider: greenhouse` first if you want live results.

## Live job discovery

The default provider is `demo`, so the project runs without internet access and does not pretend sample jobs are real vacancies. For live results, set `search.provider: greenhouse` in `config.yaml` or run `python -m job_assistant.cli discover --provider greenhouse`. Configure valid public Greenhouse board tokens under `search.greenhouse_board_tokens`. This searches only those employers' public boards; it is not a general internet job search. You can add providers using official job APIs, RSS/Atom feeds, or sources that explicitly permit automated access. Do not bypass CAPTCHAs, login restrictions, rate limits, or anti-bot controls. Avoid automated mass applications; honor portal terms and daily limits.

## Current limitations

- Demo provider is not live and uses fictional sample jobs.
- LinkedIn and Naukri are link-only. The project builds search URLs but does not fetch their listings, because neither offers a public job-listing API for this use and scraping them breaks their terms.
- Automatic applications are not implemented, by design. Approval records intent; you submit each application yourself.
- The baseline matcher is deterministic. Skill matches are whole words, and "Engineer" and "Developer" are treated as the same title.
- The OpenAI commands need a funded OpenAI account. Without credit they report the quota error and write nothing.
- The Playwright form helper (`job_assistant/apply.py`) is not connected to any command.
- Application form fields vary by site. The Playwright helper uses conservative label/name matching and does not submit. Review every answer and the live form yourself.
- No credentials or session cookies are managed by this project.

## Safety checklist

1. Confirm the job and employer are legitimate.
2. Verify resume changes and every application answer.
3. Never let AI guess work authorization, salary history, notice period, or other personal facts.
4. Keep final submission manual unless the portal expressly permits automation and you have reviewed the application.
5. Do not share your account password, OTP, or session cookie with an AI service.
