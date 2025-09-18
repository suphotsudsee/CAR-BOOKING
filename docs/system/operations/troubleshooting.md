# Troubleshooting & Maintenance

## Common Issues

### API fails to start: `Directory 'uploads' does not exist`
Create the `uploads/` directory (or mount a persistent volume) before booting the backend; FastAPI mounts it for static file serving at `/static` during application startup.【F:backend/app/core/config.py†L29-L41】【F:backend/app/main.py†L21-L88】

### Database connection errors
- **Symptom:** `sqlalchemy.exc.OperationalError` or `Can't connect to MySQL server`.
- **Resolution:** Ensure MariaDB credentials in `DATABASE_URL` match the Compose secrets and that the database container is healthy. Run `docker compose ps db` and `docker compose logs db` for diagnostics.【F:docker-compose.yml†L24-L52】【F:backend/.env.example†L7-L19】

### Stale migrations or schema drift
- **Symptom:** Alembic raises `Target database is not up to date` or tables are missing columns.
- **Resolution:** Execute `alembic upgrade head` inside the backend container and verify that `DATABASE_URL` matches the live environment. Alembic is already configured for async engines and metadata autoloading.【F:backend/alembic/env.py†L46-L104】

### Authentication keeps expiring
Adjust `ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS` to align with organisational policies. Remember to redeploy backend containers so the new settings propagate.【F:backend/.env.example†L4-L16】【F:backend/app/core/config.py†L13-L41】

### Notifications not delivered
- Verify Redis availability for background tasks and notification queues.【F:docker-compose.yml†L53-L61】【F:backend/app/core/config.py†L39-L47】
- Confirm users have enabled the relevant channels (email, LINE) in their notification preferences before expecting multi-channel delivery.【F:backend/app/models/notification.py†L1-L48】

## Routine Maintenance

| Task | Frequency | Notes |
|------|-----------|-------|
| Rotate `SECRET_KEY`, database, and LINE tokens | Quarterly or when compromised | Update Compose environment files and restart containers.【F:backend/.env.example†L4-L31】 |
| Review audit logs and system health records | Weekly | Fetch via `/api/v1/system/audit` and `/api/v1/system/health` endpoints to monitor anomalies.【F:backend/app/api/api_v1/endpoints/system.py†L1-L200】 |
| Clear expired uploads and archive documents | Monthly | Files live under `uploads/` and are referenced by vehicle/expense records—keep retention policies in sync with compliance.【F:backend/app/models/vehicle.py†L1-L64】【F:backend/app/models/job_run.py†L1-L80】 |
| Validate backup restore procedures | Monthly | MariaDB backups are mounted via `backups` volume; run test restores to ensure data integrity.【F:docker-compose.prod.yml†L24-L63】 |
| Dependency updates | Quarterly | Rebuild containers to pick up security patches (`pip install -r requirements.txt`, `npm install`). Monitor FastAPI/Next.js release notes for breaking changes.【F:backend/requirements.txt†L1-L52】【F:frontend/package.json†L1-L80】 |

## Support Checklist
When escalating to engineering:
1. Capture relevant container logs (`docker compose logs <service>`).
2. Note the API endpoint, user role, and request payload if applicable.
3. Include timestamps and correlation IDs from audit logs for traceability.【F:backend/app/api/api_v1/endpoints/system.py†L120-L200】
