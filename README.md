# JyotishAI

JyotishAI is a production-grade, containerized AI-powered Vedic Astrology application that integrates advanced astrological calculations, life-path interpretation engines, and a Retrieval-Augmented Generation (RAG) scriptures knowledge base.

---

## 1. Architecture Diagram

```
                            +-------------------+
                            |  Internet Client  |
                            +-------------------+
                                      │
                                      ▼ (Port 80/443)
                            +-------------------+
                            |   Nginx Reverse   |
                            |   Proxy Server    |
                            +-------------------+
                               /             \
             (Routed to /)    /               \ (Routed to /api, /health)
                             ▼                 ▼
                 +-----------------+     +-----------------+
                 |    frontend     |     |     backend     |
                 | (Next.js Node)  |     | (FastAPI Uvicorn)|
                 +-----------------+     +-----------------+
                                                  │
                                        /─────────┴─────────\
                                       ▼                     ▼
                             +-------------------+ +-------------------+
                             |     postgres      | |      chroma       |
                             |  (PostgreSQL DB)  | | (Standalone HTTP) |
                             +-------------------+ +-------------------+
```

---

## 2. Technology Stack

### Backend
- **Core Framework**: FastAPI (Python)
- **Database Engine**: SQLAlchemy 2.0 (Object Relational Mapping)
- **Schema Migrations**: Alembic
- **Relational Storage**: PostgreSQL
- **Vector Database**: Standalone Chroma DB HTTP server
- **RAG & Embeddings**: Google Gemini API (Text embeddings & LLM chat sessions)

### Frontend
- **Core Framework**: React & Next.js (TypeScript)
- **Data Fetching**: TanStack React Query (Axios client base)
- **Styling**: Tailwind CSS v4 & custom glassmorphism components
- **Transitions**: Framer Motion
- **Toasts**: Sonner

### Reverse Proxy & Operations
- **Reverse Proxy**: Nginx (handling SSL termination, WebSocket upgrades, rate limits, and gzip compression)
- **Containerization**: Multi-stage Docker & Docker Compose orchestration

---

## 3. Features

### 3.1. Authentication
- Robust token-based user authentication covering sign-up, sign-in, token refreshes, and reset password templates.

### 3.2. AI Chat
- Context-aware Vedic Astrologer dialogue engine using Gemini API. Fits RAG-retrieved scripture context blocks into the prompt window.

### 3.3. Birth Charts
- Computes planetary coordinate configurations and divisional charts (D1 Rashi, D9 Navamsa, D10 Dasamsa, D60 Shastiamsa) utilizing precise astronomical ephemeris models.

### 3.4. Astrometric Analysis
- **Vimshottari Dasha**: Computes nested dasha timelines (Maha Dasha, Antar Dasha) from natal Moon positions.
- **Yoga Detection**: Scans planet placement arrays to identify classic Vedic Yogas (e.g. Budhaditya, Raja, Gaja Kesari, Dhana, and Pancha Mahapurusha configurations).

### 3.5. Knowledge Base (RAG)
- **Document Ingestion**: Supports PDF, DOCX, TXT, and Markdown files.
- **DOCX Parser**: Dependency-free parser using standard libraries to safely extract paragraph contents.
- **Smart Queue Polling**: Web frontend monitors backend task queue statuses with intelligent query polling to update status badges (`pending`, `processing`, `completed`, `failed`).
- **Vector Cleanup**: Automatically purges document embeddings and chunk index metadata from Chroma DB upon deletion.

### 3.6. History, Profile & Settings
- **History**: Local storage calculation sheets list and active chat history database tables.
- **Profile**: Customize user preferences, birth credentials, and profile pictures.
- **Settings**: Manage application themes (standard default dark mode), keys, and password changes.

---

## 4. Installation & Local Development Setup

### 4.1. Prerequisites
- Python 3.12+ (or UV package manager)
- Node.js 20+
- PostgreSQL database instance
- Google Gemini API key

