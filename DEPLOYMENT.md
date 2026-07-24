# Deployment Guide

This guide details deployment options, environment configuration, database migrations, and operational procedures for JyotishAI.

## System Requirements

### Hardware Requirements
- CPU: 2 vCPUs minimum (4 vCPUs recommended)
- RAM: 4 GB RAM minimum (8 GB recommended for vector operations)
- Disk Space: 20 GB free disk space

### Software Requirements
- OS: Linux (Ubuntu 22.04 LTS recommended), macOS, or Windows Server
- Docker: Engine v24.0+
- Docker Compose: v2.20+

## Docker Deployment (Recommended)

1. Clone repository to server:
```bash
git clone https://github.com/KAIZER-2002/JyotishAi.git /opt/jyotishai
cd /opt/jyotishai
```

2. Create production environment configuration:
```bash
cp .env.example .env
```
Edit `.env` to set secure passwords, `SECRET_KEY`, and API keys.

3. Start services:
```bash
docker compose up -d --build
```

4. Verify service health:
```bash
docker compose ps
curl http://localhost/api/v1/health
```

## Production Deployment Architecture

In production, traffic should flow through an SSL termination proxy to Nginx.

```
Internet -> Cloudflare / Load Balancer (SSL 443) -> Nginx Proxy (Port 80) -> Internal Containers
```

### Docker Compose Service Architecture

- `jyotishai-postgres`: PostgreSQL 15 database listening on internal port 5432.
- `jyotishai-chroma`: ChromaDB vector database listening on internal port 8000.
- `jyotishai-backend`: FastAPI application listening on internal port 8000.
- `jyotishai-frontend`: Next.js standalone application listening on internal port 3000.
- `jyotishai-nginx`: Nginx reverse proxy listening on host port 80.

## Database Migrations

Alembic handles PostgreSQL schema migrations. Migrations run automatically during backend container initialization.

To run migrations manually:
```bash
docker exec -it jyotishai-backend alembic upgrade head
```

To roll back a migration step:
```bash
docker exec -it jyotishai-backend alembic downgrade -1
```

To create a new migration after model changes:
```bash
docker exec -it jyotishai-backend alembic revision --autogenerate -m "describe_change"
```

## Nginx and SSL Configuration

### Nginx Configuration
The default proxy configuration resides in `nginx/default.conf`.

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 25M;

    location /api/v1/ {
        proxy_pass http://jyotishai-backend:8000/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE Streaming headers
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location / {
        proxy_pass http://jyotishai-frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Enabling SSL with Certbot

To set up HTTPS on a Linux server using Let's Encrypt:

1. Install Certbot:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

2. Generate certificate:
```bash
sudo certbot --nginx -d yourdomain.com
```

3. Certbot will update Nginx configuration to redirect HTTP to HTTPS.

## Troubleshooting

### Container Health Checks
Check status of all containers:
```bash
docker compose ps
```

View backend logs:
```bash
docker logs -f --tail 100 jyotishai-backend
```

View frontend logs:
```bash
docker logs -f --tail 100 jyotishai-frontend
```

### Database Connection Failures
If the backend fails to connect to PostgreSQL:
1. Ensure `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in `.env` match `DATABASE_URL`.
2. Confirm container startup order (`jyotishai-backend` depends on `jyotishai-postgres`).

### Vector Embedding Errors
If document uploads fail with status `failed`:
1. Check backend logs for Gemini API key validity:
   ```bash
   docker logs jyotishai-backend | grep -i embedding
   ```
2. Verify model setting is set to `gemini-embedding-001`.
