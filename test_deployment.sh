#!/bin/bash

# Test script for SICETAC deployment
echo "🧪 Testing SICETAC Deployment..."
echo "================================"

# Get the latest deployment URL
DEPLOYMENT_URL=$(vercel ls --json | jq -r '.[0].url' 2>/dev/null || echo "liftit-cotizador-sicetac.vercel.app")
echo "Testing deployment: https://$DEPLOYMENT_URL"
echo ""

# Test 1: Login page
echo "1. Testing login page (/sicetac)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL/sicetac")
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Login page accessible (HTTP $STATUS)"
else
    echo "   ❌ Login page returned HTTP $STATUS"
fi

# Test 2: API Health endpoint
echo ""
echo "2. Testing API health endpoint..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL/sicetac/api/healthz")
if [ "$STATUS" = "200" ]; then
    echo "   ✅ API endpoint working (HTTP $STATUS)"
    curl -s "https://$DEPLOYMENT_URL/sicetac/api/healthz" | jq '.' 2>/dev/null || curl -s "https://$DEPLOYMENT_URL/sicetac/api/healthz"
else
    echo "   ❌ API endpoint returned HTTP $STATUS"
fi

# Test 3: Static files
echo ""
echo "3. Testing static files..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL/sicetac/static/config.js")
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Static files accessible (HTTP $STATUS)"
else
    echo "   ❌ Static files returned HTTP $STATUS"
fi

# Test 4: Application page
echo ""
echo "4. Testing application page..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DEPLOYMENT_URL/sicetac/app")
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Application page accessible (HTTP $STATUS)"
else
    echo "   ❌ Application page returned HTTP $STATUS"
fi

echo ""
echo "================================"
echo "Test complete!"
echo ""
echo "📌 Access your application at:"
echo "   https://$DEPLOYMENT_URL/sicetac"
echo ""
echo "📝 If all tests passed, your deployment is ready!"
echo "   Next: Configure custom domain if needed"