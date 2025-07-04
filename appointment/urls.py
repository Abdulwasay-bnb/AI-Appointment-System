from django.urls import path
from . import views

app_name = 'appointment'

urlpatterns = [
    # Calendar views
    path('', views.calendar_view, name='calendar'),
    path('settings/', views.calendar_settings, name='calendar_settings'),
    
    # Google Calendar integration
    path('google/auth/', views.google_calendar_auth, name='google_calendar_auth'),
    path('google/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('google/disconnect/', views.google_calendar_disconnect, name='google_calendar_disconnect'),
    path('google/sync/', views.google_calendar_sync, name='google_calendar_sync'),
    path('google/test/', views.test_google_credentials, name='test_google_credentials'),
    
    # Microsoft Calendar integration
    path('microsoft/auth/', views.microsoft_calendar_auth, name='microsoft_calendar_auth'),
    path('microsoft/callback/', views.microsoft_calendar_callback, name='microsoft_calendar_callback'),
    path('microsoft/disconnect/', views.microsoft_calendar_disconnect, name='microsoft_calendar_disconnect'),
    path('microsoft/sync/', views.microsoft_calendar_sync, name='microsoft_calendar_sync'),
    
    # Event management
    path('events/', views.event_list, name='event_list'),
    path('event/create/', views.event_create, name='event_create'),
    path('event/<uuid:event_id>/', views.event_detail, name='event_detail'),
    path('event/<uuid:event_id>/update/', views.event_update, name='event_update'),
    path('event/<uuid:event_id>/edit/', views.event_update, name='event_update'),
    path('event/<uuid:event_id>/delete/', views.event_delete, name='event_delete'),
    
    # Available time slots
    path('slots/', views.available_slots, name='available_slots'),
    path('slot/<int:slot_id>/delete/', views.slot_delete, name='slot_delete'),
    
    # API endpoints
    path('api/events/', views.api_events, name='api_events'),
    path('api/availability/', views.check_availability, name='check_availability'),
    
    # Client management
    path('clients/', views.client_list, name='client_list'),
    path('client/create/', views.client_create, name='client_create'),
    path('client/<int:client_id>/', views.client_detail, name='client_detail'),
    path('client/<int:client_id>/update/', views.client_update, name='client_update'),
    path('client/<int:client_id>/delete/', views.client_delete, name='client_delete'),
    path('client/<int:client_id>/restore/', views.client_restore, name='client_restore'),
] 