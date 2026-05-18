# PrepStack

> AI-powered mock interview and resume review platform — built entirely in Python.

PrepStack helps job seekers practice interviews with a realistic AI interviewer, get structured feedback on their resume, and walk into real interviews more confident. The project demonstrates end-to-end product engineering: a clean backend API, a lightweight frontend, and practical AI integration — all in a single Python codebase with zero external services required to run locally.

---

## Business context

The job market is competitive. Most candidates are rejected not because they lack the skills, but because they struggle to articulate them under pressure. Traditional preparation tools — static question banks, YouTube videos — offer no feedback loop.

PrepStack closes that gap by simulating the full interview experience: an AI persona asks contextually relevant questions, listens to your answers, pushes back when needed, and then produces a scored debrief with concrete coaching notes. The resume module complements this by reviewing uploaded CVs against role expectations and guiding candidates through targeted improvements — one suggestion at a time.

The core value proposition is **deliberate practice with instant, specific feedback** — the same loop that separates average candidates from strong ones.

---

## What it does

| Capability | Detail |
|---|---|
| **Mock interviews** | Choose an AI persona, interview mode, and duration. The AI conducts a realistic session, asks follow-ups, and scores you at the end. |
| **Resume review** | Upload a PDF. The AI identifies weak points and walks you through a structured improvement wizard. |
| **Voice I/O** | Speak your answers via the browser mic. Hear the AI's questions read aloud — no extra cost, uses the browser's built-in speech engine. |
| **Scorecard** | Post-interview report with per-competency scores, observed strengths, gaps, and a coaching plan. |
| **No login required** | Designed as a demo/portfolio tool — works out of the box without creating an account. |

---

## AI personas

| Persona | Style |
|---|---|
| **Alex** | Professional and neutral — simulates a FAANG-style recruiter screen |
| **Tough Love Terry** | Blunt and demanding — designed to stress-test your answers |
| **Friendly Frankie** | Warm and encouraging — good for first-time practice |
| **The Panel** | Three interviewers rotating across Hiring Manager, Tech Lead, and HR perspectives |

## Interview modes

| Mode | Format |
|---|---|
| **Behavioral** | STAR-method, competency-based questions |
| **Technical** | Problem-solving and role-specific knowledge |
| **Case Study** | Consulting-style structured analysis |
| **Stress Test** | Rapid-fire, intentionally challenging |

---

## Technical highlights

Built as a portfolio project to demonstrate:

- **FastAPI** — async REST API with streaming responses (Server-Sent Events for live AI output)
- **SQLAlchemy (async)** — ORM with SQLite for zero-setup local storage; swap the connection string for PostgreSQL in production
- **NVIDIA NIM API** — large language model integration via the OpenAI-compatible SDK; different models are selected per interview phase (start, respond, score) to balance cost and quality
- **pypdf** — PDF text extraction for resume parsing
- **Jinja2 + vanilla JS** — lightweight server-rendered frontend; no framework dependencies
- **Browser Speech APIs** — `SpeechRecognition` for voice input, `speechSynthesis` for voice output; free, no third-party key needed
- **Pydantic v2** — request/response validation and internal data modelling throughout

---

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Database | SQLAlchemy (async) + SQLite (aiosqlite) |
| AI | NVIDIA NIM API via OpenAI Python SDK |
| PDF parsing | pypdf |
| Frontend | Jinja2 templates + vanilla HTML/CSS/JS |
| Voice I/O | Browser Web Speech API (free, no key) |
| Data validation | Pydantic v2 |

---

## Project layout

```
prepstack/
├── main.py                  # FastAPI app, startup, static file serving
├── database.py              # SQLAlchemy async engine + session factory
├── models.py                # ORM models: Resume, InterviewSession
├── auth.py                  # No-auth stub (fixed demo user)
├── requirements.txt
├── .env.example
├── lib/
│   ├── types.py             # Pydantic domain models
│   ├── constants.py         # Personas, interview modes
│   ├── prompts.py           # AI prompt builders
│   ├── resume_review.py     # Resume review logic
│   └── interview_models.py  # Per-phase model selection
├── routers/
│   ├── interview.py         # /api/interview — start, respond (streaming), end
│   ├── resume.py            # /api/resume — upload, review, wizard, delete
│   ├── tts.py               # /api/tts — ElevenLabs (optional upgrade)
│   └── pages.py             # HTML page routes (Jinja2)
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS
└── uploads/                 # Uploaded PDFs (local disk, git-ignored)
```

---

## Quick start

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd prepstack

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your **NVIDIA API key** — that's the only required value:

```
NVIDIA_API_KEY=your-nvidia-api-key
```

Everything else (TTS, email, database path) is optional.

### 3. Run

```bash
uvicorn main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000). The SQLite database is created automatically on first run — no migration step needed.

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## API reference

Interactive docs at `http://localhost:8000/docs`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/interview/start` | Create a new interview session |
| POST | `/api/interview/respond` | Stream the AI's next reply |
| POST | `/api/interview/end` | Score the session, persist transcript |
| POST | `/api/resume/upload` | Upload a PDF resume |
| POST | `/api/resume/review` | AI review — returns structured feedback |
| POST | `/api/resume/review/question` | Ask a follow-up on a suggestion |
| POST | `/api/resume/review/agree` | Accept a suggestion |
| POST | `/api/resume/review/skip` | Skip a suggestion |
| POST | `/api/resume/activate` | Set the active resume for interviews |
| DELETE | `/api/resume/{id}` | Delete a resume |
| GET | `/api/health` | Health check |

---

## Environment variables

**Required**

| Variable | Description |
|---|---|
| `NVIDIA_API_KEY` | NVIDIA NIM API key for all AI features |

**Optional**

| Variable | Description |
|---|---|
| `ELEVENLABS_API_KEY` | Upgrade TTS from browser voices to ElevenLabs |
| `RESEND_API_KEY` | Email delivery |
| `RESEND_FROM_EMAIL` | Sender address |
| `DATABASE_URL` | Override database path (defaults to `./prepstack.db`) |
| `INTERVIEW_START_MODEL` | AI model for session opening |
| `INTERVIEW_RESPOND_MODEL` | AI model for mid-session replies |
| `INTERVIEW_END_MODEL` | AI model for scorecard generation |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `APP_URL` | Base URL for email links |
