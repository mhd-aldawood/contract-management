# Contract Management

Vue 3 frontend, Django REST Framework backend, PostgreSQL, and Nginx, deployed
as one Docker Compose application.

The deployment follows the same single-gateway pattern as the school project.
The application Nginx routes by public hostname: `cm-dev.svuonline.edu.sy` is
the Vue dashboard and `cmapi-dev.svuonline.edu.sy` is the Django API. Public
DNS, TLS, and the host-level Nginx virtual hosts remain owned by DevOps.

## Latest deployment update — 2026-10-11

The deployment configuration was simplified and hardened to match the school
project's operating model:

- The repository contains only one application Nginx gateway.
- The earlier public two-subdomain Nginx example was removed to avoid
  duplicating DevOps-owned TLS and domain configuration.
- Both DevOps subdomains forward requests unchanged to `127.0.0.1:81`,
  including the original `Host` header.
- The gateway sends every request on `cmapi-dev.svuonline.edu.sy` to Django and
  every request on `cm-dev.svuonline.edu.sy` to Vue.
- The default `localhost` virtual host keeps path-based `/api/` and `/admin/`
  routing for simple local diagnostics.
- Browser security headers are emitted once by the application gateway;
  duplicate upstream values are removed.
- CORS and preflight handling remain exclusively in Django.
- Credentialed CORS is disabled because the frontend uses token authentication,
  not cross-origin cookies.
- Docker-published ports bind to loopback by default.
- The gateway preserves the original HTTPS scheme, public host, client IP, and
  forwarding chain from the DevOps proxy.

## What was implemented

- A unified response contract for every Django REST API.
- A global DRF renderer that normalizes responses automatically.
- Unified authentication, validation, permission, not-found, throttling, and
  server-error responses.
- Arabic and English API messages selected by `Accept-Language`.
- Unified signup, login, logout, current-user, and token-refresh responses.
- Unified educational-content, lifelong-learning, Nafath Center, and other
  agreement responses.
- Pagination metadata: `totalCount`, `page`, and `pageSize`.
- A centralized Vue API response mapper and structured API errors.
- Frontend propagation of `Accept-Language`.
- Postman mappings for tokens and entity IDs inside `response.data`.
- API response, authentication, validation, upload, and renderer tests.
- PostgreSQL, media, static, and log persistence through Docker volumes.
- Health checks for the backend, frontend, PostgreSQL, and gateway.
- Loopback-only published Docker ports.
- One Nginx gateway listening on container port `81`.
- Forwarded HTTPS/host preservation for operation behind the DevOps proxy.
- Security headers applied once at the application gateway.

## Architecture

```text
cm-dev.svuonline.edu.sy ─────┐
                             ├─ DevOps Nginx/TLS ─> 127.0.0.1:81
cmapi-dev.svuonline.edu.sy ──┘                           │
                                                        ▼
                                           Application Nginx gateway
                                            ├─ cm-dev host ───> Vue :80
                                            └─ cmapi-dev host ─> Django :8000
```

Both public subdomains forward requests unchanged to the same application
gateway. The gateway distinguishes them using the original HTTP `Host` header.
DevOps must preserve that header and must not remove or duplicate `/api`.

## Project structure

| Path | Purpose |
| --- | --- |
| `backend/` | Django API, Gunicorn, migrations, message catalogs, and tests |
| `frontend/` | Vue/Vite application and its static-file Nginx image |
| `nginx/nginx.conf` | The single application gateway configuration |
| `postman/` | Postman collection and local environment |
| `.env.example` | Local environment template |
| `.env.production.example` | Production environment template |
| `docker-compose.yml` | Complete container stack |

## Unified API response

Success:

```json
{
  "status": "SUCCESS",
  "code": "agreement.life_long.created",
  "message": "تم حفظ اتفاقية التعلم مدى الحياة بنجاح",
  "data": {},
  "totalCount": 1,
  "page": 1,
  "pageSize": 1
}
```

Failure:

```json
{
  "status": "FAILURE",
  "code": "request.validation_failed",
  "message": "تعذر الحفظ. يرجى مراجعة الحقول المدخلة",
  "data": null,
  "totalCount": 0,
  "page": 1,
  "pageSize": 10,
  "errors": {
    "name": ["This field is required."]
  }
}
```

