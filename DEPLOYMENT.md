# De-ASI-INTERFACE — Deployment Guide

Owner/Creator: Richard Patterson  
© 2026 Richard Patterson. All Rights Reserved.

---

## Deployment Options

This app has two supported deployment targets:

| Feature | Vercel | Railway |
|---|---|---|
| HTTP API (`/api/auth/*`) | ✅ Full support | ✅ Full support |
| Static frontend (`/static`) | ✅ Full support | ✅ Full support |
| Health check (`/health`) | ✅ Full support | ✅ Full support |
| WebSockets (`/ws`) | ⚠️ Not supported\* | ✅ Full support |
| PostgreSQL pool | ⚠️ Serverless (per-req) | ✅ Persistent pool |
| Redis (token store) | ⚠️ External required | ✅ Plugin (1-click) |
| Long-running processes | ❌ No | ✅ Yes |
| Auto-deploy from GitHub | ✅ Yes | ✅ Yes |

> \* Vercel Serverless Functions are stateless and time-limited (10s Hobby / 60s Pro).  
> WebSocket connections require persistence. Use Railway for full WS support.

---

## 🔷 Vercel Deployment

### Prerequisites
- Vercel account at [vercel.com](https://vercel.com)
- External PostgreSQL (e.g. Neon, Supabase, or Railway Postgres)
- External Redis (e.g. Upstash Redis — free tier works)

### Step 1 — Connect Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `De-ASI-INTERFACE/De-ASI-INTERFACE` from GitHub
3. Framework Preset: **Other**
4. Root Directory: `/` (leave as default)
5. Build Command: leave blank
6. Output Directory: leave blank
7. Click **Deploy**

### Step 2 — Set Environment Variables

In Vercel Dashboard → Project → **Settings** → **Environment Variables**:

```
ENVIRONMENT        = production
JWT_SECRET         = <python -c "import secrets; print(secrets.token_hex(64))">
DATABASE_URL       = postgresql://user:pass@your-db-host:5432/dbname
REDIS_URL          = rediss://default:token@your-upstash-host:6379
CORS_ORIGINS       = https://your-app.vercel.app
LOG_LEVEL          = INFO
LOG_DIR            = /tmp/logs
JWT_EXPIRY_HOURS   = 1
```

> **Note:** `LOG_DIR` must be `/tmp/logs` on Vercel (only `/tmp` is writable in serverless).

### Step 3 — Run Database Migration

```bash
# From your local machine with DATABASE_URL set:
psql $DATABASE_URL -f src/api/auth/db_migrations.sql
```

Or use Neon/Supabase SQL editor to paste the contents of `src/api/auth/db_migrations.sql`.

### Step 4 — Verify Deployment

```bash
curl https://your-app.vercel.app/health
# Expected:
# {"status":"ok","version":"1.0.0-secure","environment":"production","redis":"connected","db":"connected"}
```

### Recommended External Services for Vercel

| Service | Provider | Free Tier |
|---|---|---|
| PostgreSQL | [Neon](https://neon.tech) | 512MB, 1 branch |
| PostgreSQL | [Supabase](https://supabase.com) | 500MB, 2 projects |
| Redis | [Upstash](https://upstash.com) | 10K req/day |

---

## 🚄 Railway Deployment (Recommended for WebSockets)

### Step 1 — Connect Repository

1. Go to [railway.app](https://railway.app) → **New Project**
2. Select **Deploy from GitHub repo**
3. Choose `De-ASI-INTERFACE/De-ASI-INTERFACE`
4. Railway auto-detects `Procfile` and deploys

### Step 2 — Add Plugins

In Railway Project dashboard:
- Click **+ New** → **Database** → **PostgreSQL** (auto-sets `DATABASE_URL`)
- Click **+ New** → **Database** → **Redis** (auto-sets `REDIS_URL`)

### Step 3 — Set Environment Variables

In Railway → Project → **Variables**:

```
ENVIRONMENT        = production
JWT_SECRET         = <python -c "import secrets; print(secrets.token_hex(64))">
CORS_ORIGINS       = https://your-app.up.railway.app
LOG_LEVEL          = INFO
LOG_DIR            = /var/log/app
JWT_EXPIRY_HOURS   = 1
```

> `DATABASE_URL` and `REDIS_URL` are auto-injected by Railway plugins.

### Step 4 — Run Migration

```bash
railway run psql $DATABASE_URL -f src/api/auth/db_migrations.sql
```

### Step 5 — Verify

```bash
curl https://your-app.up.railway.app/health
```

---

## Auto-Deploy on Push

Both Vercel and Railway auto-deploy on every push to `main`.
No manual `vercel deploy` or `railway up` needed after initial setup.

## Procfile (Railway)

```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 2 --loop asyncio
```

## vercel.json (Vercel)

See `vercel.json` in the project root. Routes all traffic through `api/index.py` ASGI adapter.
