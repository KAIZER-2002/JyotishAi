# Security Policy

This document outlines the security architecture, data protection controls, and vulnerability reporting procedures for JyotishAI.

## Authentication and JWT Security

- Authentication Mechanism: OAuth2 Password Flow with JSON Web Tokens (JWT).
- Password Hashing: Password credentials are hashed using `bcrypt` with automated salt generation.
- Token Lifetime: Access tokens expire after 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES=30`).
- Token Storage: Stored in HTTP cookies with `SameSite=Lax` and `HttpOnly` attributes where applicable.
- Token Revocation: Backend tracks `token_version` on user models to allow instant invalidation of active sessions across devices upon logout.

## Secrets and Environment Variables

- Secret Key Management: `SECRET_KEY` must be configured as a 32-byte cryptographically secure random hex string.
- API Key Isolation: Third-party LLM API keys (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are read strictly from environment variables on the backend container.
- Client Isolation: Third-party API keys are never exposed or sent to the frontend client.

## File Upload Security

- Allowed Media Types: Uploads are restricted to plain text (`.txt`), Markdown (`.md`), PDF (`.pdf`), and Microsoft Word (`.docx`).
- File Size Enforcement: Maximum upload payload size is capped at 10 MB per file.
- Storage Isolation: Uploaded files are processed in memory and indexed into isolated ChromaDB vector collections scoped by `user_id`.

## Known Security Practices

- CORS Policy: Origins are strictly controlled via `CORS_ORIGINS` in FastAPI settings.
- Input Validation: Pydantic schemas enforce type bounds on all incoming REST request payloads.
- SQL Injection Prevention: All database queries use SQLAlchemy parameterized ORM calls; raw unescaped SQL strings are not used.

## Future Security Work

- Implementation of Redis-backed rate limiting (`slowapi`) per IP and user account on sensitive auth routes (`/auth/login`, `/auth/register`).
- Support for optional Multi-Factor Authentication (MFA/TOTP).

## Responsible Disclosure

If you discover a potential security vulnerability in JyotishAI:

1. Do not open a public GitHub issue.
2. Email details of the vulnerability to `security@jyotishai.com` or contact project maintainers directly.
3. Include reproduction steps, sample HTTP requests, and proof of concept details.
4. Maintain confidentiality until a patch has been released.
