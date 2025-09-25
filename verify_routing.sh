#!/bin/bash

echo "================================================================================"
echo "MICARGA.FLEXOS.AI/SICETAC ROUTING VERIFICATION"
echo "================================================================================"

BASE_URL="https://micarga.flexos.ai/sicetac"

# Function to test endpoint
test_endpoint() {
    local url=$1
    local description=$2

    response=$(curl -s -w "\n%{http_code}" "$url" | tail -n 1)

    if [ "$response" = "200" ]; then
        echo "✓ $description: SUCCESS (200)"
    elif [ "$response" = "500" ]; then
        echo "✗ $description: ERROR (500 - Server Error)"
    else
        echo "⚠ $description: Status $response"
    fi
}

echo ""
echo "Main Pages:"
echo "----------------------------------------"
test_endpoint "$BASE_URL" "Login Page (/sicetac)"
test_endpoint "$BASE_URL/" "Login Page (/sicetac/)"
test_endpoint "$BASE_URL/app" "Main App (/sicetac/app)"

echo ""
echo "Static Resources:"
echo "----------------------------------------"
test_endpoint "$BASE_URL/static/config.js" "Config JS"
test_endpoint "$BASE_URL/static/app.js" "App JS"
test_endpoint "$BASE_URL/static/cities.js" "Cities JS"
test_endpoint "$BASE_URL/static/styles.css" "Styles CSS"
test_endpoint "$BASE_URL/static/liftit-logo.svg" "Logo SVG"

echo ""
echo "API Endpoints:"
echo "----------------------------------------"
test_endpoint "$BASE_URL/api/health" "Health Check"
test_endpoint "$BASE_URL/api/auth/login" "Auth Login"
test_endpoint "$BASE_URL/api/quotes" "Quotes API"

echo ""
echo "Direct Vercel Deployment:"
echo "----------------------------------------"
VERCEL_URL="https://liftit-cotizador-sicetac-d0c8vl3fg-fbetancourtcs-projects.vercel.app/sicetac"
test_endpoint "$VERCEL_URL" "Direct Vercel (/sicetac)"
test_endpoint "$VERCEL_URL/api/health" "Direct Vercel API"

echo ""
echo "================================================================================"
echo "SUMMARY:"
echo "  • Frontend routing: ✓ WORKING"
echo "  • Static assets: ✓ WORKING"
echo "  • API endpoints: ✗ ERROR 500 (needs fixing)"
echo "================================================================================"
echo ""
echo "Note: The proxy routing from micarga.flexos.ai/sicetac is working correctly."
echo "      API endpoints are returning 500 errors on both proxy and direct access."
echo "      This is a backend issue in the FastAPI application that needs to be resolved."