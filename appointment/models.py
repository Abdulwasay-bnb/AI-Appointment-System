from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class CalendarEvent(models.Model):
    """Model to store calendar events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True, null=True)
    google_event_id = models.CharField(max_length=100, blank=True, null=True)
    microsoft_event_id = models.CharField(max_length=256, blank=True, null=True)
    is_all_day = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class AvailableTimeSlot(models.Model):
    """Model to store available time slots for appointments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='available_slots')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'day_of_week', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class Client(models.Model):
    """Model to store client information for each user (soft delete supported)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Soft delete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'email']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class ClientAuditTrail(models.Model):
    """Model to log changes to Client objects for audit purposes"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='audit_trails')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    change_details = models.TextField(blank=True, null=True)  # JSON or text description

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.client} - {self.action} at {self.timestamp}"
