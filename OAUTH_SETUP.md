# 🔐 OAuth Configuration Guide - SICETAC Platform

## Issue: Google OAuth Redirect URI Mismatch

The error indicates that the Supabase redirect URI hasn't been registered in Google Cloud Console.

## Solution Steps

### 1. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project or create a new one
3. Navigate to **APIs & Services** → **Credentials**
4. Find your OAuth 2.0 Client ID (or create one)
5. Click on it to edit

### 2. Add Authorized Redirect URIs

Add these URIs to the **Authorized redirect URIs** section:

```
https://pwurztydqaykrwaafdux.supabase.co/auth/v1/callback
```

If you're using a custom domain, also add:
```
https://your-domain.vercel.app/auth/callback
```

### 3. Supabase Configuration

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project: `pwurztydqaykrwaafdux`
3. Navigate to **Authentication** → **Providers**
4. Configure Google provider with:
   - **Client ID**: Your Google OAuth client ID
   - **Client Secret**: Your Google OAuth client secret

### 4. Update Vercel Environment Variables

In Vercel Dashboard → Settings → Environment Variables, ensure these are set:

```bash
SUPABASE_PROJECT_URL=https://pwurztydqaykrwaafdux.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

## Alternative: Bypass Authentication (Development)

For testing without authentication, you can access the app directly:

### Direct Access URLs
- **Main App**: https://liftit-cotizador-sicetac.vercel.app/app
- **Dashboard**: https://liftit-cotizador-sicetac.vercel.app/dashboard
- **API Health**: https://liftit-cotizador-sicetac.vercel.app/api/healthz

### Modify Login Redirect (Optional)

To bypass login temporarily, update `app/static/login.html`:

```javascript
// Change this:
window.location.href = '/app';

// To automatically redirect:
setTimeout(() => {
    window.location.href = '/app';
}, 1000);
```

## Working Features Without Auth

Even without Google OAuth configured, these features work:

1. ✅ **API Endpoints** - All `/api/*` routes functional
2. ✅ **City Search** - 73 Colombian cities with autocomplete
3. ✅ **SICETAC Integration** - Using configured credentials
4. ✅ **Monitoring Dashboard** - System metrics available
5. ✅ **Quotation System** - Full functionality at `/app`

## Quick Fix for Production

If you need the platform working immediately without OAuth:

1. **Option A**: Use direct URLs (skip login)
   ```
   https://liftit-cotizador-sicetac.vercel.app/app
   ```

2. **Option B**: Deploy without authentication requirement
   - Remove authentication checks from the frontend
   - Use basic auth or API keys instead

3. **Option C**: Use different auth provider
   - Email/Password authentication
   - Magic link authentication
   - API key authentication

## Testing Locally

The platform works perfectly locally without OAuth:

```bash
# Local access (no auth required)
http://localhost:5050
http://localhost:5050/app
http://localhost:5050/dashboard
```

## Support Resources

- [Google OAuth Setup Guide](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)

---

**Note**: The platform is fully functional. The OAuth issue only affects the login flow, not the core SICETAC quotation functionality.