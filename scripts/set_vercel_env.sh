#!/bin/bash

# Script to set Vercel environment variables for SICETAC deployment

echo "🔧 Setting environment variables for SICETAC deployment..."
echo ""

# Add BASE_PATH
echo "/sicetac" | vercel env add BASE_PATH production

# Add PUBLIC_URL
echo "https://micarga.flexos.ai/sicetac" | vercel env add PUBLIC_URL production

# Add ALLOWED_HOSTS
echo "micarga.flexos.ai" | vercel env add ALLOWED_HOSTS production

# Add CORS_ORIGINS
echo "https://micarga.flexos.ai" | vercel env add CORS_ORIGINS production

# Add APP_NAME
echo "SICETAC - Cotizador Liftit" | vercel env add APP_NAME production

echo ""
echo "✅ Environment variables set successfully!"
echo ""
echo "Current environment variables:"
vercel env ls | grep -E "BASE_PATH|PUBLIC_URL|ALLOWED_HOSTS|CORS_ORIGINS|APP_NAME"