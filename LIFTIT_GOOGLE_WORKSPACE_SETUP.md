# Liftit Google Workspace OAuth Setup

This guide configures Google OAuth to work with Liftit's corporate Google Workspace, allowing only @liftit.co employees to access the application.

## Prerequisites

- Admin access to Liftit's Google Cloud Console
- Admin access to Supabase project
- Permissions to create OAuth applications in Liftit organization

## Step 1: Google Cloud Console Setup (Liftit Organization)

### 1.1 Access Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your **@liftit.co** account
3. Ensure you're in the **Liftit organization**

### 1.2 Create/Select Project
1. Create new project:
   - Name: `Liftit Cotizador SICETAC`
   - Organization: `liftit.co`
   - Billing account: Select Liftit's billing account

### 1.3 Enable APIs
Navigate to "APIs & Services" > "Library" and enable:
- Google Identity Toolkit API
- Admin SDK API
- Cloud Identity API

### 1.4 Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Select **"Internal"** (Important: This restricts to @liftit.co only)
3. Configure:
   ```
   App name: Liftit Cotizador SICETAC
   User support email: soporte@liftit.co
   App logo: [Upload Liftit logo]
   Application home page: https://cotizador-sicetac.vercel.app
   Authorized domains:
     - liftit.co
     - vercel.app
     - supabase.co
   Developer contact: desarrollo@liftit.co
   ```
4. Scopes: Add these scopes:
   - `email`
   - `profile`
   - `openid`

### 1.5 Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "+ Create Credentials" > "OAuth client ID"
3. Configure:
   ```
   Application type: Web application
   Name: Supabase Auth - Liftit Internal

   Authorized JavaScript origins:
   - http://localhost:5050
   - https://cotizador-sicetac.vercel.app
   - https://pwurztydqaykrwaafdux.supabase.co

   Authorized redirect URIs:
   - https://pwurztydqaykrwaafdux.supabase.co/auth/v1/callback
   - http://localhost:5050/auth/callback
   - https://cotizador-sicetac.vercel.app/auth/callback
   ```
4. Save and copy:
   - **Client ID**: `xxxxx.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-xxxxx`

## Step 2: Supabase Configuration

### 2.1 Add OAuth Credentials
1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/pwurztydqaykrwaafdux/auth/providers)
2. Click on **Google** provider
3. Add:
   - Client ID: [Your Client ID from Google]
   - Client Secret: [Your Client Secret from Google]
   - Authorized Client IDs: [Leave empty or add Client ID again]
4. Save

### 2.2 Configure Auth Settings
1. Go to Authentication > Settings
2. Configure:
   - Site URL: `https://cotizador-sicetac.vercel.app`
   - Redirect URLs: Add:
     ```
     http://localhost:5050/app
     https://cotizador-sicetac.vercel.app/app
     ```

## Step 3: Application Configuration

### 3.1 Update Environment Variables
Add to Vercel environment variables:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_HD=liftit.co  # Hosted domain restriction
```

### 3.2 Update Login Page
The login page has been updated to:
- Restrict logins to @liftit.co domain
- Show account selector for multiple Liftit accounts
- Redirect to corporate SSO

## Step 4: Domain Verification (If Required)

If Google requires domain verification:

1. Go to Google Search Console
2. Add property: `cotizador-sicetac.vercel.app`
3. Verify using DNS or HTML file method
4. Add TXT record to Vercel DNS settings if using DNS verification

## Step 5: Testing

### 5.1 Local Testing
```bash
# Start the application
uvicorn app.main:app --reload --port 5050

# Open in browser
open http://localhost:5050
```

### 5.2 Test Login Flow
1. Click "Continuar con Google"
2. You should see Liftit's SSO page
3. Login with @liftit.co credentials
4. Should redirect to /app after successful authentication

### 5.3 Verify Domain Restriction
Try logging in with non-@liftit.co account:
- Should be rejected with "This app is restricted to liftit.co users"

## Security Considerations

### Domain Restriction
The app is configured to only accept @liftit.co emails:
- OAuth consent screen set to "Internal"
- `hd` parameter set to 'liftit.co' in OAuth request
- Supabase can add additional email domain validation

### Access Control
- Only Liftit employees can access
- Sessions expire after inactivity
- Tokens are securely stored in httpOnly cookies

### Audit Trail
- All logins are logged in Supabase
- Can integrate with Liftit's audit systems
- Session management through Supabase dashboard

## Troubleshooting

### "Access Blocked" Error
- Ensure app is set to "Internal" in OAuth consent screen
- Verify user has @liftit.co email
- Check if user needs to be added to test users list

### "Invalid Client" Error
- Verify Client ID and Secret in Supabase match Google Console
- Check redirect URIs are exactly matching
- Ensure project is in Liftit organization

### Domain Not Verified
- Complete domain verification in Google Search Console
- Add DNS records to Vercel
- Wait for propagation (can take up to 48 hours)

## Admin Tasks

### Adding/Removing Access
1. Users are automatically allowed if they have @liftit.co email
2. To block specific users, use Supabase user management
3. Can integrate with Liftit's HR systems for automated provisioning

### Monitoring Usage
1. View login activity in Supabase Dashboard > Authentication > Users
2. Set up alerts for unusual activity
3. Regular audit of access logs

## Support

For issues:
1. Check Google Workspace admin console for SSO issues
2. Review Supabase authentication logs
3. Contact Liftit IT team for corporate account issues
4. Development team: desarrollo@liftit.co