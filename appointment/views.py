from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import json
import datetime
from datetime import timedelta
from .models import CalendarEvent, AvailableTimeSlot, Client, ClientAuditTrail
from .google_calendar_service import GoogleCalendarService
from .forms import CalendarEventForm, AvailableTimeSlotForm, UserCalendarSettingsForm, ClientForm
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from user_auth.models import UserProfile
import os
import pytz
from django.db.models import Q
import csv

@login_required
def calendar_settings(request):
    """Manage calendar settings"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserCalendarSettingsForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calendar settings updated successfully!')
            return redirect('appointment:calendar_settings')
    else:
        form = UserCalendarSettingsForm(instance=user_profile)
    
    context = {
        'form': form,
        'user_profile': user_profile,
    }
    
    return render(request, 'appointment/calendar_settings.html', context)

@login_required
def google_calendar_auth(request):
    """Handle Google Calendar OAuth authentication"""
    try:
        # Check if credentials file exists
        credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        if not os.path.exists(credentials_path):
            messages.error(request, 'Google OAuth credentials not configured. Please contact the administrator.')
            return redirect('appointment:calendar_settings')
        
        # Test reading credentials file
        try:
            with open(credentials_path, 'r') as f:
                creds_data = json.load(f)
            print(f"DEBUG: Credentials file loaded successfully. Keys: {list(creds_data.keys())}")
        except Exception as e:
            print(f"DEBUG: Error reading credentials file: {e}")
            messages.error(request, f'Error reading credentials file: {str(e)}')
            return redirect('appointment:calendar_settings')
        
        # Create flow instance with all the scopes that Google might return
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ],
            redirect_uri='http://localhost:8000/appointment/google/callback/'
        )
        
        # Get authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        print(f"DEBUG: Authorization URL generated: {authorization_url[:100]}...")
        
        # Store state in session
        request.session['google_auth_state'] = state
        
        return redirect(authorization_url)
        
    except Exception as e:
        print(f"DEBUG: Exception in auth: {str(e)}")
        messages.error(request, f'Error setting up Google Calendar authentication: {str(e)}')
        return redirect('appointment:calendar_settings')

@login_required
def google_calendar_callback(request):
    """Handle Google Calendar OAuth callback"""
    try:
        # Get authorization code from request
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        print(f"DEBUG: OAuth callback received - code: {code[:10]}..., state: {state}, error: {error}")
        
        # Check for OAuth errors
        if error:
            messages.error(request, f'Google OAuth error: {error}')
            return redirect('appointment:calendar_settings')
        
        # Verify state
        if state != request.session.get('google_auth_state'):
            messages.error(request, 'Invalid state parameter. Please try again.')
            return redirect('appointment:calendar_settings')
        
        # Check if credentials file exists
        credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        if not os.path.exists(credentials_path):
            messages.error(request, 'Google OAuth credentials not configured. Please contact the administrator.')
            return redirect('appointment:calendar_settings')
        
        print(f"DEBUG: Using credentials file: {credentials_path}")
        
        # Create flow instance with the same scopes as auth
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'openid'
            ],
            redirect_uri='http://localhost:8000/appointment/google/callback/'
        )
        
        print("DEBUG: Flow created successfully")
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        print(f"DEBUG: Credentials obtained - token: {credentials.token[:10]}..., refresh_token: {credentials.refresh_token[:10] if credentials.refresh_token else 'None'}...")
        
        # Save credentials to user's profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        print(f"DEBUG: UserProfile {'created' if created else 'retrieved'} for user: {request.user.username}")
        
        user_profile.google_access_token = credentials.token
        # Only update refresh_token if a new one is provided
        if credentials.refresh_token:
            user_profile.google_refresh_token = credentials.refresh_token
        user_profile.google_token_expiry = timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - timezone.now().timestamp())
        user_profile.google_calendar_connected = True
        
        print(f"DEBUG: About to save UserProfile with token: {user_profile.google_access_token[:10]}...")
        user_profile.save()
        print("DEBUG: UserProfile saved successfully")
        
        messages.success(request, 'Google Calendar connected successfully! You can now sync your events.')
        
    except Exception as e:
        print(f"DEBUG: Exception in callback: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        messages.error(request, f'Error connecting Google Calendar: {str(e)}')
    
    return redirect('appointment:calendar_settings')

@login_required
def google_calendar_disconnect(request):
    """Disconnect Google Calendar"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        user_profile.google_calendar_connected = False
        user_profile.google_access_token = None
        user_profile.google_refresh_token = None
        user_profile.google_token_expiry = None
        user_profile.save()
        
        messages.success(request, 'Google Calendar disconnected successfully!')
        
    except UserProfile.DoesNotExist:
        messages.info(request, 'Google Calendar was not connected.')
    
    return redirect('appointment:calendar')