`errors` is present when field or exception details are available. Backend
messages live in:

- `backend/contract/messages/ar.json`
- `backend/contract/messages/en.json`

The frontend displays `message` and consumes the actual payload from `data`.

## Security and CORS ownership

Each concern has one owner:

| Concern | Owner |
| --- | --- |
| API CORS and preflight | Django `django-cors-headers` |
| Allowed host and CSRF origin validation | Django |
| Response hardening headers | Application Nginx gateway |
| TLS certificates, HTTP-to-HTTPS redirect, and HSTS | DevOps edge Nginx |
| API response format and error mapping | Django REST Framework |

The application gateway sends:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- A limited CSP for `base-uri`, `frame-ancestors`, and `object-src`
- A permissions policy disabling camera, geolocation, and microphone

These headers are not CORS. They protect MIME handling, framing, referrer
privacy, document embedding, and unused browser capabilities. Do not add
`Access-Control-Allow-Origin: *` in Nginx. Django returns the correct CORS
headers only for configured browser origins.

HSTS belongs at the TLS-terminating DevOps Nginx, not inside the application
container. Enable it only after HTTPS works correctly.

## Local development

Prerequisites:

- Docker Engine or Docker Desktop
- Docker Compose v2

Create the environment and replace all placeholder secrets:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Default local addresses:

| Service | Address |
| --- | --- |
| Complete application | `http://localhost:81` |
| Gateway health | `http://localhost:81/healthz` |
| Django diagnostic port | `http://localhost:8000` |
| Vue diagnostic port | `http://localhost:8081` |
| pgAdmin | `http://localhost:5050` |
| PostgreSQL | `localhost:5432` |

Published ports bind to `127.0.0.1` by default.

For a browser test that mirrors the two production subdomains, use:

| Service | Local test address |
| --- | --- |
| Dashboard | `http://cm.localhost:81` |
| Django API | `http://cmapi.localhost:81` |
| Django admin | `http://cmapi.localhost:81/admin/` |
| Gateway health | `http://cmapi.localhost:81/healthz` |

Modern browsers resolve `*.localhost` to the local computer, so no Windows
hosts-file change is normally required. The local `.env.example` builds the
dashboard with `VITE_API_BASE_URL=http://cmapi.localhost:81`.

Each `server_name` line contains two independent aliases. For example,
`cmapi-dev.svuonline.edu.sy` is the real production API hostname, while
`cmapi.localhost` is only its local testing alias. The names are not parent and
subdomain variants, and `.localhost` is never used in production.

Useful commands:

```bash
docker compose logs -f nginx backend frontend
docker compose restart backend
docker compose down
```

`docker compose down` preserves named volumes. Never run
`docker compose down -v` in production unless permanent data deletion is
explicitly intended.

## Production launch

The deployment uses `cm-dev.svuonline.edu.sy` for the dashboard and
`cmapi-dev.svuonline.edu.sy` for the Django API.

### 1. Prepare the environment

```bash
cp .env.production.example .env
chmod 600 .env
```

Replace every `CHANGE_ME...` value.

Required domain settings:

```dotenv
BIND_ADDRESS=127.0.0.1
APP_PORT=81
DEBUG=False

ALLOWED_HOSTS=cm-dev.svuonline.edu.sy,cmapi-dev.svuonline.edu.sy,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://cm-dev.svuonline.edu.sy,https://cmapi-dev.svuonline.edu.sy
CORS_ALLOWED_ORIGINS=https://cm-dev.svuonline.edu.sy
CORS_ALLOW_CREDENTIALS=False

VITE_API_BASE_URL=https://cmapi-dev.svuonline.edu.sy
```

Why the CORS list contains only the frontend: the frontend is the separate
browser origin calling the API. Requests originating from the API domain itself
are same-origin and do not need CORS permission.

Credentialed CORS is disabled because the frontend authenticates with an
explicit token header, not cross-origin session cookies. Enable it only if a
future browser flow genuinely requires cross-origin cookies.

`VITE_API_BASE_URL` must not end with `/` and must not include `/api`; the
frontend appends `/api/...`. It is a build-time value, so changing it requires a
frontend rebuild.

Generate secrets with a secure generator, for example:

```bash
openssl rand -base64 48
```

Never commit the real `.env` file.

### 2. Build and start

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

