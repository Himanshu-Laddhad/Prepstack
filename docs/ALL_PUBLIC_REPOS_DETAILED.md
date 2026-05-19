# Himanshu-Laddhad — Public Repositories (Detailed Technical & Product Overview)

> Generated on 2026-05-19.
>
> Location: `docs/ALL_PUBLIC_REPOS_DETAILED.md`
>
> Scope: All public repositories under `Himanshu-Laddhad`.
>
> Method: Each repo section is written by inspecting that repository’s README + key project files (entrypoints, dependency manifests, and core modules) when available.

---

## Table of contents

- [Prepstack](#repo-prepstack-himanshu-laddhadprepstack)

---

## Repo: Prepstack (`Himanshu-Laddhad/Prepstack`)

- Repo URL: https://github.com/Himanshu-Laddhad/Prepstack

### What it is (high-level)
**PrepStack** is an AI-powered mock interview and resume review web app built entirely in **Python**. It’s designed as a practical, demo-friendly platform that simulates a realistic interview loop (including follow-ups), supports multiple interviewer “personas” and interview “modes,” and generates post-session scorecards and coaching plans.

In addition, it provides a resume review workflow: users upload a resume PDF, the app extracts text, generates structured feedback and improvement suggestions, and drives a step-by-step “wizard” where users can ask follow-up questions and accept/skip recommendations.

### Links
- Live site (from README): https://prepstack.ryg.lol/
- Medium article (from README): https://h11laddhad.medium.com/why-i-used-three-different-llms-to-build-one-interview-coach-11131ca489d6

### Core capabilities (user-facing)
From the repo README:

- **Mock interviews**
  - Choose an AI persona, interview mode, and duration.
  - The AI conducts the interview, asks follow-ups, and scores you at the end.
- **Resume review**
  - Upload a PDF and get structured feedback.
  - A guided improvement wizard supports iterative refinement.
- **Voice I/O**
  - Uses the browser’s built-in Web Speech APIs for voice input and voice output (free, no extra vendor key required).
- **Scorecard**
  - Post-interview report with per-competency scores, strengths, gaps, and coaching plan.
- **No login required**
  - Designed to be frictionless for demo/portfolio usage.

### Personas & interview modes
Personas (README):
- **Alex** — professional / neutral
- **Tough Love Terry** — blunt / demanding
- **Friendly Frankie** — warm / encouraging
- **The Panel** — rotating perspectives (Hiring Manager / Tech Lead / HR)

Interview modes (README):
- Behavioral (STAR)
- Technical
- Case Study
- Stress Test

### Architecture & major components

#### Backend framework + routing
- The backend is a **FastAPI** app (`main.py`).
- It mounts:
  - `/static` for CSS/assets
  - `/uploads` for uploaded PDFs (local filesystem directory created at runtime)
- It wires routers:
  - `routers/interview.py` (under `/api/interview/*`)
  - `routers/resume.py` (under `/api/resume/*`)
  - `routers/tts.py` (under `/api/tts`)
  - `routers/pages.py` (HTML routes)

Startup behavior:
- On FastAPI startup, the app auto-creates DB tables via SQLAlchemy metadata (`Base.metadata.create_all`).

CORS:
- Configurable via `ALLOWED_ORIGINS` environment variable.

#### Persistence layer
- Uses **SQLAlchemy 2.x** in async mode + **SQLite** via `aiosqlite`.
- The app is designed to be zero-setup locally: DB file is created automatically on first run.
- It can be swapped to another DB (e.g., Postgres) by setting `DATABASE_URL`.

#### LLM integration strategy (multi-model by phase)
- Uses **NVIDIA NIM API** through the **OpenAI Python SDK** (OpenAI-compatible client).
- Different models can be chosen per interview phase:
  - `INTERVIEW_START_MODEL`
  - `INTERVIEW_RESPOND_MODEL`
  - `INTERVIEW_END_MODEL`

Default values are shown in `.env.example`:
- `nvidia/nemotron-mini-4b-instruct` (start)
- `mistralai/mistral-small-4-119b-2603` (respond)
- `meta/llama-3.3-70b-instruct` (end)

This supports a key product goal: balance **cost/latency** vs **quality** by choosing different models for different phases.

#### Resume review workflow (structured feedback + wizard)
The resume review subsystem includes logic to:
- Parse extracted resume text into sections (summary/experience/education/skills/projects) using heading detection.
- Normalize AI responses into strict typed objects (scores, score breakdowns, suggestions, section feedback).
- Maintain a “suggestion log” with status and message threads, enabling iterative follow-up conversation.

A key module is `lib/resume_review.py`, which includes:
- `build_resume_sections(...)` to generate structured section blocks from raw text.
- `normalize_resume_review(...)` to coerce/validate LLM outputs into domain models.
- Helpers for managing suggestion logs: build initial log, upsert entries, etc.

#### Frontend approach
- Server-rendered pages with **Jinja2** templates + vanilla HTML/CSS/JS.
- Voice features are implemented with browser Web Speech APIs (free).
- Optional TTS upgrade via **ElevenLabs** (configured through env vars).

### Dependency stack (from `requirements.txt`)
- fastapi
- uvicorn
- jinja2
- sqlalchemy
- aiosqlite
- python-dotenv
- pydantic
- openai
- httpx
- python-multipart
- pypdf
- resend

### API surface (from README)
Interactive docs: `http://localhost:8000/docs`

Interview:
- `POST /api/interview/start`
- `POST /api/interview/respond` (streaming AI reply)
- `POST /api/interview/end` (score + persist transcript)

Resume:
- `POST /api/resume/upload`
- `POST /api/resume/review`
- `POST /api/resume/review/question`
- `POST /api/resume/review/agree`
- `POST /api/resume/review/skip`
- `POST /api/resume/activate`
- `DELETE /api/resume/{id}`

Other:
- `GET /api/health`

### Environment configuration (from README / `.env.example`)
Required:
- `NVIDIA_API_KEY`

Optional:
- Model overrides: `INTERVIEW_START_MODEL`, `INTERVIEW_RESPOND_MODEL`, `INTERVIEW_END_MODEL`
- ElevenLabs: `ELEVENLABS_API_KEY` + voice IDs
- Resend email: `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `APP_URL`
- DB override: `DATABASE_URL`
- CORS: `ALLOWED_ORIGINS`

### How to run locally (from README)
1. Create venv + install deps: `pip install -r requirements.txt`
2. `cp .env.example .env` and set `NVIDIA_API_KEY`
3. Start: `uvicorn main:app --reload --port 8000`
4. Open: `http://localhost:8000`

---

## Notes / Next repos
This document will be expanded repo-by-repo by inspecting each repository’s README and key source files.
