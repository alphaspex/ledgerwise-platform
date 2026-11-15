<!-- Inputs: backend source files, frontend TypeScript API contract, uploaded Module 1/2/3 specifications, and deployment environment variables. -->
<!-- Outputs: backend setup, configuration, runtime, integration, and test instructions for maintainers. -->
<!-- Explanation: Documents how to configure and run the Ledgerwise FastAPI backend; it does not deploy resources. -->

# Ledgerwise backend

## Runtime

Python 3.11+ with FastAPI and Uvicorn. The service exposes the frontend HTTP API and starts a single 5-second orchestrator loop in the same process.

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

On Windows, activate the virtual environment with `.venv\\Scripts\\activate`.

## Required configuration

Set these values in the deployment environment. Do not commit credentials.

| Variable | Purpose |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account containing D1 |
| `CLOUDFLARE_DATABASE_ID` | D1 database identifier |
| `CLOUDFLARE_API_TOKEN` | D1 query permission token |
| `API_TOKEN` | Meta Muse API token |
| `JWT_SECRET` | HS256 JWT signing secret |
| `SEED_ADMIN_EMAIL` | First administrator email |
| `SEED_ADMIN_PASSWORD` | First administrator password |
| `RESEND_API_KEY` | Required auth and outbound email provider key |
| `RESEND_FROM_EMAIL` | Verified Resend sender |
| `CALCOM_API_KEY` | Cal.com API v2 token |
| `CALCOM_EVENT_TYPE_ID` | Cal.com event type identifier |

Optional settings are listed in `.env.example`. Apollo is disabled unless `APOLLO_ENABLED=true`; when enabled, set `APOLLO_API_KEY`. Apollo requests are limited by `APOLLO_RATE_LIMIT_RPM` (default 50).

The backend seeds the first admin with `INSERT OR IGNORE`. Keep `SEED_ADMIN_PASSWORD` in the secret store and rotate it through the password flow after initial access. There is no public signup route.

## Database

At startup, the service applies `backend/migrations/0001_init.sql` to the configured D1 database. The migration uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.

D1 stores boolean flags as integers. API response serializers convert `is_admin`, `do_not_contact`, and `read` to JSON booleans.

The orchestrator is the only writer to `module_1_queues`. It uses a compare-and-set version update before dispatching Module 1 worker tasks. Module 2 work is claimed from `module_2_queue`; workers do not issue D1 queries.

## API contract

The public API implements the 29 method/path definitions from `frontend/src/api/endpoints.ts`. Request and response models are defined in `backend/models.py` to match `frontend/src/shared/types.ts`.

Authentication uses `Authorization: Bearer <jwt>`. Member tokens use HS256 and expire after seven days. Admin-only user management checks the `is_admin` claim.

Rate limits are in-memory per process and per client IP: 5 requests per 60 seconds for auth-class routes, and 60 requests per 60 seconds for global-class routes. A 429 response includes `Retry-After`.

Wrong passwords for protected password-change flows and wrong one-time codes return 400, not 401. A 401 is reserved for missing, invalid, or expired bearer tokens on authenticated routes, and incorrect login credentials on the public login route.

The backend also exposes two backend-only webhooks:
- `POST /webhooks/resend/inbound`
- `POST /webhooks/calcom`

## Background work

The orchestrator runs every five seconds. It owns D1 queue writes, claims tasks before dispatch, and writes worker results on a later tick. The main controls include the approved-company target (30), minimum live sources (1), three attempts, five-minute worker leases, and the source-defined Module 1/2 concurrency limits.

Prospect replies can call the Cal.com availability, booking, and human-handoff tools. A successful agent booking is written to `bookings`. Human takeover and closed threads suppress automatic replies. A human reply endpoint queues delivery and waits for the final message status.

## Apollo contact lookup

Apollo is optional and disabled by default. When enabled, approved companies without a manually entered contact are queued using the existing `draft` type with a null `message_id`. A lookup searches Founder/CEO, COO, and finance titles, then enriches a single candidate by Apollo person ID.

An Apollo candidate is accepted only when the returned current-employer domain matches the target company, the role is one of the configured groups, the email is verified, and it is not a generic inbox. Multiple candidates are sent to the existing `contact_missing` notification flow for human selection. Manual contact entry always overrides an Apollo result.

## Tests

Run:

```bash
pytest backend/tests
```

The contract tests check route parity, rate-limit behavior, contact/domain helpers, and response boolean/memory serialization.

## Container

Build from the repository root:

```bash
docker build -f backend/Dockerfile -t ledgerwise-backend .
docker run --env-file backend/.env -p 8000:8000 ledgerwise-backend
```

No external database, provider account, deployment target, or secret is created by these instructions.
