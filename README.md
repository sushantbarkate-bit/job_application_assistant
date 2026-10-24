# AI Job Application Assistant

An approval-first Python starter project for discovering jobs, scoring fit, tailoring resume text, preparing application forms, and producing daily reports.

## What is included

- **Job discovery:** offline demo provider with sample jobs; add a real provider only through official APIs, feeds, or permitted portal workflows.
- **Job matching:** transparent deterministic score using target titles, skills, and locations.
- **AI resume tailoring:** OpenAI-backed helper that is instructed not to invent experience. User must verify suggested edits.
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

Set `OPENAI_API_KEY` in `.env` if you want AI resume tailoring. Matching and demo discovery work without an API key.

## Configure

Edit `config.yaml` with your real profile and target roles. Add your base resume at the configured `resume_path` (default `resume/base_resume.docx`). Keep profile facts truthful. Do not store passwords, OTPs, government IDs, or sensitive account credentials in this project.

Before using browser form filling, add only a domain you have checked and are allowed to automate to `workflow.allowed_domains`. The helper refuses all other domains.

## Run

```bash
# Discover sample jobs and score them
python -m job_assistant.cli discover

# Export today's report
python -m job_assistant.cli report

# Mark a discovered job approved for review (does not submit)
python -m job_assistant.cli approve --job-id demo-001
```

The daily CSV is saved under `reports/`. Application state is stored in `data/applications.sqlite3`.

## Integrating live job discovery

Implement a provider in `job_assistant/providers.py` that returns `Job` objects. Use official job APIs, RSS/Atom feeds, or sources that explicitly permit automated access. Do not bypass CAPTCHAs, login restrictions, rate limits, or anti-bot controls. Avoid automated mass applications; honor portal terms and daily limits.

## Current limitations

- Demo provider is not live and uses fictional sample jobs.
- The baseline matcher is deterministic; the OpenAI helper is an optional resume-tailoring utility, not yet wired into an automatic pipeline.
- Application form fields vary by site. The Playwright helper uses conservative label/name matching and does not submit. Review every answer and the live form yourself.
- No credentials or session cookies are managed by this project.

## Safety checklist

1. Confirm the job and employer are legitimate.
2. Verify resume changes and every application answer.
3. Never let AI guess work authorization, salary history, notice period, or other personal facts.
4. Keep final submission manual unless the portal expressly permits automation and you have reviewed the application.
5. Do not share your account password, OTP, or session cookie with an AI service.
