from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_client_portal_user = models.BooleanField(default=False, help_text="Designates whether this user can access the client portal.")
    profile_image = models.ImageField(upload_to='profile_images/', default='default_profile_image.png', help_text="Profile image for the user.")
    
    def __str__(self):
        return self.user.username
