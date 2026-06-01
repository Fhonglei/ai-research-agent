# 🚀 Deployment Guide

This guide covers deploying the AI Research Agent to production.

## Architecture (Production)

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Vercel         │────▶│   Railway        │────▶│  Supabase     │
│   (Frontend)     │     │   (Backend)      │     │  (Database)   │
│   Next.js 14     │     │   FastAPI        │     │  PostgreSQL   │
└─────────────────┘     └─────────────────┘     └──────────────┘
                                   │
                        ┌──────────┼──────────┐
                        │          │          │
                   ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
                   │ Claude  │ │ Tavily  │ │ Others  │
                   │ API     │ │ Search  │ │         │
                   └────────┘ └────────┘ └────────┘
```

## Option 1: Vercel + Railway (Recommended)

### Frontend (Vercel)

1. Push your code to GitHub:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ai-research-agent.git
git push -u origin main
```

2. Go to [vercel.com](https://vercel.com) → "New Project"
3. Import your GitHub repo
4. Configure:
   - **Framework**: Next.js
   - **Root Directory**: `frontend`
   - **Environment Variables**:
     - `NEXT_PUBLIC_API_URL` = your Railway backend URL

5. Deploy!

### Backend (Railway)

1. Go to [railway.app](https://railway.app) → "New Project" → "Deploy from GitHub"
2. Select your repo
3. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `ANTHROPIC_API_KEY` — your Claude API key
   - `TAVILY_API_KEY` — your Tavily API key
   - `SUPABASE_URL` — your Supabase project URL
   - `SUPABASE_ANON_KEY` — your Supabase anon key
5. Deploy!

6. Update Vercel's `NEXT_PUBLIC_API_URL` to point to your Railway URL.

### Database (Supabase)

1. Go to [supabase.com](https://supabase.com) → "New Project"
2. Once created, go to SQL Editor
3. Paste and run the contents of `supabase/schema.sql`
4. Copy the project URL and anon key to your Railway env vars

## Option 2: Docker Compose (VPS)

For self-hosted deployment on a VPS (AWS EC2, DigitalOcean, Hetzner):

```bash
# Clone and configure
git clone https://github.com/YOUR_USERNAME/ai-research-agent.git
cd ai-research-agent
cp .env.example .env
# Edit .env with your API keys + Supabase URL

# Start all services
docker-compose up -d

# Frontend: http://your-server-ip:3000
# Backend: http://your-server-ip:8000
```

For production, add an nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;  # Important for SSE streaming
        proxy_cache off;
    }
}
```

## Option 3: Single Docker Image

Build a combined image:

```dockerfile
# Dockerfile (root)
FROM python:3.12-slim AS backend
WORKDIR /app/backend
# ... backend setup ...

FROM node:20-alpine AS frontend
WORKDIR /app/frontend
# ... frontend build ...

FROM python:3.12-slim
# Copy both and run with supervisord or similar
```

## Environment Variables Reference

| Variable | Required | Description | Where to Get |
|----------|----------|-------------|--------------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key | [console.anthropic.com](https://console.anthropic.com/) |
| `TAVILY_API_KEY` | ✅ | Tavily search key | [app.tavily.com](https://app.tavily.com/) |
| `SUPABASE_URL` | ❌* | PostgreSQL URL | [supabase.com](https://supabase.com/) |
| `SUPABASE_ANON_KEY` | ❌* | Supabase auth key | [supabase.com](https://supabase.com/) |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL (frontend only) | Your Railway or VPS URL |

*Optional — the app works without Supabase but won't save history.

## Cost Estimates

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Vercel | 100 GB bandwidth | $20/mo Pro |
| Railway | $5 credit | ~$5-20/mo |
| Supabase | 500 MB DB | $25/mo Pro |
| Claude API | N/A | ~$0.01-0.05 per research |
| Tavily API | 1000 searches/mo | $30/mo for 5000 |

A single research task (standard depth) costs approximately **$0.02-0.08** in API fees.

## Monitoring

- **Backend logs**: Railway dashboard → Deployments → View Logs
- **Frontend logs**: Vercel dashboard → Analytics
- **API usage**: [Anthropic Console](https://console.anthropic.com/) + [Tavily Dashboard](https://app.tavily.com/)

## Custom Domain

1. Vercel: Settings → Domains → Add domain
2. Railway: Settings → Custom Domain
3. Update `NEXT_PUBLIC_API_URL` in Vercel to use the custom backend domain
