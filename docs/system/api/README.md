# API Documentation Guide

## Overview
The Office Vehicle Booking System backend exposes a FastAPI-powered REST API. An up-to-date OpenAPI 3.1 specification is generated directly from the application and stored at `docs/system/api/openapi.json` for reference and import into tooling such as Swagger UI, Postman, or Stoplight.【F:docs/system/api/openapi.json†L1-L30】 When the backend runs in debug mode, interactive Swagger and ReDoc explorers are automatically available under `/docs` and `/redoc` respectively.【F:backend/app/main.py†L21-L88】

## Getting Started
1. **Run the stack locally** using Docker Compose: `docker-compose up -d --build`. This starts the FastAPI backend on port 8000 with dependencies (MariaDB, Redis) plus the Next.js frontend.【F:docker-compose.yml†L1-L56】
2. **Access the Swagger UI** at `http://localhost:8000/docs` (development mode only). The UI renders directly from the OpenAPI document and supports live requests with Bearer authentication.【F:backend/app/main.py†L21-L88】
3. **Download the specification** if you prefer external tooling: `curl http://localhost:8000/api/v1/openapi.json -o openapi.json` while the backend is running.

## Authentication & Authorisation
- JWT bearer tokens are issued via `/api/v1/auth/login` and refreshed through `/api/v1/auth/refresh`. Tokens embed the user role (`requester`, `manager`, `fleet_admin`, `driver`, or `auditor`) and expire according to `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15 minutes).【F:backend/app/api/api_v1/endpoints/auth.py†L64-L166】【F:backend/app/models/user.py†L11-L33】【F:backend/app/core/config.py†L13-L47】
- All protected routes rely on role-based dependencies. For example, booking management operations require manager or fleet admin roles while personal booking history is available to the requester role.【F:backend/app/api/api_v1/endpoints/bookings.py†L1-L190】
- Use the `Authorize` button in Swagger UI to provide the `access_token` returned from `/auth/login`. The refresh token must be stored client-side and exchanged via `/auth/refresh` when the access token nears expiry.【F:backend/app/api/api_v1/endpoints/auth.py†L64-L166】

## Pagination, Filtering & Sorting
Most list endpoints support cursor-free pagination via `skip` and `limit` query parameters, constrained by `DEFAULT_PAGE_SIZE` (20) and `MAX_PAGE_SIZE` (100). Additional filters include status enums, date ranges, and search strings, mirroring the FastAPI endpoint signatures. Consult the `parameters` section of the OpenAPI document for precise names and validation rules.【F:docs/system/api/openapi.json†L1-L30】【F:backend/app/api/api_v1/endpoints/bookings.py†L91-L157】【F:backend/app/core/config.py†L52-L59】

## WebSocket Notifications
Real-time updates—such as booking approvals—stream over the `/ws/notifications` WebSocket. Clients must supply a valid access token (`token=<JWT>`) during connection; the server validates the token before joining the notification broadcaster.【F:backend/app/main.py†L94-L128】 Notification payload schemas are documented under `NotificationRead` and related models in the OpenAPI file.【F:docs/system/api/openapi.json†L1-L30】

## Error Handling
The API returns RFC 7807-compliant JSON error bodies with informative `detail` messages produced by FastAPI’s exception handlers. Common status codes include:
- `400 Bad Request` for validation issues (e.g., overlapping booking windows).【F:backend/app/api/api_v1/endpoints/bookings.py†L60-L124】
- `401 Unauthorized` for bad credentials or invalid tokens.【F:backend/app/api/api_v1/endpoints/auth.py†L64-L148】
- `403 Forbidden` when role checks fail.【F:backend/app/api/api_v1/endpoints/bookings.py†L157-L189】
- `404 Not Found` for missing resources across bookings, users, drivers, or vehicles.【F:backend/app/api/api_v1/endpoints/bookings.py†L125-L189】【F:backend/app/api/api_v1/endpoints/users.py†L160-L188】 Use the `responses` section of each endpoint in the OpenAPI document for exhaustive mappings.

## Change Management
Regenerate `openapi.json` whenever the backend changes by running:
```bash
python - <<'PY'
import json, pathlib, sys
sys.path.append('backend')
from app.main import app
pathlib.Path('docs/system/api/openapi.json').write_text(json.dumps(app.openapi(), indent=2, sort_keys=True))
PY
```
Commit the updated specification together with code changes to keep documentation in sync with the API surface.【F:docs/system/api/openapi.json†L1-L30】
