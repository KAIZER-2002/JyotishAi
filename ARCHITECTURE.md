# System Architecture

This document describes the architectural design and implementation details of JyotishAI.

## Architecture Overview

JyotishAI uses a decoupled client-server architecture consisting of a Next.js frontend, a FastAPI backend, a PostgreSQL relational database, a ChromaDB vector database, and an Nginx reverse proxy.

```
+-----------------------------------------------------------------------------------+
|                                 Nginx (Port 80)                                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
                     v                                         v
     +-------------------------------+         +-------------------------------+
     | Next.js Frontend (Port 3000)  |         |   FastAPI Backend (Port 8000) |
     | - App Router                  |         | - Auth Routes                 |
     | - React Query                 |         | - Chart Engine                |
     | - Zustand Stores              |         | - RAG Service                 |
     +-------------------------------+         +---------------+---------------+
                                                               |
                                     +-------------------------+-------------------------+
                                     |                         |                         |
                                     v                         v                         v
                           +------------------+      +------------------+      +------------------+
                           | PostgreSQL DB    |      | ChromaDB         |      | Swiss Ephemeris  |
                           | User & Chat Data |      | Vector Store     |      | Calculation Lib  |
                           +------------------+      +------------------+      +------------------+
```

## Frontend Architecture

The frontend is constructed using Next.js 16 App Router with React 19.

- App Routes: Route pages are separated into public routes (`(public)`) such as `/login` and `/register`, and authenticated dashboard routes (`(dashboard)`) such as `/dashboard`, `/chart`, `/analysis`, `/chat`, `/documents`, `/history`, and `/settings`.
- Component Layer: Reusable UI primitives built with Tailwind CSS and Radix UI.
- State Management: 
  - Server state, caching, and background refetching are managed via TanStack React Query (`useQuery`, `useMutation`).
  - Local authentication tokens and user state are managed via Zustand (`useAuthStore`).
  - Active theme preference is managed using `next-themes` synced with backend user settings via `ThemeSync`.
- Streaming Client: `useChat` custom hook uses `fetch` with `ReadableStream` to process Server-Sent Events (SSE) line by line, maintaining smooth streaming state.

## Backend Architecture

The backend is built with Python 3.12 and FastAPI using async handlers.

- API Routes (`app/api/v1/routes/`): Handlers for authentication (`auth.py`), user profile (`users.py`), chart calculations (`astrology_analysis.py`), document management (`documents.py`), conversation management (`conversations.py`), and chat streaming (`chat.py`).
- Service Layer (`app/services/`): Business logic encapsulated into decoupled services:
  - `AstrologyAnalysisService`: Coordinates planetary calculations and house positioning.
  - `YogaAnalysisService`: Rule-based evaluation engine for Vedic planetary yogas.
  - `DocumentService`: Handles document ingestion, parsing, chunking, and background processing.
  - `ChatSessionService`: Manages conversation persistence and streaming response generation.
- Domain Contracts (`app/domain/`): Abstract interfaces for `LLMProvider`, `KnowledgeRetriever`, and `VectorStore` to allow flexible provider implementations.

## Authentication Flow

Authentication uses OAuth2 Password Flow with JSON Web Tokens (JWT).

1. User submits login credentials to `POST /api/v1/auth/login`.
2. Backend verifies password hash using `bcrypt`.
3. Backend generates an HTTP access token (default 30-minute expiry) signed with `SECRET_KEY` using HS256.
4. Token is stored in HTTP cookies (`access_token`) and returned in response payload.
5. Frontend includes token in request header: `Authorization: Bearer <token>`.
6. `get_current_user` FastAPI dependency validates token signature and loads user model from PostgreSQL.

## Database Structure

PostgreSQL stores operational data. Schema migrations are managed by Alembic.

### Users Table (`users`)
- `id` (UUID, Primary Key)
- `email` (String, Unique, Index)
- `username` (String, Unique)
- `hashed_password` (String)
- `full_name` (String)
- `timezone`, `date_of_birth`, `time_of_birth`, `birth_place`, `latitude`, `longitude`, `ayanamsa`
- `settings` (JSONB): Stores general preferences, AI settings (default model, detail level), and notifications.
- `created_at`, `updated_at` (Timestamps with timezone)

### Documents Table (`documents`)
- `id` (String, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `filename` (String)
- `media_type` (String)
- `size_bytes` (Integer)
- `status` (String: `pending`, `processing`, `completed`, `failed`)
- `error_message` (String, Nullable)
- `content` (Text, Parsed plain text)
- `metadata_json` (JSONB)
- `created_at`, `updated_at` (Timestamps)

### Conversations & Messages Tables
- `conversations`: Stores `id` (UUID), `title`, `user_id` (UUID), `created_at`, `updated_at`.
- `messages`: Stores `id` (UUID), `conversation_id` (UUID), `role` (`user` | `assistant`), `content` (Text), `created_at`.

## AI and RAG Pipeline

```
[Document Upload] -> Plain Text Extraction -> Token Chunking -> Gemini Embeddings (768-dim) -> ChromaDB
                                                                                                  |
[User Chat Query] -> Vector Search Query ---------------------------------------------------------+
       |
       v
Context Retrieval -> Prompt Assembly -> LLM Provider (Gemini/OpenRouter/OpenAI/Anthropic) -> SSE Stream
```

### Document Ingestion
1. User uploads a file via `POST /api/v1/documents/upload`.
2. File record is created in PostgreSQL with status `pending`.
3. Background task `_process_document_background` is scheduled.
4. Text parser extracts plain text (PDF via pypdf/fitz, DOCX via python-docx, TXT/MD plain text).
5. Text is split into chunks (500-1000 characters with overlap).
6. Embeddings are generated using `GeminiEmbeddingProvider` configured for output dimensionality 768.
7. Vectors and metadata are upserted into ChromaDB collection.
8. Document status in PostgreSQL updates to `completed`.

### Chat Workflow
1. User sends message to `POST /api/v1/chat/stream`.
2. Active user birth chart data is loaded and calculated.
3. Relevant document chunks are queried from ChromaDB using prompt embedding vector.
4. Structured prompt is assembled combining system instructions, birth chart placement, detected yogas, retrieved document context, and chat history.
5. `LLMProvider` generates response stream using configured model.
6. Backend yields newline-delimited JSON chunks (`{"text": "...", "conversation_id": "..."}`) via FastAPI `StreamingResponse`.
7. Once streaming completes, assistant reply is persisted into `messages` table.

## Deployment Architecture

The application is deployed using Docker Compose behind an Nginx reverse proxy.

- Nginx container binds to host port 80.
- Routes matching `/api/v1/` proxy requests to `jyotishai-backend:8000`.
- All other routes proxy requests to `jyotishai-frontend:3000`.
- PostgreSQL database container uses named volume `postgres_data` for data persistence.
- ChromaDB container uses volume `chroma_data` for vector database storage.
