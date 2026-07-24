# JyotishAI

JyotishAI is a full-stack web application designed for Vedic astrological calculation, chart interpretation, and context-aware conversation using Retrieval-Augmented Generation (RAG). It combines Swiss Ephemeris astronomical calculations with multi-provider Large Language Models (LLM) and a vector document store.

## Features

- Astronomical Calculations: Computes planetary positions, house cusps, nakshatras, ayanamsa values (Lahiri, Raman, Krishnamurti, True Chitra), and Vimshottari Dasha periods using Swiss Ephemeris backend bindings.
- Interactive Chart Rendering: Displays interactive North Indian, South Indian, and East Indian divisional chart layouts (D1 Rashi, D9 Navamsha, D60 Shastiamsa).
- Conversational RAG Engine: Accepts user document uploads (PDF, DOCX, TXT, Markdown), generates vector embeddings via Google Gemini (`gemini-embedding-001`), indexes chunks into ChromaDB, and performs context retrieval during chat sessions.
- Multi-Provider LLM Integration: Supports Google Gemini (`gemini-flash-latest`), OpenRouter (GPT-4o Mini, Claude 3.5 Sonnet, Llama 3.3 70B), OpenAI Direct (`gpt-4o-mini`, `gpt-4o`), and Anthropic Direct (`claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`).
- User Management: Account registration, JWT authentication, user profile management, historical chat session persistence, and customizable theme settings.

## Technology Stack

### Backend
- Framework: FastAPI (Python 3.12)
- Database: PostgreSQL 15 with SQLAlchemy 2.0 (asyncpg) and Alembic migrations
- Ephemeris Engine: Swiss Ephemeris (`libephemeris` Python bindings)
- Vector Store: ChromaDB
- Embeddings: Google GenAI (`gemini-embedding-001`) with 768-dimension configuration
- LLM SDKs: `google-genai`, `openai`, `anthropic`

### Frontend
- Framework: Next.js 16 (App Router)
- UI Library: React 19, Tailwind CSS, Radix UI primitives, Lucide React
- State Management: TanStack React Query v5, Zustand, `next-themes`

### Infrastructure
- Containerization: Docker and Docker Compose
- Reverse Proxy: Nginx

## Architecture Overview

The system is structured as a client-server web application behind an Nginx reverse proxy. The Next.js frontend handles server-side rendering and client interaction. The FastAPI backend exposes REST API endpoints for authentication, chart generation, document upload, and chat streaming.

```
Client (Browser) -> Nginx Reverse Proxy (Port 80)
                     ├── / -> Next.js Frontend (Port 3000)
                     └── /api/v1 -> FastAPI Backend (Port 8000)
                                     ├── PostgreSQL (Database)
                                     ├── ChromaDB (Vector Index)
                                     ├── Swiss Ephemeris (Calculations)
                                     └── LLM APIs (Gemini, OpenRouter, OpenAI, Anthropic)
```

## Screenshots

`[Dashboard Mockup Placeholder]`
`[Birth Chart Calculation View Placeholder]`
`[AI Chat and Knowledge Base Placeholder]`

## Installation

### Prerequisites

- Node.js 20.0 or higher
- Python 3.12
- PostgreSQL 15
- Docker and Docker Compose (recommended for containerized deployment)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/KAIZER-2002/JyotishAi.git
cd JyotishAi
```

2. Setup backend environment:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements/base.txt
```

3. Setup frontend environment:
```bash
cd ../frontend
npm install
```

4. Configure environment variables by copying `.env.example` to `.env` in the project root.

5. Run database migrations:
```bash
cd ../backend
alembic upgrade head
```

6. Start local development servers:
```bash
# Terminal 1 - Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Docker Deployment

To launch the complete stack using Docker Compose:

```bash
docker compose up -d --build
```

The services will be available at:
- Web Application: `http://localhost`
- API Base Endpoint: `http://localhost/api/v1`
- API Health Check: `http://localhost/api/v1/health`

To stop the services:
```bash
docker compose down
```

## Environment Variables

Key variables required in `.env`:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Secret key for JWT signing | 32-byte hex string |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://user:pass@postgres:5432/jyotishai` |
| `CHROMA_HOST` | ChromaDB hostname | `chroma` |
| `CHROMA_PORT` | ChromaDB port | `8000` |
| `GEMINI_API_KEY` | Google Gemini API Key | `your_gemini_api_key` |
| `OPENROUTER_API_KEY` | OpenRouter API Key | `your_openrouter_api_key` |
| `OPENAI_API_KEY` | OpenAI API Key (Optional) | `your_openai_api_key` |
| `ANTHROPIC_API_KEY` | Anthropic API Key (Optional) | `your_anthropic_api_key` |

See `.env.example` for the full template.

## Project Structure

```
JyotishAI/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST route handlers
│   │   ├── core/            # App configuration and security
│   │   ├── db/              # Database models, sessions, repositories
│   │   ├── domain/          # Domain interfaces and value objects
│   │   ├── infrastructure/  # Swiss Ephemeris wrapper services
│   │   └── services/        # Business logic, RAG, and LLM providers
│   ├── alembic/             # Migration scripts
│   └── requirements/        # Dependency specifications
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client layer
│   └── store/               # Zustand state stores
├── nginx/                   # Nginx reverse proxy configuration
├── docker-compose.yml       # Container orchestration spec
├── README.md
├── ARCHITECTURE.md
├── DEPLOYMENT.md
├── API.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CHANGELOG.md
```

## Known Limitations

- Direct OpenAI and Anthropic API keys require paid credits active on the respective accounts; otherwise requests fall back to configured Gemini or OpenRouter models.
- Document processing currently supports plain text, Markdown, PDF, and DOCX files under 10MB.
- Swiss Ephemeris binary data files download automatically on first initialization if not cached locally.

## Roadmap

- Transit and Ashtakavarga calculation modules.
- Export of PDF reports for comprehensive chart interpretations.
- Multi-user organization workspace sharing.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
