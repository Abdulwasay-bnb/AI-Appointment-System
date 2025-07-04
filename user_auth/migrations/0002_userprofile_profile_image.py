# Generated by Django 5.2.1 on 2025-06-03 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='profile_image',
            field=models.ImageField(default='default_profile_image.png', help_text='Profile image for the user.', upload_to='profile_images/'),
        ),
    ]
