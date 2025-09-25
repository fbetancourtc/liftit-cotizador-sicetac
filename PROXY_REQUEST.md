# Proxy Configuration Request for SICETAC Application

## Request Summary
We need to route traffic from `micarga.flexos.ai/sicetac/*` to our SICETAC application deployed on Vercel.

## Technical Details

**Source Path**: `https://micarga.flexos.ai/sicetac/*`
**Target URL**: `https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac/*`

## Required Configuration

### Option 1: If using Nginx
```nginx
location /sicetac {
    proxy_pass https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Base-Path /sicetac;

    # Handle CORS if needed
    proxy_set_header Access-Control-Allow-Origin https://micarga.flexos.ai;
}
```

### Option 2: If using Vercel
Add to your `vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/sicetac",
      "destination": "https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac"
    },
    {
      "source": "/sicetac/(.*)",
      "destination": "https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac/$1"
    }
  ]
}
```

### Option 3: If using Cloudflare
Add a Page Rule or Worker:
- **If Match**: `micarga.flexos.ai/sicetac/*`
- **Then Forward**: `https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac/$1`

## Important Notes

1. **No Path Conflicts**: Ensure no existing routes use `/sicetac`
2. **Headers Required**:
   - `X-Forwarded-Host: micarga.flexos.ai`
   - `X-Base-Path: /sicetac`
3. **CORS Configuration**: Our app accepts `https://micarga.flexos.ai` as origin

## Testing URLs

After configuration, these should work:
- Login: `https://micarga.flexos.ai/sicetac`
- API: `https://micarga.flexos.ai/sicetac/api/healthz`
- Static: `https://micarga.flexos.ai/sicetac/static/config.js`

## Our Application Info

- **Application**: Liftit Cotizador SICETAC
- **Purpose**: Transport quotation system
- **Tech Stack**: FastAPI (Python) + JavaScript
- **Current Status**: Fully deployed and working at Vercel URL

## Contact

If you need any adjustments to our application configuration to support the proxy setup, please let us know.

## Benefits of This Approach

1. **No Domain Transfer**: Keep your existing micarga.flexos.ai setup
2. **Multi-Tenant Support**: Multiple apps can share the domain
3. **Independent Deployments**: Each team can deploy independently
4. **Clean URLs**: Users access via `micarga.flexos.ai/sicetac`

---

**Estimated Time**: 15-30 minutes to implement and test