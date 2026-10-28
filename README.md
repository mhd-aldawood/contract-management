# Contract Management

Vue 3 frontend, Django REST Framework backend, PostgreSQL, and Nginx, deployed
as one Docker Compose application.

For account usernames, generated passwords, demo-data seeding and role-by-role test steps, see [Prepare a shared test environment](#prepare-a-shared-test-environment).

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
- Docker-published ports use Compose's default host-interface binding, matching
  the school project; the production firewall controls external access.
- The gateway preserves the original HTTPS scheme, public host, client IP, and
  forwarding chain from the DevOps proxy.

## What was implemented

- A unified response contract for every Django REST API.
- A global DRF renderer that normalizes responses automatically.
- Unified authentication, validation, permission, not-found, throttling, and
  server-error responses.
- Arabic and English API messages selected by `Accept-Language`.
- Unified login, logout, current-user, password-change, and token-refresh responses.
- Unified educational-content, lifelong-learning, Nafath Center, and other
  agreement responses.
- Pagination metadata: `totalCount`, `page`, and `pageSize`.
- A centralized Vue API response mapper and structured API errors.
- Frontend propagation of `Accept-Language`.
- Postman mappings for tokens and entity IDs inside `response.data`.
- API response, authentication, validation, upload, and renderer tests.
- PostgreSQL, media, static, and log persistence through Docker volumes.
- Health checks for the backend, frontend, PostgreSQL, and gateway.
- Fixed Docker-published ports matching the documented service addresses.
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

Published ports use Compose's default all-interface binding. Restrict production
access with the host firewall.

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
DEBUG=False

ALLOWED_HOSTS=cm-dev.svuonline.edu.sy,cmapi-dev.svuonline.edu.sy,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://cm-dev.svuonline.edu.sy,https://cmapi-dev.svuonline.edu.sy
CORS_ALLOWED_ORIGINS=https://cm-dev.svuonline.edu.sy

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

### GitLab CI/CD

The `master` branch pipeline uses the same `validate`, `preflight`, and `deploy`
stages as the school-management pipeline. It builds and pushes only images whose
source changed:

- `backend/**` builds and deploys only `cm_backend`.
- `frontend/**` builds and deploys only `cm_frontend`.
- `nginx/**` recreates only `cm_nginx`.
- `docker-compose.yml` performs a controlled full Compose update.

After a frontend or backend container is replaced, the pipeline restarts
`cm_nginx` so it resolves the new Docker container address. It does not recreate
PostgreSQL, pgAdmin, or the unaffected application container. Docker Compose
remains the source of truth for service names, build contexts, and containers.
Harbor uses one repository, `svu-cm-dev/contract-management`, with separate
`backend-<commit>` and `frontend-<commit>` tags. These deployment artifacts are
tagged to the local image names derived from the Compose project; registry
details are not added to the Compose file. All pipeline and remote deployment logic is contained in
`.gitlab-ci.yml`; there is no second CI deployment script to configure.

Configure these protected and masked GitLab CI/CD variables:

```text
REGISTRY_PASSWORD
SSH_PRIVATE_KEY_B64
```

The deployment server must already contain `/home/deployer/contract-fe/.env`.
The pipeline never copies production secrets from the repository.
`VITE_API_BASE_URL` is supplied during the frontend image build and defaults to
`https://cmapi-dev.svuonline.edu.sy` in the pipeline.

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

Port `81` is published on the server interfaces, matching the school project.
Restrict it to the native DevOps Nginx host with the server firewall; do not
allow public access to application ports.

### 4. Verify production

#### Dashboard URLs

| URL | Expected result |
| --- | --- |
| `https://cm-dev.svuonline.edu.sy/` | Vue application; redirects inside the SPA to login |
| `https://cm-dev.svuonline.edu.sy/health` | `200 OK` with `OK` |
| `https://cm-dev.svuonline.edu.sy/login` | Login page |
| `https://cm-dev.svuonline.edu.sy/change-password` | Required temporary-password change page |
| `https://cm-dev.svuonline.edu.sy/home` | Authenticated home page or login redirect |
| `https://cm-dev.svuonline.edu.sy/planning` | Agreements planning page |
| `https://cm-dev.svuonline.edu.sy/contracts/educational-content` | Educational-content page |
| `https://cm-dev.svuonline.edu.sy/contracts/nafath-centers` | Nafath Centers page |
| `https://cm-dev.svuonline.edu.sy/contracts/lifelong-learning` | Lifelong-learning page |
| `https://cm-dev.svuonline.edu.sy/contracts/memorandum` | Memorandum page |
| `https://cm-dev.svuonline.edu.sy/contracts/other-agreements` | Other-agreements page |
| `https://cm-dev.svuonline.edu.sy/admin/roles` | Admin-only account, role, and permission management |
| `https://cm-dev.svuonline.edu.sy/admin/users` | Admin-only user lifecycle management |

#### API URLs

| Method | URL | Purpose |
| --- | --- | --- |
| GET | `https://cmapi-dev.svuonline.edu.sy/healthz` | Nginx/API-host health check |
| GET | `https://cmapi-dev.svuonline.edu.sy/admin/` | Django administration login |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/login/` | Login and obtain token |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/change-password/` | Change temporary or current password |
| GET, POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/users/` | Admin-only list/filter or create users |
| PATCH | `https://cmapi-dev.svuonline.edu.sy/api/auth/users/{id}/` | Admin-only update, activate/deactivate, role assignment, or password reset |
| GET | `https://cmapi-dev.svuonline.edu.sy/api/auth/me/` | Current authenticated user |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/token/refresh/` | Rotate access token using refresh cookie + CSRF header |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/auth/logout/` | Revoke the current login session and clear its cookies |
| GET, POST, PATCH, DELETE | `https://cmapi-dev.svuonline.edu.sy/api/auth/access-control/` | Admin-only role and permission management |
| GET, POST | `https://cmapi-dev.svuonline.edu.sy/api/educational-contents` | List or create educational content |
| GET, PUT, PATCH, DELETE | `https://cmapi-dev.svuonline.edu.sy/api/educational-contents/{id}/` | Read or modify one educational-content record |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/educational-contents/upload/` | Upload educational-content files |
| GET | `https://cmapi-dev.svuonline.edu.sy/api/nafath-center/` | List Nafath Center agreements |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/nafath-center/create` | Create a Nafath Center agreement |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/life-long/create` | Create a lifelong-learning agreement |
| POST | `https://cmapi-dev.svuonline.edu.sy/api/other-agreement/create` | Create another agreement type |

## Role-based access control

The application seeds these roles idempotently during backend startup: `admin`,
`dean`, `contract`, `planning`, and `finance`. Each application feature has
separate `read` and `write` permissions. Read controls page/list access; write
controls create, update, delete, deactivate, file upload, and form-save actions.

Administrators manage the permission matrix and user-role assignments at:

`http://cm.localhost:81/admin/roles`

The equivalent API is `/api/auth/access-control/` and is restricted
to the Admin role. Set `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` before the first
deployment to bootstrap the initial administrator. Existing non-superusers are
not granted a role automatically and must be assigned one by an administrator.

Public signup is disabled. Administrators create accounts at
`http://cm.localhost:81/admin/users`; the generated temporary password is shown
once. The user is redirected to `/change-password` after the first login and
cannot use protected application features until the password is changed.

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
| `SECRET_KEY` | Django cryptographic secret |
| `DEBUG` | Must be `False` in production |
| `ALLOWED_HOSTS` | Comma-separated public hosts accepted by Django |
| `CSRF_TRUSTED_ORIGINS` | Trusted full origins, including `https://` |
| `CORS_ALLOWED_ORIGINS` | Browser origins allowed to read API responses |
| `FILE_DOWNLOAD_SIGNING_KEY` | Optional independent server secret for download grants; defaults to a key derived from `SECRET_KEY` |
| `API_DEFAULT_LANGUAGE` | Fallback API language: `ar` or `en` |
| `VITE_API_BASE_URL` | API origin without `/api` or trailing slash |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` | PostgreSQL connection and credentials |
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

Django tests default to an isolated SQLite database. For PostgreSQL, including the simultaneous single-use grant regression, run the second command. Both use a separate test database:

```bash
docker compose run --rm --no-deps --entrypoint python backend manage.py test contract --noinput
docker compose run --rm --no-deps -e USE_SQLITE_FOR_TESTS=False --entrypoint python backend manage.py test contract --noinput
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
Login and Refresh return `response.data.token` plus `csrfToken`. Postman saves both in the selected environment; its cookie jar retains the HttpOnly refresh cookie. Run **Get refresh CSRF token** before **Refresh token** if needed. Keep cookie handling enabled.

## Troubleshooting

### 502 from DevOps Nginx

```bash
curl -v http://127.0.0.1:81/healthz
docker compose ps
docker compose logs --tail=200 nginx backend frontend
```

Confirm the proxy target matches the gateway mapping in `docker-compose.yml`.

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

## Role dashboards and local testing

The home page remains **لوحة التحكم**. Its data comes from `GET /api/dashboard/` and is scoped to the signed-in user's features. Admin receives system/user/order summaries, Dean receives agreement review and aggregate user counts, Finance receives order coverage and uploads, Contracts receives agreement/reminder metrics, and Planning receives only agreements visible to Planning. The endpoint never seeds agreement or financial data; an empty database shows zero counts.

To explicitly create local accounts for testing all five built-in roles, run:

```bash
docker compose exec backend python manage.py seed_test_users
```

This optional command creates `cm_demo_admin`, `cm_demo_dean`, `cm_demo_finance`, `cm_demo_contract`, and `cm_demo_planning` with separate random passwords printed once. It preserves existing accounts and passwords on subsequent runs and is never called at startup. Test accounts can open their dashboard immediately; normal accounts created in User Management retain the mandatory first-login password change. No test passwords are stored in the repository.

### Prepare a shared test environment

After pulling the latest `master` into the existing test checkout, rebuild the application and explicitly seed the test database:

```bash
git pull --ff-only origin master
docker compose up -d --build backend frontend
docker compose exec nginx nginx -s reload
docker compose exec backend python manage.py seed_test_users
docker compose exec backend python manage.py seed_demo_data
```

If the environment is deployed by the existing GitLab/Harbor pipeline, wait for its successful backend deployment instead of rebuilding manually. Connect to the test server, change into its deployment directory (for example `/home/deployer/contract-management`), and run only the two `docker compose exec backend ... seed_...` commands. Seeding is deliberately not part of the pipeline or container startup.

Save the passwords printed by `seed_test_users` for that environment. They differ from passwords generated on another PC. Open the environment's login page and use each role account to test **لوحة التحكم**.

#### Accounts and passwords

| Role | Username | Main responsibility |
| --- | --- | --- |
| Admin | `cm_demo_admin` | Manage users, roles and permissions; access all features |
| Dean | `cm_demo_dean` | Review all agreements and Finance orders; control visibility in Planning |
| Finance | `cm_demo_finance` | Upload, edit, replace, download and remove disbursement orders |
| Contracts | `cm_demo_contract` | Add agreements and manage their information and reminders |
| Planning | `cm_demo_planning` | Review visible agreements and filter current, future and finished agreements |

The seed command prints each newly created account as `role username password`. Copy the generated passwords from your own terminal. Passwords are not fixed and are not committed to Git. Existing accounts retain their current passwords; rerunning the command will report `already exists` rather than printing or resetting a password.

If you need to set a new password for an existing test account, run the interactive command below and enter the new password twice. Replace the username to reset another account:

```bash
docker compose exec backend python manage.py changepassword cm_demo_admin
```

#### Run the app and confirm the seed

1. Use the test environment's existing `.env` and database configuration. Start Docker Desktop or the server's Docker service before running Compose.
2. Run the pull, build and seed commands above. The default data seed should report **40 agreements and 60 Finance orders created** on its first run. A repeat run reports skipped examples and preserves tester edits and removed orders.
3. Check services with `docker compose ps`. If the backend is still starting, wait for it to become healthy before opening the app. Check startup problems with `docker compose logs --tail=100 backend`.
4. Locally, open [the login page](http://cm.localhost:81/login). For a shared server, use its configured frontend address, such as [the development login page](https://cm-dev.svuonline.edu.sy/login). Refresh with **Ctrl+F5** after rebuilding.
5. Sign in separately with each account. Use **تسجيل الخروج** before changing roles, or use separate private browser sessions.

#### Test every role

Agreement lists include an **أوامر الصرف** filter (all / with orders / without orders). Beside **عرض التفاصيل**, **عرض أوامر الصرف (N)** opens that agreement's Finance files in a modal; it is disabled for zero active orders. Contract and Planning readers can view related file metadata; downloading additionally requires that page’s Download permission. Hidden agreements remain inaccessible through the Planning viewer. Finance write permissions are still required to add, edit, replace or remove files.

| Account | Dashboard checks | Feature checks |
| --- | --- | --- |
| Admin | Confirm agreement totals, active users, roles, Finance order totals, status/type charts and monthly activity. | Open **إدارة النظام → المستخدمون** and **الأدوار والصلاحيات**. Create a temporary user, assign a role, edit the user and test activation/deactivation. Create a custom role and verify its read/write permissions with that role's user. |
| Dean | Confirm aggregate user counts, hidden agreement counts, current/future/finished charts and Finance coverage. | Open **العميد ومراجعة الاتفاقيات**, select a `DEMO-` agreement, inspect its details and download an order. Hide/show it and confirm the Planning account's list changes after refresh. User management should remain unavailable to Dean. |
| Finance | Confirm total orders, agreements without orders, orders added this month, type distribution, coverage and recent uploads. | Open **المالية وأوامر الصرف**. Select a demo agreement with several orders. Upload a file, edit its name/notes, replace it, download it and remove it. Switch documents and confirm each document shows only its own orders. Refresh the dashboard to see the new counts. |
| Contracts | Confirm agreement totals, agreements added this month, due reminders and upcoming expiration. | Open each agreement type, filter by a `DEMO-` number and review details. Add a new agreement with a reminder date. Check that it appears in that type's list and updates the dashboard. User/role administration and Finance order editing should remain unavailable. |
| Planning | Confirm only agreements visible to Planning contribute to totals and charts. | Open **التخطيط والاتفاقيات**. Filter agreement types and date phases. Current agreements include today; future agreements start after today; finished agreements ended before today. Hidden agreements must not appear. Verify Dean visibility changes after refreshing. User administration and Finance editing should remain unavailable. |

Default demo data, before any tester edits and **in addition to any records already in the database**:

| Metric | Admin / Dean / Finance / Contracts | Planning |
| --- | ---: | ---: |
| Agreements | 40 | 30 visible agreements |
| Current agreements | 20 | 15 |
| Future agreements | 10 | 5 |
| Finished agreements | 10 | 10 |
| Hidden agreements | 10 | 0 |
| Active Finance orders | 60 for Admin, Dean and Finance | Not exposed |
| Agreements with / without Finance orders | 30 / 10 for Admin, Dean and Finance | Not exposed |

The status counts above apply on the day the examples are created; they change as time passes or dates are edited. The six-month chart includes examples in every month. Admin can change role permissions, so customized access can differ from the defaults in this checklist. All demo agreement numbers start with `DEMO-`; names and downloadable text attachments are clearly labeled as test data.

`seed_demo_data` is a CLI management command, not an API or automatic startup task. It creates 8 clearly labeled examples for each of the 5 agreement types (40 agreements), 60 downloadable Finance order files, agreement attachments and payment/clause examples. Dates include current, future and finished agreements; 10 agreements are hidden from Planning. Creation dates span the last six months so dashboard charts contain data. Existing records and edited demo examples are preserved on reruns. Use `--per-type 5` through `--per-type 10` to choose a different number; no records are removed when reducing the count. Run these demo commands against the designated test database.

## Create Contract — إضافة عقد

Open [إضافة عقد locally](http://cm.localhost:81/contracts/create) from the **العقود → إضافة عقد** sidebar entry. This implements the supplied procurement/tender reference with the application's shared colors, typography, panels, buttons, large responsive modals and RTL layout.

Use **إضافة عقد جديد** to enter the justification memo, technical specifications, legal specifications, announcement start/end dates, reminder date, ordered bid-opening minutes (minute number/date/subject), optional wishes, and the successful/failed tender result. Add/remove minutes and wishes dynamically. Blank placeholder minutes are ignored; a partly completed minute must be completed before saving. Dates are calendar dates, and the announcement end cannot precede its start.

The list supports search, status filtering, pagination, details, editing and deletion confirmation. Entries persist in PostgreSQL and survive reloads. The reminder date is saved and displayed, including for failed tenders. Changing the draft status does not immediately destroy entered rows; saving **فشلت المناقصة** clears announcement dates, minutes and wishes on the server while preserving the memo, specifications and reminder. Failed tenders can therefore be saved without announcement dates, correcting the contradictory required-date behavior in the reference. Deletion removes the entry from normal lists/access while retaining it internally as a deleted record.

This is a separate procurement-entry feature, not a new signed-agreement type. Its **contract-requests** permission appears in Roles: Admin/Contracts receive Read/Write; Dean/Planning/Finance receive Read by default. Custom roles need explicit permission. Every API read/write/delete is checked server-side. The reference's specifications fields remain text; no document URLs or client-only browser persistence are introduced.

| Method | API |
| --- | --- |
| GET / POST | `/api/contract-requests/` |
| GET / PATCH / PUT / DELETE | `/api/contract-requests/<id>/` |

List queries accept `q` and `status=success|failed`. Nested `bids` contain `number`, `date` and `subject`; `wishes` is a JSON string array. Requests are JSON, including nested arrays. The Postman **Create Contract - إضافة عقد** folder contains creation, filter, details, update-to-failed, delete and deleted-record checks. Migrations `0018` and `0019` create storage and missing role permissions on backend startup.

The regression suite includes persistence, date/required-field validation, minute/wish limits, transitions between results, filtering without duplicated records, deletion visibility, role restrictions and constant list-query counts. All 115 PostgreSQL tests passed; live desktop/mobile checks covered creation, editing, deletion/retry, filtering and all five roles. The local Postman smoke passed 8 requests and 10 assertions with cloud reporting disabled. `frontend/tests/contract-requests.browser.mjs` tests the live local Docker UI at desktop/phone sizes and all five roles, then removes only its own temporary records. It uses the same temporary credentials-file and Playwright setup documented below.

## Doctoral contracts — عقد الدكتوراه

The sidebar places **عقد الدكتوراه** immediately below **المحتوى التعليمي**. Open [the local doctoral contracts screen](http://cm.localhost:81/contracts/doctoral-contracts), then **إضافة عقد** to open its responsive form. The list supports search, details, Finance-order viewing and CSV export.

Required fields: **رقم العقد، اسم الدكتور، المهام، رتبة الدكتور، مدة العقد، أمر المباشرة**. Rank and duration are free text, for example `أستاذ مساعد` and `سنة دراسية واحدة`. **إرفاق الوثيقة** accepts an optional PDF, Word, image, TXT or Excel document up to 19 MiB. Contract numbers must be unique. Attachments use the existing private, permission-checked, single-use download protocol; storage paths are not exposed.

The new `doctoral-contracts` feature has independent Read, Write and Download permissions in Roles. Defaults: Admin/Contracts can create and update; Dean/Finance/Planning can read and download. Custom roles need an explicit grant. The contract also participates in Planning visibility, Dean review, Finance order management and dashboard type counts. The entered duration remains text; no dates are invented from it. Use **إخفاء العقد عن التخطيط** or the Dean visibility control to hide a contract from Planning.

| Method | API |
| --- | --- |
| GET / POST | `/api/doctoral-contracts/` |
| GET / PATCH / PUT | `/api/doctoral-contracts/<id>/` |
| POST | `/api/files/grants/` with `kind: "doctoral-contracts"` |

JSON creation example (send the file with the same fields as multipart when attaching a document):

```json
{
  "contractNumber": "PHD-001",
  "doctorName": "الدكتور أحمد",
  "tasks": "الإشراف على الرسائل وتدريس المقررات",
  "doctorRank": "أستاذ مساعد",
  "duration": "سنة دراسية واحدة",
  "commencementOrder": "أمر مباشرة رقم 12",
  "isHidden": false
}
```

Rebuild backend/frontend and reload Nginx using the deployment commands below. Startup applies migrations `0016` and `0017`, creates the doctoral-contract table and Finance relation, and seeds missing role permissions without resetting existing permissions. `seed_demo_data` continues to seed its original five agreement types and does not insert doctoral contracts automatically. Postman includes a **Doctoral Contracts** folder with JSON/multipart creation, listing, details, update and protected download requests.

Regression coverage includes required fields, duplicate contract numbers, attachment validation, role restrictions, private downloads, updates, Planning hiding, Dean details, Finance scoping and dashboards. All 105 backend tests passed on local Docker PostgreSQL; the live doctoral browser checks passed at 1440px and 390px and verified access for all five roles. `frontend/tests/doctoral.browser.mjs` uses the temporary credentials file described below to test the live local screen at desktop/phone sizes and all five roles; it removes only its own temporary contracts and documents afterward.

## Planning columns and text/table costs

`/planning` includes **تفاصيل العمل، حالة الاتفاقية، التكلفة، تفاصيل التكلفة، نوع الاتفاقية**, alongside the existing dates, date-based phase and actions. Work details use the saved subject/contract text or agreement clauses. The agreement's saved status is shown separately from its date-based phase; types without a saved status use the phase label. The type column identifies the agreement category.

The existing **نص / جدول** choice controls the cost cell. Text is shown directly; otherwise an available estimated value is formatted, including zero. Selecting Table displays **إظهار الجدول**, opening only that agreement's rows in a responsive modal with **عدد السنوات / النسبة / تفاصيل**. Switching documents never reuses another agreement's rows. CSV export includes the new Planning columns and the selected agreement's actual cost rows.

The entry table now uses those same three columns for all five agreement types. Use **إضافة صف** to add rows and enter a percentage from 0 to 100, with up to two decimal places. Years accepts descriptive text such as `أول 5 سنوات`. Empty/invalid tables cannot be saved; each agreement stores its own rows. This uses the existing text/table choice, without an additional independent selector. Other agreements and memoranda also expose this choice in their Cost section.

API JSON example:

```json
{
  "paymentMethod": "table",
  "costTable": [
    { "years": "أول 5 سنوات", "percentage": "40.00", "details": "حصة الجامعة" },
    { "years": "ثاني 3 سنوات", "percentage": "60.00", "details": "حصة الجهة" }
  ]
}
```

For text, send `paymentMethod: "text"`, `paymentText` and `costTable: []`. Multipart requests send `costTable` as a JSON string. The normal agreement create/read/update endpoints and `GET /api/planning/agreements/` include these fields; the Postman examples are updated. Migration `0015` adds per-agreement storage and preserves existing records. Previously saved `paymentSchedule` rows retain their amounts and due dates: Planning opens them as a clearly labeled legacy payment table, without converting money into percentages. No shared dummy cost data is used.

Regression commands:

```bash
node --test frontend/tests/contractDates.test.js frontend/tests/agreementCosts.test.js
node frontend/tests/planning-costs.browser.mjs
docker compose run --rm --no-deps -e USE_SQLITE_FOR_TESTS=False --entrypoint python backend manage.py test contract --noinput
```

The cost browser regression passed the new columns, text/table selection, isolation between agreements, legacy and empty tables, percentage bounds and multipart submission for all five forms at desktop and phone sizes. A live local-Docker check also created agreements of all five types, saved their cost tables to PostgreSQL and displayed their own rows in Planning; those temporary records were removed afterward. Use the Playwright/Chrome environment variables documented below.

## Download-only files and secure login sessions

Agreement attachments and Finance orders now use **تنزيل** only. Details no longer open raw file links in another tab. API responses return `hasFile` and the original filename instead of a public storage path. All Nginx `/media/` routes and Django direct media access return 404, including old agreement links. Existing uploaded files remain in the media volume.

### Admin configuration

Open **إدارة النظام → الأدوار والصلاحيات** at `/admin/roles`, select a role, and set **قراءة / كتابة / تنزيل** per feature. Read is required for Download; Write and Download are independent. Removing Read removes both other permissions. Download is available for all six document types, Planning, Finance and Dean. The screen containing the action determines its permission: a Planning download uses Planning permissions, for example. Planning cannot download hidden agreements, even by changing the requested scope.

Built-in roles receive Download for file features they could already read during this upgrade. Existing custom roles start without Download until Admin grants it. Admin retains full access. Later `seed_roles` runs preserve configured permissions.

Open **إدارة النظام → الأمان والجلسات** at `/admin/security` to change the central database settings:

| Setting | Default | Allowed values |
| --- | ---: | --- |
| Download grant lifetime | 60 seconds | 5–3600 seconds |
| Access token lifetime | 15 minutes | 1–60 minutes |
| Normal login session | 8 hours | 1–168 hours |
| Remember Me session | 7 days | 1–90 days |
| Allow Remember Me | Enabled | Enabled / disabled |

These durations are configured in this page, not duplicated across `.env`, Docker Compose and Vue. Shorter settings also constrain existing sessions and grants; increasing a setting does not extend an already issued absolute session or grant. Non-admins cannot open or call Security Settings.

### Download protocol

1. With a valid login access token, send JSON to `POST /api/files/grants/`:

   ```json
   {
     "kind": "nafath-centers",
     "agreementId": 1,
     "scope": "agreement",
     "orderId": null
   }
   ```

2. Use the returned `grant` in `X-Download-Grant` and the login token in `Authorization: Token ...` when calling `GET /api/files/download/`. To download an order, set `orderId` to that order's ID. Allowed scopes are `agreement`, `planning`, `finance` and `dean`; the server checks the corresponding permissions.
3. The grant is signed, expires after the configured duration, and is bound to the user’s current login session and the selected file/version. It can start **one** download. It is consumed when the authorized server request opens the file; expiry does not interrupt a transfer already started. Another click requests a fresh grant.

The ticket is sent in a header, never in the URL. The response is an attachment with `application/octet-stream`, `nosniff` and `private, no-store`. Legacy Finance/Dean/agreement-order file endpoints also require a matching grant. Permission, account state, password/session revocation, hidden state, removal and file version are checked again when downloading. A downloaded local copy cannot be revoked by expiring its grant.

| Response | Meaning / next step |
| --- | --- |
| 400 | Invalid JSON fields or settings; correct the form |
| 401 | Missing/expired/revoked login; renew the session or sign in |
| 403 | Missing Download permission, invalid/mismatched grant, or failed refresh CSRF/origin check |
| 404 | Missing/removed file, wrong document type/order, hidden Planning document or blocked public media link |
| 409 | Grant already used or file changed; click Download again for a fresh grant |
| 410 | Grant expired; click Download again |
| 429 | Five failed sign-in attempts triggered the 15-minute username lockout |

### Login changes and deployment

Access tokens and the current user are held in Vue memory, not `localStorage` or `sessionStorage`. Old browser authentication/password-cache keys are removed on startup. The app restores a valid session after reload through a rotating HttpOnly refresh cookie and automatically retries an API request once after access expiry. Normal login cookies last for the browser session, bounded by the configured server session duration. **تذكرني على هذا الجهاز** enables a persistent cookie, bounded by Remember Me settings. The server stores only token hashes.

Refresh requires both its cookie and the `X-Refresh-CSRF` header, obtained from Login or `GET /api/auth/csrf/`; untrusted browser origins are rejected. Logout revokes the current session. Password changes revoke all previous sessions and issue a new current session; Admin password reset and account deactivation revoke the user's sessions. New users still must change their generated temporary password before accessing features. Incorrect login, malformed input and expired sessions return the standard API error response.

Refresh cookies use `HttpOnly`, `SameSite=Lax`, host-only scope and `/api/auth/`. HTTPS requests receive `Secure` cookies. Keep the native TLS proxy's `Host` and `X-Forwarded-Proto` forwarding correct. Django explicitly allows credentialed CORS for the configured origins; the old `CORS_ALLOW_CREDENTIALS` environment switch is obsolete and is ignored. Preflight allows `Authorization`, `Content-Type`, `X-Refresh-CSRF` and `X-Download-Grant`; an external proxy must preserve these responses and headers.

Local Docker uses the dashboard's same-origin `/api/` gateway so `.localhost` cookie site rules do not break reloads. Ports remain unchanged. Use [local login](http://cm.localhost:81/login), [Admin security settings](http://cm.localhost:81/admin/security), or `http://localhost:81`. Direct frontend access on `:8081` also proxies `/api/`. Vite development/preview proxies `/api/` to the local gateway on port 81. Production continues to use `VITE_API_BASE_URL` and the configured HTTPS API origin.

Deploy backend, frontend and Nginx together:

```bash
docker compose build backend frontend
docker compose up -d backend frontend nginx
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
docker compose ps
```

Backend startup applies migrations `0013` and `0014` and seeds missing role permissions. **All legacy login tokens are invalidated once by this upgrade; sign in again after updating.** User passwords and uploaded documents are preserved. Refresh the browser with Ctrl+F5 to load the new frontend. No Docker Compose port changes are needed.

Keep `SECRET_KEY` stable and secret. Optionally set one independent `FILE_DOWNLOAD_SIGNING_KEY` in the existing backend environment; otherwise it derives a separate signing key from `SECRET_KEY`. Rotating the download key invalidates outstanding grants. Never place signing keys in Vue, Postman or URLs.

### Postman and regressions

The collection includes **Secure Downloads and Security Settings**, JSON grant requests, attachment download, a reused-grant check, Admin settings and cookie/CSRF refresh steps. Run Login, choose an existing document and scope, issue a grant, then **Download once (Send and Download)**. Run the reused-grant request immediately afterward to expect 409. Keep Postman cookies enabled. New sign-ins, refresh and password-change requests update both `token` and `csrf_token` in the selected local/production environment.

The Docker regression suite covers login for all roles, malformed/incorrect/disabled login, lockout, secure-cookie flags, session/access expiry, refresh rotation/replay, CSRF/origin/CORS, logout, password change/reset, deactivation, Admin settings validation, Read/Write/Download separation, all six document types and their Finance orders, expired/tampered/reused/wrong-session tickets, hidden/removed/replaced/missing files, signing-key rotation, public-path protection and simultaneous use of one grant. PostgreSQL execution runs the race test; SQLite skips that one test.

```bash
docker compose run --rm --no-deps -e USE_SQLITE_FOR_TESTS=False --entrypoint python backend manage.py test contract --noinput
npm run test:planning --prefix frontend
```

After local Docker is healthy, browser tests can use an installed `playwright` package and Chrome. Override `PLAYWRIGHT_MODULE` and `CHROME_PATH` when using another installation. For live tests, set `DASHBOARD_TEST_ACCOUNTS` to a temporary JSON file containing the five seeded account credentials as `{ "role": "admin", "username": "...", "password": "..." }` objects. Do not commit this file; remove it after testing. Use the passwords generated in your own environment.

```powershell
$env:DASHBOARD_TEST_URL = 'http://cm.localhost:81'
$env:ORDER_TEST_URL = 'http://cm.localhost:81'
$env:MODAL_TEST_URL = 'http://cm.localhost:81'
$env:DASHBOARD_TEST_ACCOUNTS = 'C:/path/outside/repository/test-accounts.json'
node frontend/tests/dashboard.browser.mjs
node frontend/tests/security.browser.mjs
node frontend/tests/agreement-orders.browser.mjs
node frontend/tests/modal-layout.browser.mjs
```

`dashboard.browser.mjs` tests real Admin, Dean, Finance, Contracts and Planning logins at desktop/phone sizes, live charts/navigation, reload renewal, absence of stored credentials, private cookies, protected downloads, reused-grant rejection and logout. `security.browser.mjs` is local-only: it creates one temporary user, verifies first-login password change and mismatch handling, expires only its own access token to check automatic renewal, verifies Admin-page denial and deactivation redirect, then deletes only that temporary user through local Docker. The other browser suites mock API data and cover attachment/order actions, error/retry/empty states and 80 responsive modal checks without modifying agreements.

Verified locally on 2026-10-28 with the rebuilt Docker app:

| Check | Result |
| --- | --- |
| Django regression suite on PostgreSQL | 115 tests passed, including contract requests, doctoral contracts, cost-table persistence and simultaneous grant consumption |
| Live role/browser checks | All 5 roles passed at 1440px and 390px |
| First-login / password / expiry / deactivation workflow | Passed; temporary account removed afterward |
| Agreement and Finance-order browser checks | 16 page checks passed, including attachment downloads |
| Responsive agreement/user/role modals | 80 checks passed at 5 viewport sizes |
| Damascus date/filter and cost-display unit tests | 7 passed |
| Updated Postman local security smoke | 10 requests and 9 assertions passed; cloud reporting disabled |
| Docker builds, Django checks/migrations, Nginx configuration | Passed; local services healthy |

## Production security checklist

- Keep `.env` readable only by the deployment account.
- Use separate strong secrets for Django, PostgreSQL, and pgAdmin.
- Keep `DEBUG=False`.
- Expose only ports `80` and `443` publicly.
- Restrict application ports to loopback/private networks with the host firewall.
- Do not expose pgAdmin publicly; use an SSH tunnel when required.
- Monitor certificate renewal and container health.
- Back up PostgreSQL and uploaded media.
- Review backend and proxy logs after deployments.
