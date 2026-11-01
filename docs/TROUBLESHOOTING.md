# KGP LIST — Developer Troubleshooting Guide

## 1. PowerShell Script Execution Policy (Windows)

**Error:**
```
File C:\...\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```

**Solution:**
In Windows PowerShell (as Administrator or CurrentUser scope):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 2. PostgreSQL Connection Refused (`could not connect to server: Connection refused`)

**Symptom:**
Backend startup warning:
```
Could not connect to database on startup. Ensure PostgreSQL is running.
```

**Checks & Fixes:**
1. If using Docker, ensure Docker Desktop is started and run:
   ```powershell
   cd database
   docker compose up -d
   docker compose ps
   ```
2. Verify port `5432` is not blocked or taken by another service:
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 5432
   ```
3. Check `.env` configuration:
   Ensure `DATABASE_URL` matches your local database user and password:
   ```env
   DATABASE_URL=postgresql+psycopg://kgp_user:kgp_secret_password_change_me@localhost:5432/kgp_db
   ```

---

## 3. Alembic Migration Errors

**Error:** `target database is not up to date`
**Solution:**
```powershell
cd backend
alembic upgrade head
```

**Error:** `psycopg.OperationalError: connection to server at "localhost" failed`
**Solution:** PostgreSQL is not currently running. Start the Docker container via `cd database; docker compose up -d`.

---

## 4. `decimal_max_places` Request Validation Error

**Symptom:**
Submitting a product price like `14500.999` returns `422 Unprocessable Content`.

**Explanation:**
Algerian Dinar prices only support centimes (at most 2 decimal places, e.g. `14500.50`). The backend strictly enforces `decimal_places=2` to prevent floating-point rounding errors in commercial transactions. Always format prices to two decimal places.

---

## 5. CORS Rejection in Production

**Symptom:**
Frontend reports CORS error when connecting to production API.

**Explanation:**
The backend security validator strictly forbids `CORS_ORIGINS=["*"]` when `ENVIRONMENT="production"`. Add your exact production domain (e.g. `https://admin.kgp-list.dz`) to the `CORS_ORIGINS` list in `.env`.

---

## 6. ADMIN_API_KEY Rejection in Production/Staging

**Symptom:**
Requests with `X-Admin-Key` return `401 Unauthorized` with message:
```
ADMIN_API_KEY authentication is disabled in staging and production. Authenticate using 'Authorization: Bearer <jwt_token>'.
```

**Solution:**
In Phase 2B, `ADMIN_API_KEY` is deprecated and allowed only in `development` and `testing`. Administrative web and mobile clients in staging/production must authenticate against `POST /api/v1/auth/login` to obtain a signed JWT token, then supply `Authorization: Bearer <token>`.

---

## 7. SMS Gateway Not Configured in Production

**Symptom:**
Requesting customer OTP in production returns `503 Service Unavailable`:
```
No production SMS gateway configured. Set SMS_GATEWAY_PROVIDER and SMS_API_KEY in production.
```

**Solution:**
The `dev_mock` provider is strictly forbidden in production to prevent fake phone verifications. Set `SMS_GATEWAY_PROVIDER=twilio` or `SMS_GATEWAY_PROVIDER=algeria_telecom` along with a valid `SMS_API_KEY` in `.env`.

---

## 8. Idempotency Key Conflict (`409 Conflict`)

**Symptom:**
Retrying an order returns `409 Conflict`:
```
Idempotency key conflict: A request with this Idempotency-Key has already been processed with different parameters or payload.
```

**Solution:**
Clients must use a new, unique UUID for distinct order submissions. Reusing an existing `Idempotency-Key` with altered quantities, products, or customer notes is rejected to prevent payload mutation attacks on cached idempotency keys.