@login_required
def calendar_view(request):
    """Main calendar view"""
    # Get Google Calendar connection status
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        google_connected = user_profile.is_google_calendar_connected
    except UserProfile.DoesNotExist:
        google_connected = False
    
    # Get statistics
    events_count = CalendarEvent.objects.filter(user=request.user).count()
    upcoming_events = CalendarEvent.objects.filter(
        user=request.user,
        start_time__gte=timezone.now()
    ).count()
    available_slots = AvailableTimeSlot.objects.filter(user=request.user, is_available=True).count()
    
    context = {
        'google_connected': google_connected,
        'events_count': events_count,
        'upcoming_events': upcoming_events,
        'available_slots': available_slots,
    }
    
    return render(request, 'appointment/calendar.html', context)

@login_required
def event_list(request):
    """List all events"""
    events = CalendarEvent.objects.filter(user=request.user).order_by('start_time')
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'events': page_obj,
    }
    
    return render(request, 'appointment/event_list.html', context)

@login_required
def event_detail(request, event_id):
    """View event details"""
    event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
    
    context = {
        'event': event,
    }
    
    return render(request, 'appointment/event_detail.html', context)

@login_required
def event_create(request):
    """Create a new event"""
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            # Timezone fix: treat naive datetimes as user's local time, then convert to UTC
            user_profile = None
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                user_tz = pytz.timezone(user_profile.timezone or 'UTC')
            except Exception:
                user_tz = pytz.UTC
            if event.start_time and timezone.is_naive(event.start_time):
                local_dt = user_tz.localize(event.start_time)
                event.start_time = local_dt.astimezone(pytz.UTC)
            if event.end_time and timezone.is_naive(event.end_time):
                local_dt = user_tz.localize(event.end_time)
                event.end_time = local_dt.astimezone(pytz.UTC)
            
            # If Google Calendar is connected, create event there too
            try:
                if user_profile.is_google_calendar_connected and user_profile.google_calendar_sync_enabled:
                    google_service = GoogleCalendarService(request.user)
                    # Convert event times to user's timezone for Google Calendar
                    gcal_start = event.start_time.astimezone(user_tz)
                    gcal_end = event.end_time.astimezone(user_tz)
                    event_data = {
                        'summary': event.title,
                        'description': event.description or '',
                        'location': event.location or '',
                        'start': {
                            'dateTime': gcal_start.isoformat(),
                            'timeZone': user_profile.timezone,
                        },
                        'end': {
                            'dateTime': gcal_end.isoformat(),
                            'timeZone': user_profile.timezone,
                        },
                    }
                    if event.is_all_day:
                        event_data['start'] = {'date': event.start_time.date().isoformat()}
                        event_data['end'] = {'date': event.end_time.date().isoformat()}
                    google_event = google_service.create_event(event_data)
                    if google_event:
                        event.google_event_id = google_event['id']
            
            except UserProfile.DoesNotExist:
                pass
            
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('appointment:calendar')
    else:
        form = CalendarEventForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'appointment/event_form.html', context)

