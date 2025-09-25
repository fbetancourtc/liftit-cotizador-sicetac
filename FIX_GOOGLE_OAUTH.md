# Fix Google OAuth Redirect Issue

## Problem
You're being redirected to Liftit's corporate login page instead of the public Google OAuth flow.

## Solution

### Step 1: Check Supabase Google OAuth Configuration

1. Go to your Supabase Dashboard:
   https://supabase.com/dashboard/project/pwurztydqaykrwaafdux/auth/providers

2. Click on **Google** provider settings

3. Check if you have configured:
   - **Client ID** (should NOT be empty)
   - **Client Secret** (should NOT be empty)

### Step 2: Create Google OAuth Credentials (If Missing)

If Client ID and Secret are empty, you need to create them:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. Create a new project or select existing one (NOT Liftit's corporate project)

3. Enable Google Identity API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Identity Toolkit API"
   - Click and Enable it

4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: **Web application**
   - Name: "Liftit Cotizador Supabase"

5. Add Authorized redirect URIs:
   ```
   https://pwurztydqaykrwaafdux.supabase.co/auth/v1/callback
   ```

6. Copy the **Client ID** and **Client Secret**

### Step 3: Configure in Supabase

1. Go back to Supabase Dashboard > Authentication > Providers > Google

2. Paste:
   - **Client ID** from Google Console
   - **Client Secret** from Google Console

3. **Important Settings**:
   - Skip nonce checks: Leave unchecked
   - Use PKCE flow: Leave unchecked

4. Click **Save**

### Step 4: Test Locally

1. Clear browser cache and cookies for localhost:5050

2. Restart the application:
   ```bash
   # Kill existing process
   lsof -i:5050 | grep LISTEN | awk '{print $2}' | xargs kill -9

   # Restart
   uvicorn app.main:app --reload --port 5050
   ```

3. Open in an incognito/private browser window:
   http://localhost:5050/

4. Click "Continuar con Google"

5. You should see Google's public OAuth screen (NOT Liftit corporate login)

### Step 5: Alternative - Use Email/Password Authentication

If Google OAuth continues to redirect to corporate login, use email/password:

1. Click "Iniciar sesión con email" on the login page
2. Create an account with any email
3. Verify your email (check spam folder)
4. Login with email/password

## Debugging

Check browser console for errors:
1. Open Developer Tools (F12)
2. Go to Console tab
3. Try clicking "Continuar con Google"
4. Look for any error messages

Common issues:
- Missing OAuth credentials in Supabase
- Wrong redirect URI in Google Console
- Browser cached corporate Google session

## Quick Fix - Bypass Google OAuth

If you need to test the app immediately without Google OAuth:

1. Use the email/password option
2. Or create a test user directly in Supabase:
   - Go to Supabase Dashboard > Authentication > Users
   - Click "Add user"
   - Create a test user with email/password
   - Use those credentials to login