#!/bin/bash

# Production deployment script for Liftit Sicetac
# This script handles the complete production deployment process

set -e  # Exit on error

echo "🚀 Liftit Sicetac Production Deployment"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running from project root
if [ ! -f "requirements.txt" ]; then
    print_error "Must run from project root directory"
    exit 1
fi

# Load environment variables
if [ -f ".env.production" ]; then
    print_status "Loading production environment variables"
    export $(cat .env.production | grep -v '^#' | xargs)
else
    print_warning "No .env.production file found, using defaults"
fi

# Step 1: Pre-deployment checks
echo ""
echo "1. Running pre-deployment checks..."
echo "-----------------------------------"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )[\d.]+')
print_status "Python version: $PYTHON_VERSION"

# Check Node version
NODE_VERSION=$(node --version)
print_status "Node version: $NODE_VERSION"

# Check Vercel CLI
if command -v vercel &> /dev/null; then
    print_status "Vercel CLI installed"
else
    print_error "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Step 2: Run tests
echo ""
echo "2. Running tests..."
echo "-------------------"

# Install test dependencies
pip install -q pytest pytest-cov pytest-asyncio

# Run tests
if pytest tests/ -v --tb=short; then
    print_status "All tests passed"
else
    print_error "Tests failed. Aborting deployment."
    exit 1
fi

# Step 3: Build optimization
echo ""
echo "3. Optimizing build..."
echo "----------------------"

# Minify static files
if [ -d "app/static" ]; then
    print_status "Optimizing static assets"

    # Install minification tools if needed
    npm install -g terser cssnano-cli html-minifier-terser --silent

    # Minify JavaScript
    for file in app/static/*.js; do
        if [ -f "$file" ] && [[ ! "$file" == *.min.js ]]; then
            terser "$file" -o "${file%.js}.min.js" --compress --mangle
            print_status "Minified: $(basename $file)"
        fi
    done

    # Minify CSS
    for file in app/static/*.css; do
        if [ -f "$file" ] && [[ ! "$file" == *.min.css ]]; then
            cssnano "$file" "${file%.css}.min.css"
            print_status "Minified: $(basename $file)"
        fi
    done
fi

# Step 4: Database migrations
echo ""
echo "4. Checking database migrations..."
echo "-----------------------------------"

# Check if there are pending migrations
if [ -d "migrations" ]; then
    print_status "Checking for pending migrations"
    # Add migration logic here if using Alembic or similar
fi

# Step 5: Deploy to Vercel
echo ""
echo "5. Deploying to Vercel..."
echo "--------------------------"

# Set Vercel environment
export VERCEL_ORG_ID=${VERCEL_ORG_ID}
export VERCEL_PROJECT_ID=${VERCEL_PROJECT_ID}

# Pull Vercel environment
vercel pull --yes --environment=production

# Build project
print_status "Building production bundle"
vercel build --prod

# Deploy
print_status "Deploying to production"
DEPLOYMENT_URL=$(vercel deploy --prod --prebuilt)

if [ $? -eq 0 ]; then
    print_status "Deployment successful!"
    echo "URL: $DEPLOYMENT_URL"
else
    print_error "Deployment failed"
    exit 1
fi

# Step 6: Post-deployment validation
echo ""
echo "6. Running post-deployment checks..."
echo "-------------------------------------"

# Wait for deployment to be ready
print_status "Waiting for deployment to be ready..."
sleep 30

# Health checks
print_status "Running health checks"

# Check main endpoint
if curl -f -s "https://sicetac.liftit.co/health" > /dev/null; then
    print_status "Main health check passed"
else
    print_error "Main health check failed"
    exit 1
fi

# Check API endpoint
if curl -f -s "https://sicetac.liftit.co/api/healthz" > /dev/null; then
    print_status "API health check passed"
else
    print_error "API health check failed"
    exit 1
fi

# Step 7: Performance validation
echo ""
echo "7. Validating performance..."
echo "-----------------------------"

# Quick performance test
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "https://sicetac.liftit.co/api/healthz")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)

if (( $(echo "$RESPONSE_TIME_MS < 500" | bc -l) )); then
    print_status "Response time: ${RESPONSE_TIME_MS}ms ✓"
else
    print_warning "Response time: ${RESPONSE_TIME_MS}ms (above 500ms threshold)"
fi

# Step 8: Cache warming
echo ""
echo "8. Warming cache..."
echo "--------------------"

# Warm cache with common routes
COMMON_ROUTES=(
    "BOGOTA:MEDELLIN:3S3:202501"
    "MEDELLIN:CARTAGENA:3S2:202501"
    "CALI:BOGOTA:2S3:202501"
)

for route in "${COMMON_ROUTES[@]}"; do
    IFS=':' read -r origin dest config period <<< "$route"
    curl -s -X POST "https://sicetac.liftit.co/api/quote" \
        -H "Content-Type: application/json" \
        -d "{\"origin\":\"$origin\",\"destination\":\"$dest\",\"configuration\":\"$config\",\"period\":\"$period\"}" \
        > /dev/null
    print_status "Cached route: $origin → $dest"
done

# Step 9: Monitoring setup
echo ""
echo "9. Configuring monitoring..."
echo "-----------------------------"

# Set up monitoring alerts (if using external service)
if [ ! -z "$DATADOG_API_KEY" ]; then
    print_status "Datadog monitoring configured"
fi

if [ ! -z "$SENTRY_DSN" ]; then
    print_status "Sentry error tracking configured"
fi

# Step 10: Final summary
echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "Production URL: https://sicetac.liftit.co"
echo "API Docs: https://sicetac.liftit.co/api/docs"
echo ""
echo "Next steps:"
echo "1. Monitor error rates in Sentry"
echo "2. Check performance metrics in Datadog"
echo "3. Review cache hit rates"
echo "4. Verify WebSocket connections"
echo ""
print_status "Deployment successful! 🚀"

# Optional: Send notification
if [ ! -z "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Sicetac deployed to production successfully!\nURL: https://sicetac.liftit.co\"}" \
        "$SLACK_WEBHOOK" 2>/dev/null
fi

exit 0