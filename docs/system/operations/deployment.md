# Deployment & Configuration Guide

## Platform Overview
The solution comprises a Next.js frontend, a FastAPI backend, MariaDB for persistence, Redis for caching/background jobs, and optional Nginx for TLS termination. Container definitions for both development and production are provided via Compose files to simplify orchestration.【F:PROJECT_STRUCTURE.md†L9-L96】【F:docker-compose.yml†L1-L71】【F:docker-compose.prod.yml†L1-L63】

## Environment Configuration
Create environment files by copying the provided examples and adjusting values for your target environment.

| Component | Template | Key Variables |
|-----------|----------|---------------|
| Backend | `backend/.env.example` | `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, token lifetimes, email/LINE integration, file upload limits, Celery endpoints, logging, and CORS settings.【F:backend/.env.example†L1-L36】 |
| Frontend | `frontend/.env.example` | Public API/app URLs, app branding, feature flags, and PWA toggles.【F:frontend/.env.example†L1-L13】 |

> **Tip:** The backend also exposes defaults through `Settings` in `app/core/config.py`. Override via environment variables or `.env` files when running with Docker or Uvicorn.【F:backend/app/core/config.py†L13-L63】

## Local Development
1. Install Docker and Docker Compose v2.
2. Duplicate env templates: `cp backend/.env.example backend/.env` and `cp frontend/.env.example frontend/.env.local`.
3. Start the stack with `docker-compose up -d --build`. Services include the Next.js dev server (port 3000), FastAPI with live reload (port 8000), MariaDB (3306), Redis (6379), and Adminer (8080).【F:docker-compose.yml†L1-L71】
4. Apply database migrations (inside the backend container):
   ```bash
   docker compose exec backend alembic upgrade head
   ```
   Alembic is preconfigured to read the `DATABASE_URL` and the model metadata for autogeneration.【F:backend/alembic/env.py†L1-L104】
5. Seed reference data or admin accounts using bespoke scripts or interactive sessions as needed.

## Production Deployment
1. Populate a `.env` file (or compose overrides) with strong secrets, database credentials, mail servers, and LINE token if notifications via LINE are required.【F:docker-compose.prod.yml†L14-L46】
2. Provision SSL certificates in `nginx/ssl` (e.g., via Let’s Encrypt) and review the bundled Nginx reverse proxy which enforces HTTPS, rate limiting, gzip, and routes traffic to the frontend, backend, and static assets.【F:docker-compose.prod.yml†L47-L58】【F:nginx/nginx.conf†L5-L131】
3. Launch the stack: `docker compose -f docker-compose.prod.yml --env-file .env up -d --build`.
4. Run Alembic migrations in the backend container as part of the release pipeline to ensure schema parity.
5. Configure persistent volumes for MariaDB (`db_data`), Redis (`redis_data`), and static file exports (`static_files`). Optional backups can be mounted through the `backups` volume on the database service.【F:docker-compose.prod.yml†L25-L63】

## Operational Considerations
- **Static uploads:** User-uploaded documents are served from the `uploads/` directory mounted by FastAPI at `/static`. Ensure the folder is writable and backed up in production.【F:backend/app/core/config.py†L29-L41】【F:backend/app/main.py†L21-L88】
- **Background jobs:** Celery broker/result URLs default to Redis logical databases 1 and 2; adjust if deploying managed Redis or scaling workers.【F:backend/app/core/config.py†L43-L47】
- **Scaling:** Frontend and backend containers can be horizontally scaled; ensure the database uses a managed service or replicated setup and configure Redis persistence for job reliability.
- **Observability:** Enable structured JSON logs (`LOG_FORMAT=json`) and adjust `LOG_LEVEL` to integrate with centralized logging solutions.【F:backend/app/core/config.py†L43-L63】 Consider extending Nginx logs or plugging in metrics exporters.

## Post-Deployment Checklist
- ✅ Database migrations executed successfully.
- ✅ Admin or fleet administrator account created and two-factor authentication enforced where required.
- ✅ DNS records point to the Nginx ingress and TLS certificates are valid.
- ✅ Scheduled backups for MariaDB and periodic verification restores are in place.
- ✅ Health endpoints (`/health`, `/api/v1/health`) return `healthy` and monitoring alerts are wired to your operations channels.【F:backend/app/main.py†L78-L92】