@login_required
def event_update(request, event_id):
    """Update an existing event"""
    event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
    
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            # Timezone fix: treat naive datetimes as user's local time, then convert to UTC
            user_profile = None
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                user_tz = pytz.timezone(user_profile.timezone or 'UTC')
            except Exception:
                user_tz = pytz.UTC
            if event.start_time and timezone.is_naive(event.start_time):
                local_dt = user_tz.localize(event.start_time)
                event.start_time = local_dt.astimezone(pytz.UTC)
            if event.end_time and timezone.is_naive(event.end_time):
                local_dt = user_tz.localize(event.end_time)
                event.end_time = local_dt.astimezone(pytz.UTC)
            
            # Update Google Calendar event if connected
            if event.google_event_id:
                try:
                    if user_profile.is_google_calendar_connected and user_profile.google_calendar_sync_enabled:
                        google_service = GoogleCalendarService(request.user)
                        # Convert event times to user's timezone for Google Calendar
                        gcal_start = event.start_time.astimezone(user_tz)
                        gcal_end = event.end_time.astimezone(user_tz)
                        event_data = {
                            'summary': event.title,
                            'description': event.description or '',
                            'location': event.location or '',
                            'start': {
                                'dateTime': gcal_start.isoformat(),
                                'timeZone': user_profile.timezone,
                            },
                            'end': {
                                'dateTime': gcal_end.isoformat(),
                                'timeZone': user_profile.timezone,
                            },
                        }
                        if event.is_all_day:
                            event_data['start'] = {'date': event.start_time.date().isoformat()}
                            event_data['end'] = {'date': event.end_time.date().isoformat()}
                        google_service.update_event(event.google_event_id, event_data)
                
                except UserProfile.DoesNotExist:
                    pass
            
            event.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('appointment:calendar')
    else:
        form = CalendarEventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'action': 'Update',
    }
    
    return render(request, 'appointment/event_form.html', context)

@login_required
def event_delete(request, event_id):
    """Delete an event"""
    event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
    
    if request.method == 'POST':
        # Delete from Google Calendar if connected
        if event.google_event_id:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if user_profile.is_google_calendar_connected:
                    google_service = GoogleCalendarService(request.user)
                    google_service.delete_event(event.google_event_id)
            except UserProfile.DoesNotExist:
                pass
        
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('appointment:calendar')
    
    context = {
        'event': event,
    }
    
    return render(request, 'appointment/event_confirm_delete.html', context)

@login_required
def available_slots(request):
    """Manage available time slots"""
    if request.method == 'POST':
        form = AvailableTimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.user = request.user
            slot.save()
            messages.success(request, 'Time slot added successfully!')
            return redirect('appointment:available_slots')
    else:
        form = AvailableTimeSlotForm()
    
    slots = AvailableTimeSlot.objects.filter(user=request.user).order_by('day_of_week', 'start_time')
    # Add duration_str and is_booked to each slot
    for slot in slots:
        start = slot.start_time
        end = slot.end_time
        # Calculate duration in minutes
        duration_minutes = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        if hours and minutes:
            slot.duration_str = f"{hours}h {minutes}m"
        elif hours:
            slot.duration_str = f"{hours}h"
        else:
            slot.duration_str = f"{minutes}m"
        # Check if slot is booked (any event overlaps this slot on the same day of week)
        # Find next date for this day_of_week
        today = datetime.date.today()
        days_ahead = (slot.day_of_week - today.weekday()) % 7
        slot_date = today + datetime.timedelta(days=days_ahead)
        slot_start_dt = datetime.datetime.combine(slot_date, slot.start_time)
        slot_end_dt = datetime.datetime.combine(slot_date, slot.end_time)
        # Check for any event that overlaps this slot
        slot.is_booked = CalendarEvent.objects.filter(
            user=request.user,
            start_time__lt=slot_end_dt,
            end_time__gt=slot_start_dt
        ).exists()
        # Attach booked events for modal
        slot.booked_events = list(CalendarEvent.objects.filter(
            user=request.user,
            start_time__lt=slot_end_dt,
            end_time__gt=slot_start_dt
        ).values('title', 'start_time', 'end_time'))
    context = {
        'form': form,
        'slots': slots,
    }
    
    return render(request, 'appointment/available_slots.html', context)

@login_required
def slot_delete(request, slot_id):
    """Delete an available time slot"""
    slot = get_object_or_404(AvailableTimeSlot, id=slot_id, user=request.user)
    
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Time slot deleted successfully!')
        return redirect('appointment:available_slots')
    
    context = {
        'slot': slot,
    }
    
    return render(request, 'appointment/slot_confirm_delete.html', context)