### 4.2. Environment Variables

Create a `.env` file under `backend/` and `frontend/` (see environment configuration templates for defaults):
- Backend: Refer to [backend/.env.example](file:///c:/Users/Swapnil%20Nandi/Projects/JyotishAI/backend/.env.example) or [.env.production.example](file:///c:/Users/Swapnil%20Nandi/Projects/JyotishAI/.env.production.example).
- Frontend: Refer to `NEXT_PUBLIC_API_URL`.

### 4.3. Running Locally

#### 4.3.1. Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Launch the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 4.3.2. Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run in development mode:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4.4. Running with Docker Compose

To deploy the entire production stack locally:
1. Configure environment variables in `.env` inside the workspace root (use `.env.production.example` as a guide).
2. Spin up the containers:
   ```bash
   docker compose up -d --build
   ```
3. Apply migrations in the PostgreSQL container:
   ```bash
   docker compose run --rm backend alembic upgrade head
   ```

---

## 5. Project Structure

```
JyotishAI/
├── backend/                   # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/            # API Endpoints (auth, chart, documents, chat)
│   │   ├── core/              # Config, Security, and Settings
│   │   ├── db/                # Models & Repositories (Document, User, Session)
│   │   ├── schemas/           # Pydantic Schemas
│   │   └── services/          # Business logic & parsers (document_ingestion)
│   ├── tests/                 # Pytest Suites
│   └── Dockerfile             # Multi-stage Python build
├── frontend/                  # Next.js React Frontend
│   ├── app/                   # App Router Pages
│   ├── components/            # UI components (dashboard, layouts)
│   ├── hooks/                 # React Query custom hooks (useDocuments)
│   ├── services/              # API Client callers (document)
│   └── Dockerfile             # Standalone optimized Next.js build
├── nginx/                     # Reverse Proxy Config
│   ├── nginx.conf             # Upstream servers, gzip, buffering, SSL templates
│   └── Dockerfile             # Alpine Nginx packager
├── scripts/                   # Operations automation
│   ├── deploy.sh              # Pre-flight migrations and service bootstrap
│   ├── backup.sh              # Database and Chroma DB volume archives
│   └── restore.sh             # Re-inject dumps to active volumes
└── docker-compose.yml         # Container Orchestration
```

---

## 6. Testing

### Backend Tests
Ensure your local PostgreSQL/SQLite environment is available, then run:
```bash
cd backend
python -m pytest
```

### Frontend Typecheck & Build
Compile the application to ensure Next.js build rules are validated:
```bash
cd frontend
npm run build
```

---

## 7. Deployment & Disaster Recovery

Refer to the complete production ops manual at [docs/deployment.md](file:///c:/Users/Swapnil%20Nandi/Projects/JyotishAI/docs/deployment.md) for details on:
- Automated daily backups (`scripts/backup.sh`)
- Restoration commands (`scripts/restore.sh`)
- Post-deployment health verification (`scripts/deploy.sh`)
- Rollback strategies

---

## 8. Security Notes

- **Network Containment**: Ports 5432, 8000 (Chroma), and 8000 (Backend) are locked inside the bridge network `jyotishai_net` and cannot be accessed externally.
- **Client Body Restriction**: Nginx restricts file uploads at `client_max_body_size 15M` to protect memory allocations.
- **API Rate Limiting**: The API upstream is throttled at `10r/s` with a burst limit of `20`.
- **Non-Root Execution**: Backend, frontend, and reverse proxy run under standard unprivileged accounts (`appuser`, `nextjs`, `nginx`).

---

## 9. Roadmap
- **Ollama Offline Models**: Local offline LLM integrations.
- **Hybrid Search**: Fusing BM25 keyword scans and semantic embeddings in the retrieval pipeline.
- **Multi-Tenant Partitioning**: Logical tenancy layers for large deployments.

---

## 10. License
Distributed under the MIT License. See LICENSE placeholder for terms.
