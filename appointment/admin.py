from django.contrib import admin
from .models import CalendarEvent, AvailableTimeSlot, Client, ClientAuditTrail
from unfold.admin import ModelAdmin

@admin.register(CalendarEvent)
class CalendarEventAdmin(ModelAdmin):
    list_display = ['title', 'user', 'start_time', 'end_time', 'is_all_day']
    list_filter = ['is_all_day', 'created_at', 'start_time']
    search_fields = ['title', 'description', 'user__username']
    date_hierarchy = 'start_time'
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(AvailableTimeSlot)
class AvailableTimeSlotAdmin(ModelAdmin):
    list_display = ['user', 'day_of_week', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']
    search_fields = ['user__username']

@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ClientAuditTrail)
class ClientAuditTrailAdmin(ModelAdmin):
    list_display = ['client', 'action', 'changed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['client__first_name', 'client__last_name', 'changed_by__username']
    readonly_fields = ['timestamp']
