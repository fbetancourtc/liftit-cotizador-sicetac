#!/bin/bash

# Script to pull environment variables from Vercel for local development
# Requires Vercel CLI to be installed: npm i -g vercel

echo "🔄 Syncing environment variables from Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed."
    echo "Please install it with: npm i -g vercel"
    exit 1
fi

# Pull environment variables from Vercel
echo "📥 Pulling environment variables..."
vercel env pull .env.local

if [ $? -eq 0 ]; then
    echo "✅ Environment variables synced to .env.local"
    echo ""
    echo "To use these variables locally, run:"
    echo "  export $(cat .env.local | xargs)"
    echo "Or use the .env.local file directly with your application"
else
    echo "❌ Failed to sync environment variables"
    echo "Make sure you're logged in to Vercel: vercel login"
    exit 1
fi