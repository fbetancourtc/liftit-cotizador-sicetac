# Google OAuth Setup Guide for Liftit Cotizador SICETAC

This guide explains how to configure Google OAuth authentication with Supabase for the Liftit Cotizador SICETAC application.

## Prerequisites

1. A Supabase project
2. A Google Cloud Console account
3. Access to Google Cloud Console

## Step 1: Configure Google OAuth in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. Create a new project or select an existing one

3. Enable Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API"
   - Click on it and press "Enable"

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - Choose "External" for user type
     - Fill in the required fields (App name, User support email, Developer contact)
     - Add your domain to "Authorized domains"
     - Save and continue

5. Create OAuth client ID:
   - Application type: "Web application"
   - Name: "Liftit Cotizador SICETAC"
   - Authorized redirect URIs: Add your Supabase callback URL:
     ```
     https://<YOUR_SUPABASE_PROJECT_ID>.supabase.co/auth/v1/callback
     ```
   - Click "Create"

6. Save your credentials:
   - Copy the "Client ID"
   - Copy the "Client Secret"

## Step 2: Configure Supabase

1. Go to your [Supabase Dashboard](https://app.supabase.com/)

2. Select your project

3. Navigate to "Authentication" > "Providers"

4. Find "Google" in the list and click "Enable"

5. Enter your Google OAuth credentials:
   - Client ID: (paste from Google Cloud Console)
   - Client Secret: (paste from Google Cloud Console)
   - Authorized Client IDs: (optional, leave empty for now)

6. Click "Save"

## Step 3: Configure the Application

1. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your Supabase credentials:
   ```
   SUPABASE_PROJECT_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_JWT_AUDIENCE=authenticated
   ```

3. Find your Supabase credentials:
   - Go to Supabase Dashboard > Settings > API
   - Copy "Project URL" → `SUPABASE_PROJECT_URL`
   - Copy "anon public" key → `SUPABASE_ANON_KEY`

## Step 4: Test the Authentication

1. Start the application:
   ```bash
   uvicorn app.main:app --reload --port 5050
   ```

2. Open your browser and go to:
   ```
   http://localhost:5050/
   ```

3. You should see the login page with "Continuar con Google" button

4. Click the Google sign-in button

5. You'll be redirected to Google's OAuth consent screen

6. After authorization, you'll be redirected back to the application

## Authentication Flow

```
User → Login Page (/) → Click "Google Sign In"
  ↓
Google OAuth → Authorize
  ↓
Redirect to /app → Check Auth Token
  ↓
Access Application
```

## Troubleshooting

### "Redirect URI mismatch" error
- Ensure the redirect URI in Google Cloud Console matches exactly:
  ```
  https://<YOUR_SUPABASE_PROJECT_ID>.supabase.co/auth/v1/callback
  ```

### "Invalid client" error
- Double-check your Client ID and Client Secret in Supabase
- Ensure Google+ API is enabled in Google Cloud Console

### Users can't sign in
- Check that your Google OAuth consent screen is properly configured
- For production, you may need to verify your domain

### Authentication not persisting
- Check browser console for errors
- Ensure localStorage is enabled in the browser
- Verify JWT tokens are being stored correctly

## Security Considerations

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use HTTPS in production** - OAuth requires secure connections
3. **Restrict authorized domains** in Google Cloud Console for production
4. **Enable email verification** in Supabase for additional security
5. **Configure CORS properly** in your FastAPI application

## Production Deployment

For production deployment:

1. Update authorized redirect URIs in Google Cloud Console to include your production domain:
   ```
   https://your-domain.com/auth/v1/callback
   ```

2. Update Supabase Site URL:
   - Go to Supabase Dashboard > Authentication > URL Configuration
   - Update "Site URL" to your production domain

3. Set environment variables in your production environment (e.g., Vercel, Railway, etc.)

## Additional Features

### Email Whitelist (Optional)
To restrict access to specific email domains:

1. In Supabase Dashboard > Authentication > Providers > Google
2. Add authorized domains in "Authorized Client IDs" field

### Custom Claims (Optional)
You can add custom claims to the JWT token using Supabase Database Webhooks or Edge Functions.

## Support

For issues or questions:
- Supabase Documentation: https://supabase.com/docs/guides/auth/auth-google
- Google OAuth Documentation: https://developers.google.com/identity/protocols/oauth2