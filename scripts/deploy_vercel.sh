#!/bin/bash

# Vercel Deployment Script for liftit-cotizador-sicetac

echo "🚀 Starting Vercel deployment for liftit-cotizador-sicetac..."

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo "❌ Error: vercel.json not found. Please run this script from the project root."
    exit 1
fi

echo "📦 Project: liftit-cotizador-sicetac"
echo "📍 Repository: https://github.com/fbetancourtc/liftit-cotizador-sicetac"
echo ""

echo "⚠️  Before deploying, make sure to:"
echo "1. Configure environment variables in Vercel dashboard:"
echo "   - DATABASE_URL (PostgreSQL connection string)"
echo "   - SICETAC_USERNAME"
echo "   - SICETAC_PASSWORD"
echo "   - SICETAC_ENDPOINT"
echo "   - SICETAC_TIMEOUT_SECONDS"
echo "   - SICETAC_VERIFY_SSL"
echo "   - SUPABASE_PROJECT_URL"
echo "   - SUPABASE_JWT_AUDIENCE"
echo "   - SUPABASE_ANON_KEY"
echo ""
echo "2. Set up a PostgreSQL database (Vercel Postgres, Supabase, or external)"
echo ""

read -p "Have you configured all environment variables? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Please configure environment variables first at: https://vercel.com/dashboard"
    exit 1
fi

echo ""
echo "🔗 Linking to Vercel project..."

# Try to deploy
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📌 Next steps:"
echo "1. Visit your Vercel dashboard to check deployment status"
echo "2. Configure domain settings if needed"
echo "3. Test the API endpoints:"
echo "   - Health check: https://your-app.vercel.app/api/healthz"
echo "   - Documentation: https://your-app.vercel.app/docs"
echo ""
echo "🔍 Troubleshooting:"
echo "- If deployment fails, check the Vercel logs"
echo "- Ensure all environment variables are correctly set"
echo "- Verify PostgreSQL connection string format"
echo "- Check that Python version is 3.11 in vercel.json"