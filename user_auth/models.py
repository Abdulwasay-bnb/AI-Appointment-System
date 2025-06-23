from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.conf import settings  # Import here to avoid circular import

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_client_portal_user = models.BooleanField(default=False, help_text="Designates whether this user can access the client portal.")
    profile_image = models.ImageField(upload_to='profile_images/', default='default_profile_image.png', help_text="Profile image for the user.")
    
    # Google Calendar Integration Fields
    google_calendar_id = models.CharField(max_length=100, default='primary', help_text="Google Calendar ID (usually 'primary')")
    google_access_token = models.TextField(blank=True, null=True, help_text="Google OAuth access token")
    google_refresh_token = models.TextField(blank=True, null=True, help_text="Google OAuth refresh token")
    google_token_expiry = models.DateTimeField(blank=True, null=True, help_text="Token expiration time")
    google_calendar_connected = models.BooleanField(default=False, help_text="Whether Google Calendar is connected")
    google_calendar_sync_enabled = models.BooleanField(default=True, help_text="Whether to sync events with Google Calendar")
    
    # Calendar Settings
    default_event_duration = models.IntegerField(default=60, help_text="Default event duration in minutes")
    working_hours_start = models.TimeField(default='09:00', help_text="Default working hours start time")
    working_hours_end = models.TimeField(default='17:00', help_text="Default working hours end time")
    timezone = models.CharField(max_length=50, default='UTC', help_text="User's timezone")
    
    # Calendar Preferences
    show_weekends = models.BooleanField(default=True, help_text="Whether to show weekends in calendar")
    first_day_of_week = models.IntegerField(default=0, choices=[
        (0, 'Sunday'),
        (1, 'Monday'),
    ], help_text="First day of the week")
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True, help_text="Send email notifications for events")
    reminder_minutes = models.IntegerField(default=15, help_text="Default reminder time in minutes")
    
    # Created and Updated timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.username
    
    @property
    def is_google_calendar_connected(self):
        """Check if Google Calendar is properly connected"""
        return (
            self.google_calendar_connected and 
            self.google_access_token and 
            self.google_refresh_token
        )
    
    def get_google_credentials_dict(self):
        """Get Google credentials as a dictionary for the service"""
        if not self.is_google_calendar_connected:
            return None
        return {
            'token': self.google_access_token,
            'refresh_token': self.google_refresh_token,
            'token_uri': "https://oauth2.googleapis.com/token",
            'client_id': settings.CLIENT_ID,  # Use from settings
            'client_secret': settings.CLIENT_SECRET,  # Use from settings
            'scopes': ['https://www.googleapis.com/auth/calendar']
        }
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