The backend startup performs the Django system check, migrations, and static
collection before starting Gunicorn.

Verify the application gateway:

```bash
curl -fsS http://127.0.0.1:81/healthz
```

Expected output:

```text
ok
```

### 3. DevOps reverse-proxy contract

The repository intentionally does not contain public-domain Nginx virtual hosts
or certificate paths. DevOps already owns those configurations.

In both public subdomain virtual hosts, forward requests unchanged to:

```text
http://127.0.0.1:81
```

The shared proxy location is:

```nginx
location / {
    proxy_pass http://127.0.0.1:81;
    proxy_http_version 1.1;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;

    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    client_max_body_size 20M;
}
```

DevOps should attach this location to the existing TLS server blocks for both
subdomains. `proxy_set_header Host $host` is required because the application
gateway uses it to select Django or Vue. There is no second application Nginx
configuration to install.

At the TLS edge, DevOps should also configure:

- HTTP-to-HTTPS redirect.
- Certificate renewal monitoring.
- `Strict-Transport-Security` after HTTPS verification.
- Public firewall access only to ports `80` and `443`.

Port `81` remains loopback-only. If the DevOps Nginx runs on a different host,
bind `APP_PORT` to the server's private interface instead and restrict that port
to the proxy server at the firewall.

### 4. Verify production

#### Dashboard URLs

| URL | Expected result |
| --- | --- |
| `https://cm-dev.svuonline.edu.sy/` | Vue application; redirects inside the SPA to signup |
| `https://cm-dev.svuonline.edu.sy/health` | `200 OK` with `OK` |
| `https://cm-dev.svuonline.edu.sy/signup` | Signup page |
| `https://cm-dev.svuonline.edu.sy/login` | Login page |
| `https://cm-dev.svuonline.edu.sy/home` | Authenticated home page or login redirect |
| `https://cm-dev.svuonline.edu.sy/planning` | Agreements planning page |
| `https://cm-dev.svuonline.edu.sy/contracts/educational-content` | Educational-content page |
| `https://cm-dev.svuonline.edu.sy/contracts/nafath-centers` | Nafath Centers page |
| `https://cm-dev.svuonline.edu.sy/contracts/lifelong-learning` | Lifelong-learning page |
| `https://cm-dev.svuonline.edu.sy/contracts/memorandum` | Memorandum page |
| `https://cm-dev.svuonline.edu.sy/contracts/other-agreements` | Other-agreements page |

#### API URLs

| Method | URL | Purpose |
| --- | --- | --- |
| GET | `https://cmapi-dev.svuonline.edu.sy/healthz` | Nginx/API-host health check |
| GET | `https://cmapi-dev.svuonline.edu.sy/admin/` | Django administration login |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/signup/` | Create account |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/login/` | Login and obtain token |
| GET | `https://cmapi-dev.svuonline.edu.sy/api/auth/me/` | Current authenticated user |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/token/refresh/` | Rotate authenticated token |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/logout/` | Invalidate token |
| GET, POST | `https://cmapi-dev.svuonline.edu.sy/api/educational-contents` | List or create educational content |
| GET, PUT, PATCH, DELETE | `https://cmapi-dev.svuonline.edu.sy/api/educational-contents/{id}/` | Read or modify one educational-content record |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/educational-contents/upload/` | Upload educational-content files |
| GET | `https://cmapi-dev.svuonline.edu.sy/api/nafath-center/` | List Nafath Center agreements |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/nafath-center/create` | Create a Nafath Center agreement |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/life-long/create` | Create a lifelong-learning agreement |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/other-agreement/create` | Create another agreement type |

Opening `https://cmapi-dev.svuonline.edu.sy/` itself may return Django `404`
because the backend intentionally has no root route. That confirms the hostname
reached Django rather than Vue; use `/healthz`, `/admin/`, or `/api/...` for a
functional test.

Quick smoke test:

```bash
curl -fsS https://cm-dev.svuonline.edu.sy/health
curl -fsS https://cmapi-dev.svuonline.edu.sy/healthz
```

Verify a unified validation error:

```bash
curl -i \
  -H 'Accept-Language: en' \
  -H 'Content-Type: application/json' \
  -d '{}' \
  https://cmapi-dev.svuonline.edu.sy/api/auth/login/
```

Expected result: HTTP `400` with a JSON `FAILURE` envelope, not an HTML proxy
error.

