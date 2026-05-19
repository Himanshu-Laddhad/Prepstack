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
- [Bankcheck](#repo-bankcheck-himanshu-laddhadbankcheck)
- [Conversational-LLM-Mapping-Agent](#repo-conversational-llm-mapping-agent-himanshu-laddhadconversational-llm-mapping-agent)
- [Multi-agent-analytics](#repo-multi-agent-analytics-himanshu-laddhadmulti-agent-analytics)
- [bankruptcy-prediction-ensemble](#repo-bankruptcy-prediction-ensemble-himanshu-laddhadbankruptcy-prediction-ensemble)
- [Customer-analytics-ml-pipeline](#repo-customer-analytics-ml-pipeline-himanshu-laddhadcustomer-analytics-ml-pipeline)
- [marketing-churn-ml-pipeline](#repo-marketing-churn-ml-pipeline-himanshu-laddhadmarketing-churn-ml-pipeline)
- [mlb-salary-prediction](#repo-mlb-salary-prediction-himanshu-laddhadmlb-salary-prediction)
- [telecom-churn-eda](#repo-telecom-churn-eda-himanshu-laddhadtelecom-churn-eda)
- [Walmart-demand-forecasting](#repo-walmart-demand-forecasting-himanshu-laddhadwalmart-demand-forecasting)
- [price-elasticity-and-optimal-pricing](#repo-price-elasticity-and-optimal-pricing-himanshu-laddhadprice-elasticity-and-optimal-pricing)
- [retail-brand-pricing-analysis](#repo-retail-brand-pricing-analysis-himanshu-laddhadretail-brand-pricing-analysis)
- [yelp-review-nlp-topic-modeling](#repo-yelp-review-nlp-topic-modeling-himanshu-laddhadyelp-review-nlp-topic-modeling)
- [Retail-trend-intelligence-platform](#repo-retail-trend-intelligence-platform-himanshu-laddhadretail-trend-intelligence-platform)

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

## Repo: Bankcheck (`Himanshu-Laddhad/Bankcheck`)

- Repo URL: https://github.com/Himanshu-Laddhad/Bankcheck

### What it is (high-level)
**BankCheck** is a Streamlit dashboard that compares U.S. banks and credit unions using **free, official government/public datasets** — designed explicitly to avoid affiliate-link incentives and sponsored rankings. It aggregates rate intelligence, complaint patterns, mortgage/lending performance, and safety/financial health signals.

### Core product concept
The app builds a **multi-source, cross-domain comparison layer** and turns it into:
- interactive dashboards (rate/complaints/mortgage/safety)
- quick-pick recommendations (best savings, best mortgage, best credit card)
- a short “bank matcher” quiz
- a savings calculator to show real dollar impact

### Main UI/pages and what each answers
From the README:

- **Overview**: fast “what should I do?” page (quick picks, quiz, calculator, live rankings, scorecards)
- **Rate Intelligence**: savings APY and other rates vs benchmarks, pass-through behavior, rate charts
- **Complaint Intelligence**: CFPB complaint trends, heatmaps, resolution rates
- **Mortgage & Lending**: HMDA-driven approval rates, denial reasons, rate comparisons
- **Safety & Scores**: FDIC capital ratios and a composite score/grade approach

### Composite scoring (A–F)
The repo defines a composite score using weighted dimensions:

```
Overall Score = Rate Score (35%) + Complaint Score (35%) + Safety Score (20%) + Fairness Score (10%)
```

- **Rate Score**: FDIC / FRED benchmark comparisons
- **Complaint Score**: CFPB complaint volume + % resolved with monetary relief
- **Safety Score**: FDIC Tier 1 capital ratio vs minimums
- **Fairness Score**: HMDA mortgage approval rate

### Data sources & refresh model
- FDIC BankFind (keyless)
- CFPB Complaints (keyless)
- FRED (API key optional; keyless fallback uses published national averages noted in README)
- HMDA (annual)
- NCUA (quarterly)

### Engineering architecture
**Streamlit entry + orchestration**
- `main.py` is the Streamlit entrypoint, sets theme/CSS, renders sidebar controls, and orchestrates a multi-source data pipeline.
- The pipeline is cached with `@st.cache_data(ttl=3600)` to keep repeat usage fast.

**Connectors per source**
- `connectors/` contains one connector module per data provider. The repo uses retry logic (Tenacity) and health checks.

**Processing layer**
- `processing/normalizer.py`: canonicalizes institution naming across FDIC/CFPB/HMDA/NCUA.
- `processing/aggregator.py`: per-bank rate records (savings/CD/credit card APR), plus curated rate tables.
- `processing/scorer.py`: composite scoring engine.

**Visualization & UI system**
- `analytics/`: chart builders by theme.
- `ui/`: shared UI components, engagement widgets, chart helpers, and per-page renderers.

### Configuration (.env)
Optional `.env` values include:
- `FRED_API_KEY` (optional)
- caching/logging settings

### How to run
- `pip install -r requirements.txt`
- optional: copy `.env.example` → `.env` and set `FRED_API_KEY`
- `streamlit run main.py`

---

## Repo: Conversational-LLM-Mapping-Agent (`Himanshu-Laddhad/Conversational-LLM-Mapping-Agent`)

- Repo URL: https://github.com/Himanshu-Laddhad/Conversational-LLM-Mapping-Agent

### What it is (high-level)
A production-grade Streamlit conversational agent for working with **XSLT/EDI mapping artifacts** in plain English. It is designed to reduce turnaround time for mapping changes by allowing non-specialists to:
- **explain** mappings
- **simulate** mappings against real input files
- **modify** mappings safely (with diff + verification)
- **audit** mappings with a structured checklist
- **generate** new mappings

The project positions itself as an “industry project” (PartnerLinQ / Purdue practicum) with explicit attention to change-management and safety.

### Key differentiator: real execution + verified edits
Unlike “describe what this code does” tools, this agent is engineered to:
- run real XSLT execution via **Saxon-HE (SaxonC via `saxonche`)**
- fall back to **lxml** when appropriate
- enforce an “all-or-nothing” patch apply policy with post-apply verification and well-formedness checks

### Architecture (as described in README)
High-level flow:
1. Out-of-scope guardrail (avoid using tokens on irrelevant prompts)
2. Intent classification (fast cheap classifier; described as Groq LLaMA router)
3. Optional RAG context injection (ChromaDB top-k retrieval)
4. Dispatch to specialized engine: explain/modify/simulate/audit/generate

### Provider/model configuration (.env)
The `.env.example` supports multiple providers (OpenAI, Groq, NVIDIA NIM, Anthropic) with per-engine overrides:
- `EXPLAIN_MODEL`, `MODIFY_MODEL`, `SIMULATE_MODEL`, `AUDIT_MODEL`, `GENERATE_MODEL`
- intent router model + confidence threshold

### Core modules
`modules/__init__.py` describes the core building blocks:
- unified multi-provider LLM client (`llm_client`)
- file ingestion and type handling
- intent routing
- per-intent engines (explain/simulate/modify/generate/audit)
- multi-file RAG engine (`index_folder`, `query_folder`)
- session memory + dispatcher

### Approval + rollback workflow (change management)
The repo includes an explicit approval layer (`approval_gate.py`) connecting UI actions to a persistent SQLite-backed store (rules/audit log). This supports:
- actor-stamped approvals
- audit logging of approve/reject events
- rollbacks to previous approved versions

### Dependencies (high-level)
From `requirements.txt` (abridged):
- Streamlit
- Groq SDK
- python-dotenv
- lxml + saxonche (XSLT execution)
- chromadb + sentence-transformers (local vector store + embeddings)
- pydifact (EDI parsing)

### How to run
- `pip install -r requirements.txt`
- copy `.env.example` → `.env` and set provider keys
- `streamlit run app.py`

---

## Repo: Multi-agent-analytics (`Himanshu-Laddhad/Multi-agent-analytics`)

- Repo URL: https://github.com/Himanshu-Laddhad/Multi-agent-analytics

### What it is (high-level)
**Agentic Analytics** is a Streamlit app that answers natural-language questions about tabular data using a multi-agent pipeline that:
- plans an analysis
- generates Python code
- executes it in a controlled sandbox
- returns artifacts (charts/files) plus a narrative explanation

It explicitly does **not** use NL-to-SQL as the primary architecture; it uses NL → plan → code → execution.

### Supported data sources
From README:
- CSV
- PostgreSQL
- URL-loaded datasets

### Multi-agent pipeline
From README “Features” / “Project Structure”, the pipeline includes:
- query decomposition
- planning
- code generation
- execution
- error feedback loop
- conclusion generation
- schema agent (schema summarization)

### Observability and persistence
- Conversation context persisted per chat in markdown context logs.
- Outputs saved under `outputs/{chat_id}`.
- SQLite storage via SQLAlchemy ORM; migrations via Alembic.

### Repo structure (from README)
Key directories:
- `app/`: Streamlit entrypoint + UI
- `agents/`: the multi-agent pipeline implementation
- `services/`: LLM client, sandbox, context manager, data loader, db service
- `models/`: pydantic schemas + db models
- `config/`: settings + version
- `tests/`: unit tests

### Config (.env.example)
Key settings include:
- `GOOGLE_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_CODE_MODEL`
- SQLite db path + optional Postgres DSN
- safety limits (row caps, timeouts, conversation window)

### Dependencies
From `requirements.txt`:
- Streamlit
- `google-genai`
- SQLAlchemy + Alembic + psycopg2
- pandas/numpy/httpx/seaborn
- plotly + kaleido (artifact export)
- pydantic + pydantic-settings
- python-dotenv

### How to run
- `pip install -r requirements.txt`
- set `.env` with `GOOGLE_API_KEY`
- `streamlit run app/main.py`

---

## Repo: bankruptcy-prediction-ensemble (`Himanshu-Laddhad/bankruptcy-prediction-ensemble`)

- Repo URL: https://github.com/Himanshu-Laddhad/bankruptcy-prediction-ensemble

### What it is (high-level)
A binary classification ML pipeline predicting bankruptcy from 64 anonymized financial ratios. The project emphasizes:
- **leak-free cross-validation**
- **missingness indicators** as signal
- gradient boosting model benchmarking + **Optuna** hyperparameter tuning
- ensembling across XGBoost/LightGBM/CatBoost

### Pipeline design
From README:
- Per-fold preprocessing:
  - missing value indicators for columns with high missingness
  - median imputation fit on training fold only
  - percentile clipping (1st–99th)
- Model training/tuning:
  - LightGBM (Optuna)
  - XGBoost (Optuna, best AUC in README)
  - CatBoost (Optuna)
- Ensemble via probability averaging

### Results
The README reports best validation ROC-AUC around **0.9046** for tuned XGBoost, with tuned LightGBM/CatBoost close behind.

### Artifacts
Primarily delivered as Jupyter notebooks:
- `bankruptcy_prediction.ipynb`
- `bankruptcy_prediction_pipeline.ipynb`

### Tech stack
- Python
- LightGBM / XGBoost / CatBoost
- Optuna
- scikit-learn
- pandas/numpy

---

## Repo: Customer-analytics-ml-pipeline (`Himanshu-Laddhad/Customer-analytics-ml-pipeline`)

- Repo URL: https://github.com/Himanshu-Laddhad/Customer-analytics-ml-pipeline

### What it is (high-level)
An end-to-end churn + CLV prediction pipeline (KKBox dataset framing) that combines:
- large-scale feature engineering via **DuckDB SQL**
- leakage auditing and temporal splitting
- model benchmarking (LR/RF/XGB/LGBM/stacking)
- Optuna tuning
- SHAP explainability
- business decisioning via expected-value ROI model
- Streamlit dashboard with precomputed outputs

### Key business framing
The README highlights business impact through:
- early churn warning approach (cohort/temporal split)
- EV-based targeting with ROI modeling and sensitivity analysis

### Data engineering highlights
- Feature engineering from massive logs (described as 410M rows) using SQL.
- Two-pass aggregation design for memory constraints.

### Leakage auditing
The README explicitly calls out leakage discovery (e.g., certain transaction/expiry date variables with large churn-rate splits), and that these were audited/handled.

### Model performance (reported)
Churn classification models with high ROC-AUC (README shows XGBoost/LightGBM around ~0.981x), and CLV regression with strong R² (README reports LightGBM regressor ~0.992).

### Implementation components
The repo includes:
- notebooks for data prep/feature engineering/modeling
- `queries/` SQL used for engineered features
- `app/` Streamlit dashboard (precomputed outputs)

---

## Repo: marketing-churn-ml-pipeline (`Himanshu-Laddhad/marketing-churn-ml-pipeline`)

- Repo URL: https://github.com/Himanshu-Laddhad/marketing-churn-ml-pipeline

### What it is (high-level)
An end-to-end ML pipeline predicting Airbnb host attrition and optimizing a cost-constrained retention strategy.

### Business decision rule
The project’s central decision-theoretic targeting rule is:

> Give a $1,000 retention gift **only if** `p(churn) × annual_profit > 1000`.

This ensures positive expected value interventions.

### Technical approach
- EDA + feature engineering from reservation history
- preprocessing pipeline:
  - numeric: median imputation + scaling
  - categorical: impute + one-hot encoding
- model training/tuning:
  - XGBoost + LightGBM tuned with Optuna
- evaluation emphasizes custom profit score rather than only AUC

### Main artifact
- Jupyter notebook (`ai_for_marketing_final.ipynb`)

---

## Repo: mlb-salary-prediction (`Himanshu-Laddhad/mlb-salary-prediction`)

- Repo URL: https://github.com/Himanshu-Laddhad/mlb-salary-prediction

### What it is (high-level)
A full regression benchmarking pipeline predicting MLB player salaries from season + career performance stats. The repo compares multiple classic statistical/ML regression approaches side-by-side.

### What’s being taught/demonstrated
- baseline OLS regression
- polynomial regression and overfitting behavior (bias-variance tradeoff)
- stepwise feature selection (AIC)
- regularization via Ridge and Lasso with CV

### Key reported outcome
The README states Ridge regression achieves best validation performance (lowest MSE) and Lasso yields a sparse feature set by zeroing out weak predictors.

### Repo contents
- `mlb_salary_prediction.ipynb`
- `Hitters.csv`

---

## Repo: telecom-churn-eda (`Himanshu-Laddhad/telecom-churn-eda`)

- Repo URL: https://github.com/Himanshu-Laddhad/telecom-churn-eda

### What it is (high-level)
Exploratory data analysis to identify churn drivers in a telecom dataset (3,333 customers). The project emphasizes data quality checks, outlier analysis, and identifying the strongest churn predictors.

### Key findings (from README)
- International Plan is the strongest churn signal (large churn-rate gap reported).
- Customer service call frequency is a strong numeric predictor.
- Geographic encodings (area codes) appear unreliable due to random distribution.

### Repo contents
- `telecom_churn_eda.ipynb`
- dataset file (Churn.csv)

---

## Repo: Walmart-demand-forecasting (`Himanshu-Laddhad/Walmart-demand-forecasting`)

- Repo URL: https://github.com/Himanshu-Laddhad/Walmart-demand-forecasting

### What it is (high-level)
An end-to-end retail demand forecasting case study replicating the logic behind Walmart’s move from a seasonal/exponential smoothing baseline to gradient-boosted models (LightGBM) with rich feature engineering.

### Problem framing (why GBM beats baseline)
The README calls out structural failure modes of legacy seasonal approaches:
- event-date drift (holidays shift week-to-week)
- signal blindness to covariates (promotions, macro signals)
- national forecast → store allocation failures for region-specific items

### Approach & feature engineering
- lag features (including a 52-week lag as a learnable baseline)
- explicit holiday/event indicators
- rolling stats
- external covariates (e.g., temperature, fuel, CPI, unemployment, markdowns)
- strict temporal split to avoid leakage

### Evaluation
Uses WAPE as the core metric (weighted by sales volume). The README reports improvements vs baseline.

### Repo contents
- `walmart_forecasting_case_study.ipynb`
- figures and outputs directories

---

## Repo: price-elasticity-and-optimal-pricing (`Himanshu-Laddhad/price-elasticity-and-optimal-pricing`)

- Repo URL: https://github.com/Himanshu-Laddhad/price-elasticity-and-optimal-pricing

### What it is (high-level)
An econometric pricing strategy analysis using log-log regression to estimate price elasticity, quantify the impact of advertising/featuring on elasticity, and compute profit-maximizing prices.

### Methods (from README)
- log-log regression with interaction (`log_price × feat`)
- price digit decomposition to test psychological pricing effects
- train/test evaluation for generalization

### Key reported results
The README reports elasticity estimates for featured vs not featured conditions and corresponding optimal prices.

---

## Repo: retail-brand-pricing-analysis (`Himanshu-Laddhad/retail-brand-pricing-analysis`)

- Repo URL: https://github.com/Himanshu-Laddhad/retail-brand-pricing-analysis

### What it is (high-level)
Descriptive analysis of orange juice sales across three brands to understand pricing, brand positioning, and promotion (“feature”) effects on sales.

### Methods
- descriptive stats by brand
- log transforms for linearity
- box plots/histograms + scatter plots with OLS fit lines

### Key findings (from README)
- Tropicana positioned as premium with higher prices.
- Dominicks leads in volume at lower prices.
- Promotions drive sales lift, with proportional differences across brands.

---

## Repo: yelp-review-nlp-topic-modeling (`Himanshu-Laddhad/yelp-review-nlp-topic-modeling`)

- Repo URL: https://github.com/Himanshu-Laddhad/yelp-review-nlp-topic-modeling

### What it is (high-level)
An unsupervised NLP project using LDA topic modeling on Yelp restaurant reviews, then a multinomial logistic regression to predict star ratings from topic proportions.

### Pipeline
- bigram extraction
- LDA with multiple topic counts (k = 5, 8, 10)
- select k based on interpretability
- multinomial logistic regression on topic weights

### Key results (from README)
The README states k=8 produced the best interpretability trade-off, and topic coefficients aligned with intuitive positive/negative experience drivers.

---

## Repo: Retail-trend-intelligence-platform (`Himanshu-Laddhad/Retail-trend-intelligence-platform`)

- Repo URL: https://github.com/Himanshu-Laddhad/Retail-trend-intelligence-platform

### What it is (high-level)
A real-time trend intelligence platform for fashion retail that computes momentum scores from Google Trends, visualizes regional demand across countries, and scrapes Pinterest imagery for visual references. It optionally uses Groq (text + vision) to generate dashboard copy and verify/caption images.

### Core capabilities
- Google Trends time-series and regional interest analysis for a user query
- momentum scoring and rising/stable/falling classification
- related term discovery and bubble visualization
- Pinterest scraping + deduplication
- image relevance verification with Groq vision (strict JSON)
- image ranking via a custom “Fashion Relevance Trend Score”
- SQLite caching for trend and image metadata
- backtest/validation against Pinterest Predicts 2024–2026 labeled data

### Notable engineering detail: explicit metric formulas
The README documents exact computation logic, including:
- momentum score definition (recent vs historical averages + clipping)
- bubble score fallback handling (numeric vs missing vs breakout labels)
- hybrid trend match blending (LLM + rule-based)
- final fashion score formula and ranking behavior

### Architecture
From README project structure:
- `app.py`: Streamlit dashboard
- `db.py`: SQLite cache helpers
- `backend/`: AI analyzer, fashion scorer, Groq configuration
- `data_sources/google_trends.py`: pytrends fetchers + momentum computation
- `scrapers/pinterest_scraper.py`: Selenium scraper
- `backtest/`: batch trend fetch, sliding window scoring, metrics, visualization, orchestrator

### Dependencies (high level)
From `requirements.txt`:
- Streamlit + Plotly + matplotlib + wordcloud
- pandas + requests + pytrends + duckdb
- Selenium + webdriver-manager
- groq + google-genai
- additional analytics/ML libs listed (prophet, lifetimes, cornac, sentence-transformers, umap/hdbscan, mlflow, pandera, statsmodels/scipy)

### How to run
- `pip install -r requirements.txt`
- copy `.env.example` → `.env` and set `GROQ_API_KEY`
- `streamlit run app.py`

---

## Blocked / needs manual paste
Two public repos currently cannot be read via the GitHub API from this environment (contents listing fails), so they are not included yet:
- `Himanshu-Laddhad/Aha-Moment`
- `Himanshu-Laddhad/customer-review-intelligence-nlp`

If you paste their README content here, I’ll add them into this same document.
