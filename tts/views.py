import torchaudio as ta
import os
from django.shortcuts import render
from django.http import FileResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# from chatterbox.tts import ChatterboxTTS
from dotenv import load_dotenv
from .models import UserAudio
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

load_dotenv()

UPLOAD_FOLDER = os.path.join(settings.MEDIA_ROOT, 'tts_uploads')
GENERATED_FOLDER = os.path.join(settings.MEDIA_ROOT, 'tts_generated')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# model = ChatterboxTTS.from_pretrained(device="cpu")

@login_required(login_url='login')
def tts_index(request):
    audio_url = None
    user_audio_files = UserAudio.objects.filter(user=request.user)
    if request.method == 'POST':
        text = request.POST.get('text')
        selected_audio_id = request.POST.get('selected_audio')
        audio_prompt = request.FILES.get('audio_prompt')
        audio_prompt_path = None
        # Handle new upload/record
        if audio_prompt and audio_prompt.name:
            filename = audio_prompt.name.replace(' ', '_')
            # Save directly to user_audio folder
            user_audio_path = os.path.join(settings.MEDIA_ROOT, 'user_audio', filename)
            os.makedirs(os.path.dirname(user_audio_path), exist_ok=True)
            with open(user_audio_path, 'wb+') as destination:
                for chunk in audio_prompt.chunks():
                    destination.write(chunk)
            # Save to DB with correct path
            user_audio = UserAudio.objects.create(
                user=request.user,
                file=f'user_audio/{filename}',
                original_filename=audio_prompt.name
            )
            audio_prompt_path = user_audio_path
        # Handle selection from previous uploads
        elif selected_audio_id:
            try:
                user_audio = UserAudio.objects.get(id=selected_audio_id, user=request.user)
                audio_prompt_path = user_audio.file.path
            except UserAudio.DoesNotExist:
                audio_prompt_path = None
        if text:
            if audio_prompt_path:
                wav = model.generate(text, audio_prompt_path=audio_prompt_path)
            else:
                wav = model.generate(text)
            output_path = os.path.join(GENERATED_FOLDER, f'output_{request.user.id}.wav')
            ta.save(output_path, wav, model.sr)
            audio_url = f"/tts/audio/output_{request.user.id}.wav"
    return render(request, 'tts/index.html', {'audio_url': audio_url, 'user_audio_files': user_audio_files})

def serve_audio(request, filename):
    file_path = os.path.join(GENERATED_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='audio/wav')
    else:
        raise Http404()