# Deployment Access Guide

## Current Status

The application has been successfully deployed to production at:
- **Deployment URL**: https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app

## Deployment Protection

Your deployment is currently protected by Vercel's authentication system. This is a security feature that requires authentication before accessing the deployment.

## How to Access the Deployment

### Option 1: Disable Protection (Recommended for Public Access)

1. Go to your Vercel Dashboard: https://vercel.com/dashboard
2. Navigate to your project: `liftit-cotizador-sicetac`
3. Go to Settings → General
4. Scroll to "Deployment Protection"
5. Set to "Disabled" or configure as needed
6. Save changes

### Option 2: Use Protection Bypass Token (For Development)

1. In Vercel Dashboard, go to your project settings
2. Navigate to Settings → General → Protection Bypass for Automation
3. Generate a bypass token
4. Access the deployment using:
   ```
   https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac?x-vercel-set-bypass-cookie=true&x-vercel-protection-bypass=YOUR_BYPASS_TOKEN
   ```

### Option 3: Configure for Specific Domain

Since you want to deploy to `micarga.flexos.ai/sicetac`, you'll need:

1. **Domain Configuration**:
   - Add `micarga.flexos.ai` as a custom domain in Vercel
   - Configure DNS to point to Vercel
   - Set up the domain routing

2. **Protection Settings**:
   - Configure protection to allow access from `micarga.flexos.ai`
   - Or disable protection entirely for production use

## Testing the Deployment

Once protection is configured, test these endpoints:

1. **Login Page**: `/sicetac`
2. **API Health**: `/sicetac/api/healthz`
3. **Main App**: `/sicetac/app`
4. **Dashboard**: `/sicetac/dashboard`

## Environment Variables

All required environment variables have been set:
- DATABASE_URL ✅
- SICETAC credentials ✅
- BASE_PATH (/sicetac) ✅
- PUBLIC_URL ✅
- CORS settings ✅

## Next Steps

1. Configure deployment protection settings in Vercel Dashboard
2. Set up the custom domain `micarga.flexos.ai`
3. Test all endpoints after protection is configured
4. Update OAuth redirect URLs in Supabase and Google Console

## Support

For deployment issues, check:
- Vercel Dashboard: https://vercel.com/dashboard
- Function Logs: Available in dashboard
- Build Logs: `vercel logs [deployment-url]`