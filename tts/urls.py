from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.tts_index, name='tts_index'),
    path('audio/<str:filename>', views.serve_audio, name='tts_audio'),
]