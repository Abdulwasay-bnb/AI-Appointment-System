from django.conf import settings
import os
import requests
import msal

CLIENT_ID = getattr(settings, 'MS_CLIENT_ID', os.environ.get('MS_CLIENT_ID'))
CLIENT_SECRET = getattr(settings, 'MS_CLIENT_SECRET', os.environ.get('MS_CLIENT_SECRET'))
TENANT_ID = getattr(settings, 'MS_TENANT_ID', os.environ.get('MS_TENANT_ID'))
REDIRECT_URI = getattr(settings, 'MS_REDIRECT_URI', os.environ.get('MS_REDIRECT_URI', 'http://localhost:8000/appointment/microsoft/callback/'))

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["Calendars.ReadWrite"]


def build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache,
    )

def get_auth_url(state):
    app = build_msal_app()
    return app.get_authorization_request_url(
        SCOPE,
        state=state,
        redirect_uri=REDIRECT_URI,
        prompt='select_account',
    )

def get_token_from_code(auth_code):
    app = build_msal_app()
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
    )
    return result

def get_calendar_events(access_token):
    endpoint = 'https://graph.microsoft.com/v1.0/me/events'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()

def create_outlook_event(access_token, event_data):
    endpoint = 'https://graph.microsoft.com/v1.0/me/events'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.post(endpoint, headers=headers, json=event_data)
    response.raise_for_status()
    return response.json()

def update_outlook_event(access_token, event_id, event_data):
    endpoint = f'https://graph.microsoft.com/v1.0/me/events/{event_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    response = requests.patch(endpoint, headers=headers, json=event_data)
    response.raise_for_status()
    return response.json() 