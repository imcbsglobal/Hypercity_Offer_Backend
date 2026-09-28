# Local OTP Testing Plan - Simplified

## Goal
Create `.env.local` + switch script so the user can switch from the production PostgreSQL DB to local SQLite for testing, then switch back — **one command each way**.

## Current State (verified in repo)
- `.env` has production config: PostgreSQL (`DB_ENGINE=postgresql`), `SMS_ENABLED=True`, real IMCBS credentials
- `.env` is **NOT tracked in git** (removed in commit `c7d070d` "Remove environment file from repository") — `git checkout .env` will NOT restore it
- `.gitignore` already ignores `.env`, `.env.*`, `db.sqlite3`
- App code already supports stub SMS: `apps/accounts/sms.py:send_sms()` prints to console + logs to `SMSSendLog` + returns `ok=False` when `is_enabled()` is `False`
- `apps/accounts/views.py:SendOTPView` returns OTP in response when `DEBUG=True` and SMS is disabled
- Tests already exist: `apps/accounts/tests.py` with `SendOTPViewTests`, `VerifyOTPViewTests`, etc.

## Design Decision: prod restore via `.env.production` (not git)
Because `.env` is gitignored, `git checkout .env` won't work. Instead:
- Save the current `.env` as `.env.production` (portable backup, gitignored)
- `switch-env.ps1 prod` copies `.env.production` → `.env`

## Tasks

### 1. Create `.env.production` (backup of current production config)
Copy the current `.env` content verbatim into `.env.production`. This is the portable production template.

### 2. Create `.env.local` (local development)
```ini
# .env.local - Local development: SQLite + stub SMS
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database - SQLite for local testing
DB_ENGINE=sqlite3
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# SMS - Disabled (stub mode: prints to console, logs to SMSSendLog)
SMS_ENABLED=False
SMS_ACCESS_TOKEN=
SMS_ACCESS_TOKEN_KEY=

# Keep same defaults for app logic
SMS_OTP_EXPIRY_MINUTES=5
SMS_MAX_ATTEMPTS=5
SMS_RESEND_COOLDOWN=60
SMS_SIGNATURE_TTL=60
SMS_REQUEST_TIMEOUT=10

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

### 3. Create `switch-env.ps1` (root of project)
```powershell
param(
    [string]$Mode = "local"
)

if ($Mode -eq "local") {
    Copy-Item .env.local .env -Force
    Write-Host "LOCAL: SQLite + Stub SMS (testing mode)" -ForegroundColor Green
} elseif ($Mode -eq "prod") {
    if (Test-Path .env.production) {
        Copy-Item .env.production .env -Force
        Write-Host "PROD: PostgreSQL + Live SMS (restored from .env.production)" -ForegroundColor Green
    } else {
        git checkout .env 2>$null
        Write-Host "PROD: restored .env (git checkout)" -ForegroundColor Green
    }
} else {
    Write-Host "Usage: ./switch-env.ps1 local|prod" -ForegroundColor Yellow
}
```

### 4. Update `.gitignore` (explicit entries)
Add to existing `.gitignore`:
```
.env.local
.env.production
```
(Already covered by `.env.*` but add explicitly for clarity.)

## Usage

### Switch to local (SQLite + stub SMS)
```powershell
./switch-env.ps1 local
python manage.py migrate
python manage.py runserver
```

### Test OTP flow
```bash
curl -X POST http://localhost:8000/api/auth/send-otp/ -H "Content-Type: application/json" -d '{"phone": "9999999999"}'
curl -X POST http://localhost:8000/api/auth/verify-otp/ -H "Content-Type: application/json" -d '{"phone": "9999999999", "otp": "123456"}'
```

### Run tests
```bash
python manage.py test apps.accounts
```

### Switch back to production
```powershell
./switch-env.ps1 prod
```

## Validation
- [ ] `.env.local` exists with `DB_ENGINE=sqlite3`, `SMS_ENABLED=False`, `DEBUG=True`
- [ ] `./switch-env.ps1 local` → `.env` has SQLite + SMS disabled
- [ ] `./switch-env.ps1 prod` → `.env` restored with PostgreSQL + real SMS
- [ ] `python manage.py check` passes with local config
- [ ] `python manage.py migrate` works with SQLite
- [ ] OTP flow: send → verify → JWT issued (OTP visible in response when DEBUG=True)
- [ ] `SMSSendLog` entries show `success=False` in stub mode
- [ ] Tests pass: `python manage.py test apps.accounts`
- [ ] Production `.env` restored correctly after `switch-env.ps1 prod`

## Key Insight
The entire app logic is identical between local and production. Only the external HTTP call to `sms.imcbs.com` is skipped in stub mode (handled by `sms.py:send_sms()` lines 108-114). No code changes needed.
