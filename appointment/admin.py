from django.contrib import admin
from .models import CalendarEvent, AvailableTimeSlot

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'start_time', 'end_time', 'is_all_day', 'created_at']
    list_filter = ['is_all_day', 'created_at', 'start_time']
    search_fields = ['title', 'description', 'user__username']
    date_hierarchy = 'start_time'
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(AvailableTimeSlot)
class AvailableTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['user', 'day_of_week', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']
    search_fields = ['user__username']
