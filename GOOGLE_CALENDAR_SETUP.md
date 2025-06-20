# Google Calendar Integration Setup Guide

## Overview
This guide explains how to set up Google Calendar integration for your Django appointment system. Users will be able to connect their Google Calendar accounts and sync events automatically.

## How It Works

### For Users (End Users)
1. **No Google Console Setup Required**: Users don't need to create their own Google applications
2. **One-Click Connection**: Users simply click "Connect Google Calendar" in the calendar settings
3. **Automatic Token Management**: Access tokens and refresh tokens are automatically obtained and stored
4. **Automatic Sync**: Events are automatically synced between your app and Google Calendar

### For Developers (You)
1. **Single OAuth Application**: You create one Google OAuth application that all users share
2. **Centralized Credentials**: All users authenticate through your application's credentials
3. **Secure Token Storage**: Each user's tokens are stored securely in their UserProfile

## Setup Instructions

### Step 1: Create the credentials.json file

Copy your `credentials_template.json` to `credentials.json` in the project root:

```bash
cp credentials_template.json credentials.json
```

**Important**: The `credentials.json` file should never be committed to version control as it contains sensitive credentials.

### Step 2: Configure Google Console (Already Done)

Your Google Console application is already configured with:
- **Client ID**: `496310986765-t249j48v463fl6cqpur6f7n0nrd03qgv.apps.googleusercontent.com`
- **Project ID**: `lofty-flare-458609-u7`
- **Redirect URI**: `http://localhost:8000/appointment/google/callback/`

### Step 3: Install Required Dependencies

Make sure you have the required packages in your `requirements.txt`:

```
google-auth-oauthlib==1.0.0
google-auth==2.17.3
google-api-python-client==2.86.0
```

### Step 4: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Test the Integration

1. Start your Django server: `python manage.py runserver`
2. Go to: `http://localhost:8000/appointment/calendar/settings/`
3. Click "Connect Google Calendar"
4. Complete the Google OAuth flow
5. Verify that tokens are stored in the UserProfile

## User Experience Flow

### 1. Initial Connection
1. User visits Calendar Settings page
2. Clicks "Connect Google Calendar" button
3. Redirected to Google OAuth consent screen
4. User grants permissions to your app
5. Redirected back to your app with authorization code
6. Your app exchanges code for access token and refresh token
7. Tokens are stored in UserProfile
8. User sees "Connected" status

### 2. Event Sync
1. User creates/updates events in your app
2. If Google Calendar is connected, events are automatically synced
3. Events appear in user's Google Calendar
4. Changes in Google Calendar can be synced back (if implemented)

### 3. Token Refresh
1. Access tokens expire after 1 hour
2. Refresh tokens are used to get new access tokens automatically
3. User doesn't need to re-authenticate unless refresh token expires

## Security Considerations

### 1. Credential Storage
- `credentials.json` is in `.gitignore` to prevent accidental commits
- User tokens are stored encrypted in the database
- Refresh tokens are stored securely in UserProfile

### 2. OAuth Security
- State parameter prevents CSRF attacks
- Proper error handling for OAuth failures
- Secure redirect URI validation

### 3. Token Management
- Access tokens expire automatically
- Refresh tokens are used for automatic renewal
- Users can disconnect at any time

## Troubleshooting

### Common Issues

#### 1. "Google OAuth credentials not configured"
**Solution**: Make sure `credentials.json` exists in the project root

#### 2. "Invalid redirect URI"
**Solution**: Check that the redirect URI in Google Console matches exactly:
`http://localhost:8000/appointment/google/callback/`

#### 3. "Access denied" during OAuth
**Solution**: 
- Check if the Google Calendar API is enabled in Google Console
- Verify the OAuth consent screen is configured
- Ensure the app is not in testing mode (or add test users)

#### 4. "Refresh token not received"
**Solution**: 
- Make sure `prompt='consent'` is set in the authorization URL
- Check if the user has already granted permissions (Google may not return refresh token on subsequent requests)

### Debug Steps

1. **Check credentials file**:
   ```bash
   ls -la credentials.json
   ```

2. **Verify Google Console settings**:
   - APIs enabled: Google Calendar API
   - OAuth consent screen configured
   - Credentials have correct redirect URI

3. **Check Django logs**:
   ```bash
   python manage.py runserver --verbosity=2
   ```

4. **Test OAuth flow manually**:
   - Visit the auth URL directly
   - Check for any error messages

## Production Deployment

### 1. Update Redirect URIs
For production, update the redirect URI in Google Console:
- Remove: `http://localhost:8000/appointment/google/callback/`
- Add: `https://yourdomain.com/appointment/google/callback/`

### 2. Environment Variables
Consider moving credentials to environment variables for better security:

```python
# In settings.py
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
```

### 3. HTTPS Required
Google OAuth requires HTTPS in production. Make sure your domain has SSL certificates.

## API Limits

- **Google Calendar API**: 1,000,000 requests per day per project
- **OAuth tokens**: Access tokens expire in 1 hour, refresh tokens can last indefinitely
- **Rate limiting**: Implement proper rate limiting for API calls

## Support

If users encounter issues:
1. Check the Django logs for error messages
2. Verify Google Console configuration
3. Test with a fresh OAuth flow
4. Check if the user's Google account has any restrictions

## Files Modified

- `appointment/views.py`: OAuth flow implementation
- `user_auth/models.py`: UserProfile with Google Calendar fields
- `appointment/templates/appointment/calendar_settings.html`: UI for connection
- `credentials.json`: Google OAuth credentials (not in version control)

## Next Steps

1. Test the complete OAuth flow
2. Implement event sync from Google Calendar to your app
3. Add calendar sharing features
4. Implement webhook notifications for real-time sync 