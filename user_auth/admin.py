from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin
from .models import UserProfile
from unfold.admin import StackedInline, TabularInline


admin.site.unregister(User)
admin.site.unregister(Group)

# Create an inline admin for UserProfile
class UserProfileInline(StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fields = (
        'is_client_portal_user', 'profile_image',
        'google_calendar_id', 'google_calendar_connected', 'google_calendar_sync_enabled',
        'default_event_duration', 'working_hours_start', 'working_hours_end', 'timezone',
        'show_weekends', 'first_day_of_week', 'email_notifications', 'reminder_minutes',
        'created_at', 'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_calendar_connected')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__google_calendar_connected')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_calendar_connected(self, obj):
        try:
            return obj.userprofile.google_calendar_connected
        except UserProfile.DoesNotExist:
            return False
    get_calendar_connected.boolean = True
    get_calendar_connected.short_description = 'Google Calendar Connected'

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ['user', 'google_calendar_connected', 'timezone', 'default_event_duration', 'created_at']
    list_filter = ['google_calendar_connected', 'google_calendar_sync_enabled', 'timezone', 'show_weekends', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_client_portal_user', 'profile_image')
        }),
        ('Microsoft Calendar Integration', {
            'fields': (
                'ms_calendar_connected', 'ms_access_token', 'ms_refresh_token', 'ms_token_expiry'
            ),
            'classes': ('collapse',)
        }),
        ('Google Calendar Integration', {
            'fields': (
                'google_calendar_id', 'google_calendar_connected', 'google_calendar_sync_enabled',
                'google_access_token', 'google_refresh_token', 'google_token_expiry'
            ),
            'classes': ('collapse',)
        }),
        ('Calendar Settings', {
            'fields': (
                'default_event_duration', 'working_hours_start', 'working_hours_end', 'timezone',
                'show_weekends', 'first_day_of_week'
            )
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'reminder_minutes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
