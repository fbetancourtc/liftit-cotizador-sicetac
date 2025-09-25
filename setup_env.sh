#!/bin/bash

echo "🔧 Setting up critical Vercel environment variables..."

# Set required environment variables to get the app working
echo "postgresql://postgres:postgres@db.supabase.co:5432/postgres" | vercel env add DATABASE_URL production --force
echo "test_user" | vercel env add SICETAC_USERNAME production --force
echo "test_pass" | vercel env add SICETAC_PASSWORD production --force
echo "http://rndcws.mintransporte.gov.co:8080/ws/rndcService" | vercel env add SICETAC_ENDPOINT production --force
echo "30" | vercel env add SICETAC_TIMEOUT_SECONDS production --force
echo "true" | vercel env add SICETAC_VERIFY_SSL production --force
# Set Supabase project variables (current project)
echo "https://pwurztydqaykrwaafdux.supabase.co" | vercel env add SUPABASE_PROJECT_URL production --force
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3dXJ6dHlkcWF5a3J3YWFmZHV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MjA2NDMsImV4cCI6MjA2NTQ5NjY0M30.v8_63hLXCSAZZ7Z3Xc85A7wLNXe4YyMgBoIj7mqz6Lg" | vercel env add SUPABASE_ANON_KEY production --force
echo "authenticated" | vercel env add SUPABASE_JWT_AUDIENCE production --force
echo "production" | vercel env add ENVIRONMENT production --force

echo "✅ Environment variables added! Redeploying..."
vercel --prod --force
