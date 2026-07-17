# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

No test runner, linter, or formatter is configured yet. The project runs entirely via Docker Compose.

```bash
# Start all services (production mode)
docker compose up -d --build

# Start with hot-reload for development (mounts local code, enables uvicorn --reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Start frontend dev server (separate terminal, runs on port 3000)
cd frontend && npm run dev

# Build frontend for production
cd frontend && npm run build

# View logs for a specific service
docker compose logs -f event_service

# Restart a single service after code changes (without dev mode)
docker compose up -d --build event_service

# Access Kafka UI (monitor topics/messages)
open http://localhost:8080
```

## Architecture

This is an **async microservices platform** for location-based event discovery ("События на карте" — Events on a Map). Four FastAPI services communicate via Kafka (async events) and synchronous HTTP (auth verification). The frontend is a React SPA served by Vite (dev) or Nginx (production). Nginx routes external traffic by URL prefix to the appropriate service.

### Frontend

React 18 SPA with Vite, Tailwind CSS 3, and Yandex Maps JS API 2.1. Located in `frontend/`.

| File | Role |
|---|---|
| `src/App.jsx` | Root: shows AuthPage or MapPage depending on auth state |
| `src/api/client.js` | Fetch wrapper: auto-attaches JWT Bearer token, refreshes on 401, provides `login()`, `register()`, `createEvent()`, `getNearbyEvents()`, `joinEvent()`, `getConfig()` |
| `src/hooks/useAuth.jsx` | Auth context/provider: stores JWT in localStorage, exposes `user`, `loading`, `logout`, `setAuth()` |
| `src/hooks/useMap.jsx` | Yandex Maps lifecycle: loads API key from `GET /api/v1/config`, initializes map, manages markers, reverse geocoding |
| `src/components/AuthPage.jsx` | Login/register form with tab switch |
| `src/components/MapPage.jsx` | Main layout: header + full-screen map + modals |
| `src/components/MapContainer.jsx` | Yandex Map: click → temp marker, debounced reload of nearby events, colored markers by category |
| `src/components/EventForm.jsx` | Event creation modal: title, description, category, address, start/end time, max participants |
| `src/components/EventPopup.jsx` | Event detail popup with join button |
| `src/utils/categories.js` | Category enum → Russian labels + marker colors |

**Auth flow:** Login/register → JWT in localStorage → auto-attached to API requests → 401 triggers token refresh via `/auth/refresh` → on failure clears tokens and reloads.

**Map flow:** Click map → red temp marker → reverse geocode address → EventForm opens → submit → `POST /api/v1/events` → marker becomes permanent.

**CORS:** Frontend dev runs on `localhost:3000`, backend CORS allows this origin via `ALLOWED_ORIGINS` env var (JSON array). In production, Nginx serves both frontend and API from the same origin, so no CORS needed.

### Service Responsibilities

| Service | Port (internal) | Database | Role |
|---|---|---|---|
| `auth_service` | 8000 | `postgres_auth/auth_db` | User registration, login, JWT issuance/verification |
| `event_service` | 8000 | `postgres_events/events_db` | Event CRUD, geo-search, join/leave, comments |
| `user_service` | 8000 | `postgres_auth/auth_db` (shared) | User profiles (bio, avatar, location) |
| `notification_service` | 8000 | None (Kafka-only) | Listens to Kafka events, sends email/push |

### Inter-Service Communication

**Synchronous (HTTP):** `event_service` and `user_service` verify JWT tokens by calling `GET /api/v1/auth/verify` on `auth_service` via `httpx`. This happens in their `get_current_user` dependency ([dependencies.py](services/event_service/app/core/dependencies.py)).

**Asynchronous (Kafka):** Services emit domain events to Kafka topics defined in [shared/kafka_topics.py](shared/kafka_topics.py). `notification_service` and `event_service` consume these:
- `auth_service` → produces `user.registered` on signup
- `event_service` → produces `event.created`, `event.updated`, `user.joined`, `user.left`, `comment.created`; consumes `user.registered` and `user.updated` (to track user info)
- `notification_service` → consumes `user.registered`, `event.created`, `user.joined`, `comment.created` to send emails

### Internal Service Structure

Each service follows the same FastAPI layout:
- `app/main.py` — FastAPI app with `lifespan` hook: creates DB tables on startup, initializes Kafka producer/consumer, cleans up on shutdown
- `app/api/v1/` — route definitions (thin, delegate to service layer)
- `app/services/` — business logic (AuthService, EventService, UserService)
- `app/models/` — SQLAlchemy ORM models (DeclarativeBase)
- `app/schemas/` — Pydantic request/response models
- `app/db/session.py` — async SQLAlchemy engine + `get_db` dependency (async_sessionmaker, `expire_on_commit=False`)
- `app/db/base.py` — shared `Base` class for models
- `app/core/config.py` — plain class reading `os.getenv` (no Pydantic Settings)
- `app/core/dependencies.py` — `get_current_user` (JWT verification via auth service HTTP call)
- `app/kafka/` — Kafka producer/consumer wrappers using `aiokafka`

### Key Architectural Details

- **Dual DB approach:** `auth_db` holds `users` + `user_profiles`; `events_db` holds `events`, `event_participants`, `comments`. This means the user and event services operate on separate databases.
- **Geo-search in event_service:** Two-phase filtering — first a bounding-box query on indexed lat/lon columns (`idx_events_location`), then Haversine distance calculation in Python for accurate radius filtering. See [geo_service.py](services/event_service/app/services/geo_service.py).
- **Kafka producers** use `acks="all"` and `send_and_wait` — synchronous acknowledgment from all replicas.
- **Auth tokens:** JWT with HS256. Access tokens expire in 30 min, refresh tokens in 7 days. Token type is encoded in the JWT payload (`"type": "access"` or `"type": "refresh"`).
- **Shared code** in `shared/` is mounted into each service container (dev mode) or copied (production Dockerfile copies entire context). Contains Kafka topic constants and a `TimestampMixin` for SQLAlchemy `created_at`/`updated_at` columns.
- **Nginx** rate-limits API routes (100 req/min burst 20 for auth/users, burst 50 for events) and proxies WebSocket connections under `/ws/` to `event_service`.

### Infrastructure (docker-compose.yml)

- **PostgreSQL 15** × 2 (`postgres_auth`, `postgres_events`)
- **Redis 7** (shared, 4 logical DBs via URL path: `/0` auth, `/1` events, `/2` users, `/3` notifications — currently not actively used in application logic)
- **Kafka** (Confluent 7.5.0) + **Zookeeper** — Kafka UI available at port 8080
- **Nginx** (entry point on ports 80/443)
