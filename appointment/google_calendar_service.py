import os
import json
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils import timezone
from user_auth.models import UserProfile

class GoogleCalendarService:
    """Service class to handle Google Calendar API operations"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, user):
        self.user = user
        self.service = None
        self.credentials = None
    
    def get_credentials(self):
        """Get or refresh user credentials"""
        try:
            user_profile, created = UserProfile.objects.get_or_create(user=self.user)
            
            if not user_profile.is_google_calendar_connected:
                return None
            
            # Create credentials from stored tokens
            self.credentials = Credentials(
                token=user_profile.google_access_token,
                refresh_token=user_profile.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.CLIENT_ID,
                client_secret=settings.CLIENT_SECRET,
                scopes=self.SCOPES
            )
            
            # Refresh token if expired
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                
                # Update stored tokens
                user_profile.google_access_token = self.credentials.token
                user_profile.google_token_expiry = timezone.now() + datetime.timedelta(
                    seconds=self.credentials.expiry.timestamp() - timezone.now().timestamp()
                )
                user_profile.save()
            
            return self.credentials
            
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None
    
    def build_service(self):
        """Build Google Calendar service"""
        if not self.credentials:
            self.credentials = self.get_credentials()
        
        if not self.credentials:
            return None
        
        try:
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return self.service
        except Exception as e:
            print(f"Error building service: {e}")
            return None
    
    def get_events(self, time_min=None, time_max=None, max_results=10):
        """Get calendar events"""
        if not self.service:
            self.service = self.build_service()
        
        if not self.service:
            return []
        
        try:
            if not time_min:
                time_min = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as error:
            print(f"Error getting events: {error}")
            return []
    
    def create_event(self, event_data):
        """Create a new calendar event"""
        if not self.service:
            self.service = self.build_service()
        
        if not self.service:
            return None
        
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            return event
            
        except HttpError as error:
            print(f"Error creating event: {error}")
            return None
    
    def update_event(self, event_id, event_data):
        """Update an existing calendar event"""
        if not self.service:
            self.service = self.build_service()
        
        if not self.service:
            return None
        
        try:
            event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event_data
            ).execute()
            
            return event
            
        except HttpError as error:
            print(f"Error updating event: {error}")
            return None
    
    def delete_event(self, event_id):
        """Delete a calendar event"""
        if not self.service:
            self.service = self.build_service()
        
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return True
            
        except HttpError as error:
            print(f"Error deleting event: {error}")
            return False
    
    def get_free_busy(self, time_min, time_max):
        """Get free/busy information for a time period"""
        if not self.service:
            self.service = self.build_service()
        
        if not self.service:
            return None
        
        try:
            body = {
                'timeMin': time_min,
                'timeMax': time_max,
                'items': [{'id': 'primary'}]
            }
            
            events_result = self.service.freebusy().query(body=body).execute()
            return events_result.get('calendars', {}).get('primary', {})
            
        except HttpError as error:
            print(f"Error getting free/busy: {error}")
            return None 