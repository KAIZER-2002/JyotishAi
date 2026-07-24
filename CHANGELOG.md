# Changelog

All notable changes to the JyotishAI project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-24

### Added
- Multi-provider LLM support for Google Gemini (`gemini-flash-latest`), OpenRouter (`openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`), OpenAI Direct (`gpt-4o-mini`, `gpt-4o`), and Anthropic Direct (`claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`).
- RAG document processing pipeline supporting PDF, DOCX, TXT, and Markdown files.
- Vector indexing using Google `gemini-embedding-001` with explicit 768-dimension configuration in ChromaDB.
- Interactive birth chart calculator supporting North Indian, South Indian, and East Indian divisional chart visualizations (D1, D9, D60).
- Astrological calculation engine using Swiss Ephemeris (`libephemeris` Python bindings) for accurate planetary positions, house cusps, and Vimshottari Dasha calculations.
- Real-time Server-Sent Events (SSE) chat streaming (`POST /api/v1/chat/stream`).
- Theme Engine with 5 curated themes (`Eclipse`, `Aurora Forest`, `Solar Ember`, `Celestial Ocean`, `Royal Ivory`) persisted across sessions via Next.js `ThemeSync` and user backend settings.
- Notification Center dropdown with unread badge indicators and document processing status tracking.
- Interactive Dashboard cards linking directly to Birth Chart, Dasha Cycle, and Knowledge Base management pages.
- Docker Compose deployment stack including Nginx, FastAPI backend, Next.js frontend, PostgreSQL database, and ChromaDB vector store.

### Fixed
- Resolved 404 NOT_FOUND API error caused by deprecated Gemini embedding models by updating to `gemini-embedding-001` with explicit 768-dimension parameters.
- Fixed empty assistant response bubbles in UI caused by ephemeris download delays during initial chat execution.
- Fixed theme reset bug on page reload by prioritizing stored user preferences in `localStorage` and syncing with database settings.
- Fixed blank model selection box in Settings page by adding fallback mapping for legacy model keys.

### Changed
- Refactored RAG document service background task callback to handle asynchronous text parsing and ChromaDB upsert operations cleanly.
- Updated Next.js frontend layout and topbar components for improved responsive rendering.
