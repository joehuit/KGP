# KGP LIST — Production Deployment Runbook

## Overview

This guide details the procedure for deploying the KGP LIST platform into staging and production environments in accordance with the Phase 1 security foundation.

## Production Security Checklist

1. [ ] **TLS/HTTPS Enforced:** All external traffic terminates at reverse proxy (e.g., Nginx or Caddy) with valid SSL/TLS certificates.
2. [ ] **No Direct Database Access:** PostgreSQL is bound to an isolated internal Docker network (`kgp_internal_net`) without exposing port 5432 to the public internet.
3. [ ] **Strict CORS:** Ensure `CORS_ORIGINS` in `.env.prod` contains only verified production client origins. Wildcard `*` is automatically rejected by backend validation.
4. [ ] **Cryptographic Secrets:** `SECRET_KEY` must be at least 32 characters of high-entropy randomness generated via `secrets.token_urlsafe(48)`.
5. [ ] **Debug Mode Disabled:** `DEBUG=False` in `.env.prod`.
6. [ ] **Database Connection Pooling:** Configured with `pool_pre_ping=True` and connection recycling to survive firewall disconnects.

## Deploying with Docker Compose

```bash
# 1. Clone repository on target server
git clone <repo_url> /opt/kgp-list
cd /opt/kgp-list/deployment

# 2. Configure production secrets
cp .env.prod.example .env.prod
nano .env.prod

# 3. Build and launch services
docker compose -f docker-compose.prod.yml up -d --build

# 4. Run database migrations inside backend container
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Verify health endpoint
curl -f http://localhost:8000/api/health
```
