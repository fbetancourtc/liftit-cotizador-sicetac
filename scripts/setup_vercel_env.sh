#!/bin/bash

echo "🔧 Setting up Vercel environment variables for liftit-cotizador-sicetac..."

# Required environment variables with defaults for testing
# You should replace these with actual values

# Database configuration (using a test PostgreSQL database)
echo "DATABASE_URL=postgresql://user:pass@db.example.com:5432/sicetac" | vercel env add DATABASE_URL production --force

# SICETAC configuration (using placeholder values - replace with actual)
echo "SICETAC_USERNAME=your_sicetac_username" | vercel env add SICETAC_USERNAME production --force
echo "SICETAC_PASSWORD=your_sicetac_password" | vercel env add SICETAC_PASSWORD production --force
echo "http://rndcws.mintransporte.gov.co:8080/ws/rndcService" | vercel env add SICETAC_ENDPOINT production --force
echo "30" | vercel env add SICETAC_TIMEOUT_SECONDS production --force
echo "true" | vercel env add SICETAC_VERIFY_SSL production --force

# Supabase configuration (referencing existing variables)
echo "authenticated" | vercel env add SUPABASE_JWT_AUDIENCE production --force
echo "production" | vercel env add ENVIRONMENT production --force

# Use existing Supabase variables with correct names
vercel env rm SUPABASE_PROJECT_URL production 2>/dev/null
vercel env add SUPABASE_PROJECT_URL production --force < <(vercel env get SUPABASE_URL production)

vercel env rm SUPABASE_ANON_KEY production 2>/dev/null
vercel env add SUPABASE_ANON_KEY production --force < <(vercel env get Supabase_Anon_Key production)

echo ""
echo "✅ Environment variables configured!"
echo ""
echo "⚠️  IMPORTANT: You need to update these values:"
echo "   1. DATABASE_URL - Set to your actual PostgreSQL database"
echo "   2. SICETAC_USERNAME - Your actual SICETAC username"
echo "   3. SICETAC_PASSWORD - Your actual SICETAC password"
echo ""
echo "You can update them at: https://vercel.com/fbetancourtcs-projects/liftit-cotizador-sicetac/settings/environment-variables"
echo ""
echo "After updating, redeploy with: vercel --prod --force"