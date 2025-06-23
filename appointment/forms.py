from django import forms
from django.utils import timezone
from .models import CalendarEvent, AvailableTimeSlot, Client
from user_auth.models import UserProfile
from django.conf import settings

class CalendarEventForm(forms.ModelForm):
    """Form for creating and editing calendar events"""
    
    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'start_time', 'end_time', 'location', 'is_all_day']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Event description (optional)'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Event location (optional)'
            }),
            'is_all_day': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default times if creating new event
        if not self.instance.pk:
            now = timezone.now()
            # Round to nearest 30 minutes
            minutes = (now.minute // 30) * 30
            now = now.replace(minute=minutes, second=0, microsecond=0)
            self.fields['start_time'].initial = now
            self.fields['end_time'].initial = now + timezone.timedelta(hours=1)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        is_all_day = cleaned_data.get('is_all_day')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            
            if not is_all_day:
                # For non-all-day events, ensure minimum duration
                duration = end_time - start_time
                if duration.total_seconds() < 300:  # 5 minutes
                    raise forms.ValidationError("Event must be at least 5 minutes long.")
        
        return cleaned_data

class AvailableTimeSlotForm(forms.ModelForm):
    """Form for creating available time slots"""
    
    class Meta:
        model = AvailableTimeSlot
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
            'day_of_week': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'time'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            
            # Ensure minimum slot duration
            duration = (end_time.hour - start_time.hour) * 60 + (end_time.minute - start_time.minute)
            if duration < 30:
                raise forms.ValidationError("Time slot must be at least 30 minutes long.")
        
        return cleaned_data

class UserCalendarSettingsForm(forms.ModelForm):
    """Form for managing user calendar settings"""
    
    class Meta:
        model = UserProfile
        fields = [
            'google_calendar_sync_enabled',
            'default_event_duration',
            'working_hours_start',
            'working_hours_end',
            'timezone',
            'show_weekends',
            'first_day_of_week',
            'email_notifications',
            'reminder_minutes'
        ]
        widgets = {
            'google_calendar_sync_enabled': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'default_event_duration': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }, choices=[
                (15, '15 minutes'),
                (30, '30 minutes'),
                (45, '45 minutes'),
                (60, '1 hour'),
                (90, '1.5 hours'),
                (120, '2 hours'),
                (180, '3 hours'),
                (240, '4 hours'),
            ]),
            'working_hours_start': forms.TimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'time'
            }),
            'working_hours_end': forms.TimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'time'
            }),
            'timezone': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }, choices=[
                ('UTC', 'UTC'),
                ('America/New_York', 'Eastern Time'),
                ('America/Chicago', 'Central Time'),
                ('America/Denver', 'Mountain Time'),
                ('America/Los_Angeles', 'Pacific Time'),
                ('Europe/London', 'London'),
                ('Europe/Paris', 'Paris'),
                ('Asia/Tokyo', 'Tokyo'),
                ('Asia/Shanghai', 'Shanghai'),
                ('Australia/Sydney', 'Sydney'),
            ]),
            'show_weekends': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'first_day_of_week': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'reminder_minutes': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }, choices=[
                (5, '5 minutes'),
                (10, '10 minutes'),
                (15, '15 minutes'),
                (30, '30 minutes'),
                (60, '1 hour'),
                (120, '2 hours'),
                (1440, '1 day'),
            ]),
        }

class QuickEventForm(forms.Form):
    """Quick form for creating simple events"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Event title'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'date'
        })
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'time'
        })
    )
    duration = forms.ChoiceField(
        choices=[
            (30, '30 minutes'),
            (60, '1 hour'),
            (90, '1.5 hours'),
            (120, '2 hours'),
            (180, '3 hours'),
            (240, '4 hours'),
        ],
        initial=60,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    ) 

def get_google_credentials_dict(self):
    if not self.is_google_calendar_connected:
        return None

    return {
        'token': self.google_access_token,
        'refresh_token': self.google_refresh_token,
        'token_uri': "https://oauth2.googleapis.com/token",
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'scopes': ['https://www.googleapis.com/auth/calendar']
    } 

class ClientForm(forms.ModelForm):
    """Form for creating and updating Client objects"""
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'notes', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Phone number (optional)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'rows': 2,
                'placeholder': 'Address (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'rows': 2,
                'placeholder': 'Notes (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        user = self.user or (self.instance.user if self.instance.pk else None)
        if not user:
            return email
        qs = Client.objects.filter(user=user, email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A client with this email already exists for your account.')
        return email 