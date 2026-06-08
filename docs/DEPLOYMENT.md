# Cloud Deployment Guide

This project is deployment-ready as a three-service setup:

- Neon: production PostgreSQL
- Render: FastAPI backend
- Vercel: Vite React frontend

## 1. Create Neon PostgreSQL

```powershell
neon auth
neon projects create --name hcp-ai-crm --region-id aws-ap-southeast-1 --database hcp_crm --role hcp_crm_owner --set-context
neon connection-string --database-name hcp_crm --role-name hcp_crm_owner --ssl require
```

Copy the connection string. Use it as Render's `DATABASE_URL`.

The backend normalizes both `postgres://` and `postgresql://` URLs to SQLAlchemy's `postgresql+psycopg://` driver format automatically.

## 2. Deploy Backend On Render

Render can use the root-level `render.yaml` blueprint.
The backend has `backend/.python-version` set to Python 3.12 so Render does not use its Python 3.14 default.

Required Render environment variables:

```env
ENVIRONMENT=production
DATABASE_URL=<neon-connection-string>
GROQ_API_KEY=<your-groq-key>
GROQ_MODEL=gemma2-9b-it
CORS_ORIGINS=<your-vercel-production-url>
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
TRUSTED_HOSTS=localhost,127.0.0.1,*.onrender.com
SEED_DEMO_DATA=true
```

Render health check:

```text
/ready
```

Backend smoke checks after deploy:

```text
https://<render-service>.onrender.com/
https://<render-service>.onrender.com/health
https://<render-service>.onrender.com/ready
https://<render-service>.onrender.com/docs
https://<render-service>.onrender.com/hcps
```

## 3. Deploy Frontend On Vercel

The root-level `vercel.json` builds the frontend from the monorepo root.

Set this Vercel environment variable:

```env
VITE_API_URL=https://<render-service>.onrender.com
```

Deploy:

```powershell
vercel deploy --prod
```

Frontend smoke check:

```text
https://<vercel-app>.vercel.app
```

The top bar should show `API Connected`. If it shows `API Offline`, check `VITE_API_URL` in Vercel and `CORS_ORIGINS` in Render.

## Local Production Check

```powershell
cd C:\Users\pavansai\OneDrive\Desktop\hcp-ai-crm-industry-submission
$env:DATABASE_URL="sqlite:///./demo.db"
$env:ENVIRONMENT="production"
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd C:\Users\pavansai\OneDrive\Desktop\hcp-ai-crm-industry-submission\frontend
$env:VITE_API_URL="http://127.0.0.1:8000"
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
```
