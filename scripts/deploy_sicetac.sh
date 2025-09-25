#!/bin/bash

# Deployment Script for SICETAC to micarga.flexos.ai/sicetac
# This script handles the deployment of the SICETAC application
# to a shared domain with subpath routing

echo "🚀 SICETAC Multi-Tenant Deployment Script"
echo "=========================================="
echo ""
echo "📍 Target: micarga.flexos.ai/sicetac"
echo "📦 Project: liftit-cotizador-sicetac"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo -e "${RED}❌ Error: vercel.json not found.${NC}"
    echo "Please run this script from the project root."
    exit 1
fi

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Vercel CLI
if ! command_exists vercel; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found. Installing...${NC}"
    npm i -g vercel
fi

echo ""
echo "📋 Pre-deployment Checklist:"
echo "=============================="
echo ""

# Environment variables check
echo "1. Environment Variables Required in Vercel Dashboard:"
echo "   ✓ BASE_PATH=/sicetac"
echo "   ✓ PUBLIC_URL=https://micarga.flexos.ai/sicetac"
echo "   ✓ DATABASE_URL (PostgreSQL connection)"
echo "   ✓ SICETAC_USERNAME"
echo "   ✓ SICETAC_PASSWORD"
echo "   ✓ SICETAC_ENDPOINT"
echo "   ✓ SUPABASE_PROJECT_URL"
echo "   ✓ SUPABASE_ANON_KEY"
echo ""

echo "2. OAuth Configuration:"
echo "   ✓ Supabase redirect URL: https://micarga.flexos.ai/sicetac/auth/callback"
echo "   ✓ Google Cloud Console redirect URI configured"
echo ""

echo "3. Domain Configuration:"
echo "   ✓ micarga.flexos.ai configured in Vercel"
echo "   ✓ DNS records pointing to Vercel"
echo ""

read -p "Have you completed all the checklist items? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please complete the configuration first:${NC}"
    echo "1. Go to: https://vercel.com/dashboard"
    echo "2. Configure environment variables"
    echo "3. Set up domain configuration"
    echo "4. Update OAuth providers"
    exit 1
fi

echo ""
echo "🔧 Setting up deployment environment..."
echo ""

# Create/update .env.vercel with sicetac-specific config
cat > .env.sicetac <<EOF
# SICETAC Subpath Deployment Configuration
BASE_PATH=/sicetac
PUBLIC_URL=https://micarga.flexos.ai/sicetac
ALLOWED_HOSTS=micarga.flexos.ai
CORS_ORIGINS=https://micarga.flexos.ai
APP_NAME=SICETAC - Cotizador Liftit
ENVIRONMENT=production
EOF

echo -e "${GREEN}✅ Environment configuration created${NC}"

echo ""
echo "🔍 Verifying configuration..."
echo ""

# Check if vercel.json has the correct routing
if grep -q '"/sicetac"' vercel.json; then
    echo -e "${GREEN}✅ Routing configuration verified${NC}"
else
    echo -e "${RED}❌ Error: vercel.json missing /sicetac routes${NC}"
    exit 1
fi

# Check if config.js exists
if [ -f "app/static/config.js" ]; then
    echo -e "${GREEN}✅ Frontend configuration found${NC}"
else
    echo -e "${RED}❌ Error: app/static/config.js not found${NC}"
    exit 1
fi

echo ""
echo "🚀 Starting deployment to Vercel..."
echo "===================================="
echo ""

# Deploy to Vercel
if [ "$1" == "--production" ] || [ "$1" == "-p" ]; then
    echo "Deploying to PRODUCTION..."
    vercel --prod --yes
else
    echo "Deploying to PREVIEW..."
    echo "Use './scripts/deploy_sicetac.sh --production' for production deployment"
    vercel --yes
fi

DEPLOY_EXIT_CODE=$?

if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo "📌 Next Steps:"
    echo "=============="
    echo ""
    echo "1. Verify deployment:"
    echo "   - Login page: https://micarga.flexos.ai/sicetac"
    echo "   - Application: https://micarga.flexos.ai/sicetac/app"
    echo "   - API Health: https://micarga.flexos.ai/sicetac/api/healthz"
    echo ""
    echo "2. Test OAuth flow:"
    echo "   - Try logging in with Google"
    echo "   - Verify redirect works correctly"
    echo ""
    echo "3. Monitor logs:"
    echo "   - Check Vercel dashboard for any errors"
    echo "   - Review function logs if needed"
    echo ""
    echo "4. Test with other apps on the domain:"
    echo "   - Ensure no conflicts with other subpaths"
    echo "   - Verify routing isolation"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "================"
    echo "1. Check Vercel logs for detailed error"
    echo "2. Verify all environment variables are set"
    echo "3. Ensure domain is properly configured"
    echo "4. Check that OAuth redirect URLs are correct"
    echo ""
    echo "For help, visit: https://vercel.com/docs"
    exit 1
fi

# Clean up temporary files
if [ -f ".env.sicetac" ]; then
    rm .env.sicetac
fi

echo ""
echo "🎉 SICETAC deployment script completed!"
echo ""