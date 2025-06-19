from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserAudio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_files')
    file = models.FileField(upload_to='user_audio/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"
