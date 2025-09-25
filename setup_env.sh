#!/bin/bash

echo "🔧 Setting up critical Vercel environment variables..."

# Set required environment variables to get the app working
echo "postgresql://postgres:postgres@db.supabase.co:5432/postgres" | vercel env add DATABASE_URL production --force
echo "test_user" | vercel env add SICETAC_USERNAME production --force
echo "test_pass" | vercel env add SICETAC_PASSWORD production --force
echo "http://rndcws.mintransporte.gov.co:8080/ws/rndcService" | vercel env add SICETAC_ENDPOINT production --force
echo "30" | vercel env add SICETAC_TIMEOUT_SECONDS production --force
echo "true" | vercel env add SICETAC_VERIFY_SSL production --force
echo "https://wzdhfopftxsyydjjakvi.supabase.co" | vercel env add SUPABASE_PROJECT_URL production --force
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind6ZGhmb3BmdHhzeXlkampha3ZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYxMTYyNDksImV4cCI6MjA1MTY5MjI0OX0.WyzqqvNxfb4oWZLIEidIgKkBAxqerYRPL5feVwA2X7o" | vercel env add SUPABASE_ANON_KEY production --force
echo "authenticated" | vercel env add SUPABASE_JWT_AUDIENCE production --force
echo "production" | vercel env add ENVIRONMENT production --force

echo "✅ Environment variables added! Redeploying..."
vercel --prod --force