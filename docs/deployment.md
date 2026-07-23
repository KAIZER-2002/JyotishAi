# JyotishAI - Production Operations Manual

This guide describes the production architecture, scaling operations, backup policies, and checklists for JyotishAI.

---

## 1. System Architecture & Port Maps

JyotishAI uses an integrated Docker Compose topology behind a reverse proxy:

```
                    [ External Client Request ]
                               │
                               ▼
                        [ Nginx Port 80 ]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     [ / ] Routing                       [ /api ] & [ /health ]
            │                                     │
            ▼                                     ▼
 [ frontend:3000 (Next.js) ]           [ backend:8000 (FastAPI) ]
                                                  │
                               ┌──────────────────┴──────────────────┐
                               ▼                                     ▼
                 [ postgres:5432 (Database) ]          [ chroma:8000 (Standalone Vector DB) ]
```

- **Reverse Proxy**: Nginx binds to host port `80` (and `443` in production SSL settings), terminating client requests and proxying requests upstream.
- **Port Isolation**: Backend (`8000`), Frontend (`3000`), Database (`5432`), and Standalone Chroma (`8000`) communicate entirely within the virtual network `jyotishai_net`, preventing direct public access bypass.

---

## 2. Startup, Migrations & Graceful Shutdown

### Docker Start Sequence
Services boot in order using `depends_on` conditions:
1. **postgres** and **chroma** start first and initialize health checks.
2. **backend** starts once database health checks return healthy, running database schema updates.
3. **frontend** starts once backend returns a healthy status code on `/health`.
4. **nginx** boots once frontend and backend instances are fully healthy.

### Database Migrations
Always run Alembic schema upgrades before launching containers:
```bash
docker compose run --rm backend alembic upgrade head
```

### Graceful Shutdown
Uvicorn and Node processes catch SIGTERM/SIGINT signals. To perform updates without interrupting ongoing transactions, stop containers using:
```bash
docker compose down --timeout 15
```

### Rollback Strategy
If a deployment fails verification, execute a rollback using these steps:
1. Revert target Git changes to the previous stable release commit.
2. Re-run building steps: `docker compose build`.
3. Restore DB state from the last automated pre-deploy backup archive:
   ```bash
   bash scripts/restore.sh ./backups/backup_YYYYMMDD_HHMMSS.tar.gz
   ```
4. Start the stack: `docker compose up -d`.

---

## 3. Backup Strategy & Disaster Recovery

### Automated Backup Strategy
Backups should run daily via system crontabs. The database is dumped using standard tools, and vector db indices are copied to `/var/backups/jyotishai`.

#### Daily Database & Vector Index Backup (`scripts/backup.sh`)
Executes:
1. `pg_dump` on PostgreSQL inside the container.
2. Compresses the database output.
3. Packages the persistent index directories from the Chroma volume.
4. Cleans up files older than 30 days.

### Restore Procedure
To recover a system state from a backup snapshot:
1. Stop running applications:
   ```bash
   docker compose stop backend frontend nginx
   ```
2. Run the restore script:
   ```bash
   bash scripts/restore.sh /path/to/backup_directory
   ```
3. Boot the application stack:
   ```bash
   docker compose start backend frontend nginx
   ```

---

## 4. Operational Checklists

### 4.1. Pre-Deployment Checklist
- [ ] Confirm `.env` file exists with production keys populated.
- [ ] Check `DEBUG=False` in `.env`.
- [ ] Generate a secure 32-byte hex string for `SECRET_KEY`.
- [ ] Verify database connection strings point to the container name (`postgres:5432`).
- [ ] Confirm vector store connects to standalone `chroma:8000` (`CHROMA_HOST=chroma`).
- [ ] Validate Nginx configuration syntax (`nginx -t`).

### 4.2. Security Checklist
- [ ] Disable root login and restrict SSH on host machine.
- [ ] Enable firewall (UFW/Firewalld) allowing only ports `80`, `443`, and secure SSH.
- [ ] Enable HTTPS with SSL/TLS certificates (e.g. Let's Encrypt).
- [ ] Verify that no internal service ports (3000, 8000, 5432) are mapped publicly in `docker-compose.yml`.
- [ ] Ensure all containers run under non-root users (`nextjs`, `appuser`, `nginx`).
- [ ] Validate security headers (`X-Frame-Options`, `Content-Security-Policy`) return correctly on curls.

### 4.3. Release & Migration Checklist
- [ ] Take a snapshot backup of PostgreSQL database before running migrations.
- [ ] Test the Alembic migrations downward script locally to ensure rollbacks are safe.
- [ ] Run `docker compose run --rm backend alembic upgrade head` to apply updates.
- [ ] Verify application health endpoints (`/health`) return HTTP status `200`.
- [ ] Review error logs in `/var/log/nginx/` and docker compose stdout.
