# Appointment System with Google Calendar Integration

A comprehensive Django application for managing appointments and events with Google Calendar integration.

## Features

### Core Calendar Features
- **Full Calendar View**: Interactive calendar with month, week, and day views
- **Event Management**: Create, edit, delete, and view calendar events
- **Available Time Slots**: Manage available appointment times
- **Event Details**: Rich event information with descriptions and locations
- **Responsive Design**: Mobile-friendly interface

### Google Calendar Integration
- **OAuth Authentication**: Secure Google Calendar connection
- **Two-way Sync**: Events sync between local calendar and Google Calendar
- **Automatic Updates**: Real-time synchronization of events
- **Token Management**: Automatic token refresh and management

### User Profile & Settings
- **Personalized Settings**: Each user has their own calendar preferences
- **Google Calendar Credentials**: Individual Google Calendar integration per user
- **Calendar Preferences**: 
  - Default event duration
  - Working hours
  - Timezone settings
  - Weekend display options
  - First day of week preference
- **Notification Settings**: Email notifications and reminder times
- **Sync Controls**: Enable/disable Google Calendar synchronization

### Advanced Features
- **API Endpoints**: RESTful API for calendar events
- **Availability Checking**: Check availability for specific dates/times
- **Quick Event Creation**: Fast event creation from calendar interface
- **Event Statistics**: Dashboard with event counts and upcoming events

## Models

### UserProfile (Extended)
```python
# Google Calendar Integration
google_calendar_id = CharField(default='primary')
google_access_token = TextField()
google_refresh_token = TextField()
google_token_expiry = DateTimeField()
google_calendar_connected = BooleanField(default=False)
google_calendar_sync_enabled = BooleanField(default=True)

# Calendar Settings
default_event_duration = IntegerField(default=60)
working_hours_start = TimeField(default='09:00')
working_hours_end = TimeField(default='17:00')
timezone = CharField(default='UTC')

# Calendar Preferences
show_weekends = BooleanField(default=True)
first_day_of_week = IntegerField(choices=[(0, 'Sunday'), (1, 'Monday')])

# Notification Settings
email_notifications = BooleanField(default=True)
reminder_minutes = IntegerField(default=15)
```

### CalendarEvent
```python
id = UUIDField(primary_key=True)
user = ForeignKey(User)
title = CharField(max_length=200)
description = TextField()
start_time = DateTimeField()
end_time = DateTimeField()
location = CharField(max_length=200)
google_event_id = CharField(max_length=100)
is_all_day = BooleanField(default=False)
```

### AvailableTimeSlot
```python
user = ForeignKey(User)
day_of_week = IntegerField(choices=DAYS_OF_WEEK)
start_time = TimeField()
end_time = TimeField()
is_available = BooleanField(default=True)
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Google Calendar API Setup

#### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API

#### Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Download the JSON file
5. Rename to `credentials.json` and place in project root

#### Update Settings
Add to your `.env` file:
```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Run Development Server
```bash
python manage.py runserver
```

## Usage

### For Users

#### 1. Calendar Settings
- Navigate to Calendar > Settings
- Configure your preferences:
  - Default event duration
  - Working hours
  - Timezone
  - Display options
  - Notification settings

#### 2. Google Calendar Connection
- Click "Connect Google Calendar" in settings
- Authorize the application
- Enable/disable automatic sync
- Manual sync option available

#### 3. Creating Events
- Use "Add Event" button for full event creation
- Use "Quick Add Event" for simple events
- Events automatically sync to Google Calendar (if connected)

#### 4. Managing Available Slots
- Set your available time slots
- Define working hours per day
- Control availability for appointments

### For Administrators

#### User Management
- View all users and their calendar settings
- Monitor Google Calendar connections
- Manage user preferences through admin interface

#### Calendar Management
- View all events across users
- Manage available time slots
- Monitor system usage

## API Endpoints

### Events API
- `GET /appointment/api/events/` - Get user's events
- `POST /appointment/api/events/` - Create new event
- `PUT /appointment/api/events/{id}/` - Update event
- `DELETE /appointment/api/events/{id}/` - Delete event

### Availability API
- `GET /appointment/api/availability/?date=YYYY-MM-DD&time=HH:MM` - Check availability

## Security Features

- **OAuth 2.0**: Secure Google Calendar authentication
- **Token Encryption**: Secure storage of access tokens
- **User Isolation**: Each user's data is isolated
- **CSRF Protection**: Built-in Django CSRF protection
- **Login Required**: All views require authentication

## Customization

### Adding New Calendar Settings
1. Add fields to `UserProfile` model
2. Update `UserCalendarSettingsForm`
3. Add to admin interface
4. Update settings template

### Custom Event Types
1. Extend `CalendarEvent` model
2. Add event type field
3. Update forms and templates
4. Add filtering options

### Additional Integrations
1. Create new service class (similar to `GoogleCalendarService`)
2. Add integration fields to `UserProfile`
3. Update views and templates
4. Add admin interface

## Troubleshooting

### Google Calendar Connection Issues
1. Check credentials.json file exists
2. Verify OAuth redirect URI matches
3. Ensure Google Calendar API is enabled
4. Check token expiration

### Sync Issues
1. Verify user has Google Calendar connected
2. Check sync is enabled in user settings
3. Review error logs for API issues
4. Try manual sync

### Performance Issues
1. Optimize database queries
2. Implement caching for calendar data
3. Use pagination for large event lists
4. Monitor API rate limits

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

This project is licensed under the MIT License. 