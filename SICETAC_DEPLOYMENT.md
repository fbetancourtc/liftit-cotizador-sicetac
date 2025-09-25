# 🚀 SICETAC Multi-Tenant Deployment Guide

## Overview

This document describes the deployment of the SICETAC application to **micarga.flexos.ai/sicetac**, implementing a domain-driven multi-tenant architecture where multiple applications share the same domain under different subpaths.

## Architecture

```
micarga.flexos.ai/
├── /sicetac/          → This application (Liftit Cotizador SICETAC)
├── /other-app/        → Another team's application
└── /another-app/      → Another team's application
```

## URLs Structure

### Production URLs
- **Login Page**: https://micarga.flexos.ai/sicetac
- **Application**: https://micarga.flexos.ai/sicetac/app
- **Dashboard**: https://micarga.flexos.ai/sicetac/dashboard
- **API Endpoints**: https://micarga.flexos.ai/sicetac/api/*
- **Static Assets**: https://micarga.flexos.ai/sicetac/static/*

## Environment Variables

### Required Variables (Vercel Dashboard)

```bash
# Path Configuration
BASE_PATH=/sicetac
PUBLIC_URL=https://micarga.flexos.ai/sicetac

# Domain Configuration
ALLOWED_HOSTS=micarga.flexos.ai
CORS_ORIGINS=https://micarga.flexos.ai

# Application Info
APP_NAME=SICETAC - Cotizador Liftit
ENVIRONMENT=production

# Database (PostgreSQL Required)
DATABASE_URL=postgresql://user:password@host:port/database

# SICETAC API Credentials
SICETAC_USERNAME=your_sicetac_username
SICETAC_PASSWORD=your_sicetac_password
SICETAC_ENDPOINT=http://rndcws.mintransporte.gov.co:8080/ws/rndcService
SICETAC_TIMEOUT_SECONDS=30
SICETAC_VERIFY_SSL=true

# Supabase Authentication
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_JWT_AUDIENCE=authenticated
```

## Deployment Steps

### 1. Configure Vercel Project

```bash
# Link to Vercel project (if not already linked)
vercel link

# Set environment variables
vercel env add BASE_PATH production
vercel env add PUBLIC_URL production
# ... add all other variables
```

### 2. Configure OAuth Providers

#### Supabase Configuration
1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add redirect URL: `https://micarga.flexos.ai/sicetac/auth/callback`
3. Add site URL: `https://micarga.flexos.ai/sicetac`

#### Google Cloud Console
1. Navigate to APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add authorized redirect URI: `https://micarga.flexos.ai/sicetac/auth/callback`
4. Add authorized JavaScript origin: `https://micarga.flexos.ai`

### 3. Domain Configuration

#### Option A: If domain is already configured
- Ensure micarga.flexos.ai points to Vercel
- No additional DNS configuration needed

#### Option B: New domain setup
1. In Vercel Dashboard → Settings → Domains
2. Add custom domain: `micarga.flexos.ai`
3. Configure DNS records:
   ```
   Type: CNAME
   Name: micarga
   Value: cname.vercel-dns.com
   ```

### 4. Deploy Application

```bash
# Use the deployment script
./scripts/deploy_sicetac.sh

# For production deployment
./scripts/deploy_sicetac.sh --production

# Or deploy directly with Vercel CLI
vercel --prod
```

## File Structure Changes

### Frontend Configuration
- `app/static/config.js` - Centralized path configuration
- All HTML files include base href: `<base href="/sicetac/">`
- JavaScript files use `window.APP_CONFIG` for paths

### Backend Configuration
- FastAPI uses `root_path="/sicetac"`
- CORS configured for micarga.flexos.ai
- All routes automatically prefixed

### Routing Configuration
- `vercel.json` handles path rewrites
- All requests to `/sicetac/*` routed correctly

## Testing Checklist

### Basic Functionality
- [ ] Login page loads at `/sicetac`
- [ ] OAuth login works correctly
- [ ] Successful redirect after login to `/sicetac/app`
- [ ] Dashboard accessible at `/sicetac/dashboard`

### API Testing
- [ ] API health check: `/sicetac/api/healthz`
- [ ] Quote creation works
- [ ] Quote history loads

### Asset Loading
- [ ] CSS files load correctly
- [ ] JavaScript files execute
- [ ] Images/logos display

### Multi-Tenant Validation
- [ ] No conflicts with other apps on domain
- [ ] Routing isolation maintained
- [ ] Session management isolated

## Troubleshooting

### Common Issues

#### 404 Errors
- Verify `vercel.json` routing configuration
- Check BASE_PATH environment variable
- Ensure all paths use `/sicetac` prefix

#### OAuth Redirect Issues
- Verify redirect URLs in Supabase and Google Console
- Check PUBLIC_URL environment variable
- Review browser console for errors

#### API Connection Failures
- Confirm API_BASE in frontend config
- Check CORS configuration
- Verify FastAPI root_path setting

#### Static Assets Not Loading
- Check base href in HTML files
- Verify static file routing in vercel.json
- Confirm paths in config.js

### Debug Commands

```bash
# Check deployment status
vercel ls

# View deployment logs
vercel logs

# Check environment variables
vercel env ls

# Test locally with production config
vercel dev
```

## Maintenance

### Updating Environment Variables
```bash
vercel env rm VARIABLE_NAME production
vercel env add VARIABLE_NAME production
```

### Rolling Back Deployment
```bash
# List deployments
vercel ls

# Rollback to specific deployment
vercel rollback <deployment-url>
```

### Monitoring
- Vercel Dashboard: https://vercel.com/dashboard
- Function Logs: Available in Vercel Dashboard
- Error Tracking: Configure Sentry (optional)

## Security Considerations

1. **Environment Variables**: Never commit sensitive values to git
2. **CORS**: Configured for specific domain only
3. **OAuth**: Redirect URLs restricted to production domain
4. **API Keys**: Stored securely in Vercel environment
5. **Database**: Use connection pooling for PostgreSQL

## Support

### Resources
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)

### Contact
- Technical Issues: Create issue in GitHub repository
- Deployment Support: Check Vercel support documentation

## Appendix

### Environment Variable Reference

| Variable | Description | Example |
|----------|-------------|---------|
| BASE_PATH | Application subpath | `/sicetac` |
| PUBLIC_URL | Full public URL | `https://micarga.flexos.ai/sicetac` |
| DATABASE_URL | PostgreSQL connection | `postgresql://...` |
| SICETAC_USERNAME | SICETAC API username | `api_user` |
| SICETAC_PASSWORD | SICETAC API password | `secure_password` |
| SUPABASE_PROJECT_URL | Supabase project URL | `https://xxx.supabase.co` |
| SUPABASE_ANON_KEY | Supabase public key | `eyJhbGc...` |

### Multi-Tenant Architecture Benefits

1. **Shared Infrastructure**: Multiple apps share same domain
2. **Cost Efficiency**: Single SSL certificate and DNS configuration
3. **Independent Deployment**: Each team deploys independently
4. **Clean URLs**: Professional subpath structure
5. **Scalability**: Easy to add new applications

---

**Last Updated**: 2024-09-24
**Version**: 1.0.0