Finally, open the frontend and confirm in browser Developer Tools that requests
go to `https://cmapi-dev.svuonline.edu.sy/api/...` without CORS or mixed-content
errors.

## Environment reference

| Variable | Purpose |
| --- | --- |
| `BIND_ADDRESS` | Address used for published Docker ports |
| `APP_PORT` | Host port mapped to application gateway port `81` |
| `BACKEND_PORT` | Loopback Django diagnostic port |
| `FRONTEND_PORT` | Loopback Vue diagnostic port |
| `POSTGRES_EXPOSED_PORT` | Loopback PostgreSQL diagnostic port |
| `PGADMIN_PORT` | Loopback pgAdmin port |
| `SECRET_KEY` | Django cryptographic secret |
| `DEBUG` | Must be `False` in production |
| `ALLOWED_HOSTS` | Comma-separated public hosts accepted by Django |
| `CSRF_TRUSTED_ORIGINS` | Trusted full origins, including `https://` |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed to read API responses |
| `CORS_ALLOW_CREDENTIALS` | Whether cross-origin cookies are allowed; normally `False` |
| `API_DEFAULT_LANGUAGE` | Fallback API language: `ar` or `en` |
| `VITE_API_BASE_URL` | API origin without `/api` or trailing slash |
| `POSTGRES_*` | PostgreSQL connection and credentials |
| `GUNICORN_WORKERS` | Gunicorn worker count |
| `GUNICORN_TIMEOUT` | Gunicorn timeout in seconds |

## Updating production

```bash
docker compose up --build -d
docker compose ps
curl -fsS http://127.0.0.1:81/healthz
docker compose logs --tail=200 nginx backend frontend postgres
```

## Database backup

Create a backup before major upgrades:

```bash
mkdir -p backups
docker compose exec -T postgres sh -c \
  'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "backups/contract-management-$(date +%F-%H%M%S).sql"
```

Store backups outside the application server according to the organization's
retention policy.

## Tests and build

Django tests use an isolated SQLite database:

```bash
docker compose run --rm --entrypoint python backend manage.py test contract
```

Frontend build:

```bash
cd frontend
npm ci
npm run build
```

## Postman

Import:

- `postman/contract-management.postman_collection.json`
- `postman/contract-management.local.postman_environment.json`
- `postman/contract-management.production.postman_environment.json`

Select exactly one environment before running the collection. The local
environment uses `cm.localhost:81` and `cmapi.localhost:81`; the production
environment uses the two HTTPS SVU hostnames. The collection's service checks
always pass through the Nginx gateway—none use the containers' diagnostic ports.
Signup and Login store the token from `response.data.token`.

## Troubleshooting

### 502 from DevOps Nginx

```bash
curl -v http://127.0.0.1:81/healthz
docker compose ps
docker compose logs --tail=200 nginx backend frontend
```

Confirm the proxy target and `APP_PORT` are identical.

### Django `DisallowedHost`

Add both public domains to `ALLOWED_HOSTS`, then recreate the backend:

```bash
docker compose up -d --force-recreate backend
```

### Browser CORS failure

Add the exact frontend origin, including `https://`, to
`CORS_ALLOWED_ORIGINS`. Do not solve this by adding wildcard CORS headers in
Nginx.

### Frontend calls the wrong API

Correct `VITE_API_BASE_URL`, then rebuild the frontend:

```bash
docker compose build --no-cache frontend
docker compose up -d frontend nginx
```

### Django sees HTTP instead of HTTPS

Confirm the DevOps proxy forwards `X-Forwarded-Proto`. The application gateway
preserves that header and Django trusts it through `SECURE_PROXY_SSL_HEADER`.

### Upload returns HTTP 413

The DevOps proxy, application gateway, and Django must use the same upload size
limit. The current project limit is `20 MB`.

## Production security checklist

- Keep `.env` readable only by the deployment account.
- Use separate strong secrets for Django, PostgreSQL, and pgAdmin.
- Keep `DEBUG=False`.
- Expose only ports `80` and `443` publicly.
- Keep application ports bound to loopback/private interfaces.
- Do not expose pgAdmin publicly; use an SSH tunnel when required.
- Monitor certificate renewal and container health.
- Back up PostgreSQL and uploaded media.
- Review backend and proxy logs after deployments.
