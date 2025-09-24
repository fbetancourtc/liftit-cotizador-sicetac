# Vercel Deployment Guide for liftit-cotizador-sicetac

## 🚀 Quick Deploy

### Deploy with Vercel Button
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/fbetancourtc/liftit-cotizador-sicetac)

## 📋 Prerequisites

1. **GitHub Repository**: ✅ Created at [github.com/fbetancourtc/liftit-cotizador-sicetac](https://github.com/fbetancourtc/liftit-cotizador-sicetac)
2. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
3. **PostgreSQL Database**: Required (SQLite won't work in serverless)

## 🔧 Environment Variables

Configure in Vercel Dashboard → Project Settings → Environment Variables:

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `SICETAC_USERNAME` - SICETAC API username
- `SICETAC_PASSWORD` - SICETAC API password
- `SICETAC_ENDPOINT` - `http://rndcws.mintransporte.gov.co:8080/ws/rndcService`

### Optional
- `SUPABASE_PROJECT_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_JWT_AUDIENCE` - `authenticated`
- `ENVIRONMENT` - `production`

## 🗄️ Database Setup

### Option 1: Vercel Postgres
1. Go to Vercel Dashboard → Storage
2. Create new Postgres database
3. Copy connection string to `DATABASE_URL`

### Option 2: Supabase
1. Create project at [supabase.com](https://supabase.com)
2. Settings → Database → Connection string
3. Use "Connection pooling" URL for serverless

## 🚀 Deployment Steps

### Via Vercel Dashboard
1. Import GitHub repository
2. Configure environment variables
3. Deploy

### Via CLI
```bash
npm i -g vercel
vercel --prod
```

## 🔍 Verification

- **API Health**: `https://your-app.vercel.app/api/healthz`
- **API Docs**: `https://your-app.vercel.app/docs`
- **Web Interface**: `https://your-app.vercel.app`

## 🐛 Troubleshooting

- **Module errors**: Check `requirements.txt`
- **DB errors**: Verify `DATABASE_URL` format
- **Timeouts**: Increase `maxDuration` in `vercel.json`
- **Static files**: Check `vercel.json` routes

## 📊 Project Links

- **GitHub**: [github.com/fbetancourtc/liftit-cotizador-sicetac](https://github.com/fbetancourtc/liftit-cotizador-sicetac)
- **Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)