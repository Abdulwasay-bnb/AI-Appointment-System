# Microsoft Outlook Calendar Integration

This app supports syncing with Microsoft Outlook calendars using Microsoft Graph API and MSAL.

## 1. Azure App Registration

1. Go to [Azure Portal > App registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
2. Register a new app (or use your existing one).
3. Add a Redirect URI:
   - For local development: `http://localhost:8000/appointment/microsoft/callback/`
   - For production: `https://<your-domain>/appointment/microsoft/callback/`
4. Under **Certificates & secrets**, create a new client secret. Save the value securely.
5. Under **API permissions**, add:
   - `Calendars.ReadWrite` (Microsoft Graph)

## 2. Environment Variables / Django Settings

Add the following to your `.env` file or `settings.py`:

```
MS_CLIENT_ID=your-azure-client-id
MS_CLIENT_SECRET=your-azure-client-secret
MS_TENANT_ID=your-tenant-id
MS_REDIRECT_URI=http://localhost:8000/appointment/microsoft/callback/
```

Or in `settings.py`:
```python
import os
MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID')
MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET')
MS_TENANT_ID = os.environ.get('MS_TENANT_ID')
MS_REDIRECT_URI = os.environ.get('MS_REDIRECT_URI', 'http://localhost:8000/appointment/microsoft/callback/')
```

## 3. Usage

- Go to your calendar settings page in the app.
- Click "Connect Microsoft Calendar" (button to be added in the frontend).
- Authenticate with your Microsoft account.
- The app will sync your Outlook calendar events.

## 4. Redirect URI to Register

**Register this URI in Azure:**

```
http://localhost:8000/appointment/microsoft/callback/
```

or your production equivalent.

---

For more details, see the code in `appointment/microsoft_calendar_service.py` and `appointment/views.py`. 