@login_required
def google_calendar_sync(request):
    """Sync with Google Calendar"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.is_google_calendar_connected:
            messages.error(request, 'Google Calendar is not connected.')
            return redirect('appointment:calendar')
        
        google_service = GoogleCalendarService(request.user)
        events = google_service.get_events(max_results=50)
        
        # Sync events to local database
        synced_count = 0
        for google_event in events:
            event_id = google_event.get('id')
            
            # Check if event already exists
            if not CalendarEvent.objects.filter(google_event_id=event_id, user=request.user).exists():
                # Parse event data
                start_data = google_event.get('start', {})
                end_data = google_event.get('end', {})
                
                if 'dateTime' in start_data:
                    start_time = datetime.datetime.fromisoformat(start_data['dateTime'].replace('Z', '+00:00'))
                    end_time = datetime.datetime.fromisoformat(end_data['dateTime'].replace('Z', '+00:00'))
                    is_all_day = False
                else:
                    start_time = datetime.datetime.combine(
                        datetime.date.fromisoformat(start_data['date']),
                        datetime.time.min
                    )
                    end_time = datetime.datetime.combine(
                        datetime.date.fromisoformat(end_data['date']),
                        datetime.time.min
                    )
                    is_all_day = True
                
                # Create local event
                CalendarEvent.objects.create(
                    user=request.user,
                    title=google_event.get('summary', 'Untitled Event'),
                    description=google_event.get('description', ''),
                    location=google_event.get('location', ''),
                    start_time=start_time,
                    end_time=end_time,
                    is_all_day=is_all_day,
                    google_event_id=event_id
                )
                synced_count += 1
        
        messages.success(request, f'Synced {synced_count} new events from Google Calendar!')
        
    except Exception as e:
        messages.error(request, f'Error syncing with Google Calendar: {str(e)}')
    
    return redirect('appointment:calendar')

@login_required
@csrf_exempt
def api_events(request):
    """API endpoint for calendar events"""
    if request.method == 'GET':
        start = request.GET.get('start')
        end = request.GET.get('end')
        
        events = CalendarEvent.objects.filter(user=request.user)
        
        if start:
            events = events.filter(start_time__gte=start)
        if end:
            events = events.filter(end_time__lte=end)
        
        events_data = []
        for event in events:
            event_data = {
                'id': str(event.id),
                'title': event.title,
                'start': event.start_time.isoformat(),
                'end': event.end_time.isoformat(),
                'allDay': event.is_all_day,
                'url': f'/appointment/event/{event.id}/',
            }
            
            # Add description if available
            if event.description:
                event_data['description'] = event.description
            
            # Add location if available
            if event.location:
                event_data['location'] = event.location
            
            events_data.append(event_data)
        
        return JsonResponse(events_data, safe=False)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def check_availability(request):
    """Check availability for a specific date and time"""
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    
    if not date_str or not time_str:
        return JsonResponse({'available': False, 'error': 'Date and time required'})
    
    try:
        date_obj = datetime.date.fromisoformat(date_str)
        time_obj = datetime.time.fromisoformat(time_str)
        datetime_obj = datetime.datetime.combine(date_obj, time_obj)
        
        # Check if there are any conflicting events
        conflicting_events = CalendarEvent.objects.filter(
            user=request.user,
            start_time__lt=datetime_obj + timedelta(hours=1),
            end_time__gt=datetime_obj
        )
        
        # Check available time slots
        day_of_week = date_obj.weekday()
        available_slots = AvailableTimeSlot.objects.filter(
            user=request.user,
            day_of_week=day_of_week,
            start_time__lte=time_obj,
            end_time__gt=time_obj,
            is_available=True
        )
        
        is_available = not conflicting_events.exists() and available_slots.exists()
        
        return JsonResponse({
            'available': is_available,
            'conflicting_events': list(conflicting_events.values('title', 'start_time', 'end_time'))
        })
        
    except ValueError:
        return JsonResponse({'available': False, 'error': 'Invalid date or time format'})

@login_required
def test_google_credentials(request):
    """Test view to verify Google credentials setup"""
    try:
        credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')
        
        if not os.path.exists(credentials_path):
            return JsonResponse({
                'error': 'Credentials file not found',
                'path': credentials_path
            })
        
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        # Check if it's the correct format
        if 'installed' in creds_data:
            client_id = creds_data['installed']['client_id']
            redirect_uris = creds_data['installed']['redirect_uris']
        elif 'web' in creds_data:
            client_id = creds_data['web']['client_id']
            redirect_uris = creds_data['web']['redirect_uris']
        else:
            return JsonResponse({
                'error': 'Invalid credentials format - neither "installed" nor "web" found',
                'keys': list(creds_data.keys())
            })
        
        return JsonResponse({
            'success': True,
            'client_id': client_id,
            'redirect_uris': redirect_uris,
            'format': 'installed' if 'installed' in creds_data else 'web'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'type': type(e).__name__
        })

@login_required
def client_list(request):
    """Paginated, searchable, filterable list of clients for the current user, with bulk actions and CSV export."""
    query = request.GET.get('q', '')
    show_inactive = request.GET.get('show_inactive', '0') == '1'
    export = request.GET.get('export', '')
    clients = Client.objects.filter(user=request.user)
    if not show_inactive:
        clients = clients.filter(is_active=True)
    if query:
        clients = clients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    clients = clients.order_by('-created_at')

    # CSV export
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clients.csv"'
        writer = csv.writer(response)
        writer.writerow(['First Name', 'Last Name', 'Email', 'Phone', 'Address', 'Active', 'Created', 'Updated'])
        for c in clients:
            writer.writerow([c.first_name, c.last_name, c.email, c.phone, c.address, c.is_active, c.created_at, c.updated_at])
        return response

    # Bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected')
        if action in ['soft_delete', 'restore'] and selected_ids:
            for cid in selected_ids:
                client = Client.objects.filter(user=request.user, pk=cid).first()
                if client:
                    if action == 'soft_delete' and client.is_active:
                        client.is_active = False
                        client.save()
                        ClientAuditTrail.objects.create(client=client, action='deleted', changed_by=request.user, change_details='Bulk soft delete')
                    elif action == 'restore' and not client.is_active:
                        client.is_active = True
                        client.save()
                        ClientAuditTrail.objects.create(client=client, action='created', changed_by=request.user, change_details='Bulk restore')
            messages.success(request, f'Bulk action "{action}" completed.')
            return redirect('appointment:client_list')

    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'clients': page_obj,
        'page_obj': page_obj,
        'query': query,
        'show_inactive': show_inactive,
    }
    return render(request, 'appointment/client_list.html', context)

@login_required
def client_create(request):
    """Create a new client for the current user."""
    if request.method == 'POST':
        form = ClientForm(request.POST, user=request.user)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            ClientAuditTrail.objects.create(client=client, action='created', changed_by=request.user, change_details='Created client')
            messages.success(request, 'Client created successfully!')
            return redirect('appointment:client_list')
    else:
        form = ClientForm(user=request.user)
    return render(request, 'appointment/client_form.html', {'form': form})

@login_required
def client_update(request, client_id):
    """Update an existing client (must belong to current user)."""
    client = get_object_or_404(Client, pk=client_id, user=request.user)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client, user=request.user)
        if form.is_valid():
            form.save()
            ClientAuditTrail.objects.create(client=client, action='updated', changed_by=request.user, change_details='Updated client')
            messages.success(request, 'Client updated successfully!')
            return redirect('appointment:client_list')
    else:
        form = ClientForm(instance=client, user=request.user)
    return render(request, 'appointment/client_form.html', {'form': form, 'client': client})

@login_required
def client_detail(request, client_id):
    """View client profile and history (must belong to current user)."""
    client = get_object_or_404(Client, pk=client_id, user=request.user)
    audit_trails = client.audit_trails.all()
    # TODO: Add appointment and communication history
    return render(request, 'appointment/client_detail.html', {'client': client, 'audit_trails': audit_trails})

@login_required
def client_delete(request, client_id):
    """Soft delete a client (must belong to current user)."""
    client = get_object_or_404(Client, pk=client_id, user=request.user)
    if request.method == 'POST':
        client.is_active = False
        client.save()
        ClientAuditTrail.objects.create(client=client, action='deleted', changed_by=request.user, change_details='Soft deleted client')
        messages.success(request, 'Client deleted (soft) successfully!')
        return redirect('appointment:client_list')
    return render(request, 'appointment/client_confirm_delete.html', {'client': client})

@login_required
def client_restore(request, client_id):
    """Restore a soft-deleted client (must belong to current user)."""
    client = get_object_or_404(Client, pk=client_id, user=request.user, is_active=False)
    if request.method == 'POST':
        client.is_active = True
        client.save()
        ClientAuditTrail.objects.create(client=client, action='created', changed_by=request.user, change_details='Restored client')
        messages.success(request, 'Client restored successfully!')
        return redirect('appointment:client_list')
    return render(request, 'appointment/client_confirm_restore.html', {'client': client})