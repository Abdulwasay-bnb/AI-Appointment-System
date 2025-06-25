from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from ollama import chat
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
import os
import pdfplumber
import fitz  # PyMuPDF
import docx
from .models import (
    BusinessInfo, BusinessDocument, FAQEntry, AboutUsInfo, ServiceInfo, PricingInfo, PolicyInfo, TrainingMaterial, CallScript
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
from transformers import Speech2TextProcessor, Speech2TextForConditionalGeneration
import torch
from appointment.models import AvailableTimeSlot
from pydub import AudioSegment

# Create your views here.

@csrf_exempt
def chatbot_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            if not user_message:
                return JsonResponse({'error': 'No message provided.'}, status=400)
            response = chat(model='llama3.2:1B', messages=[
                {'role': 'user', 'content': user_message},
            ])
            bot_reply = response.message.content
            return JsonResponse({'reply': bot_reply})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        # For GET requests, render a simple chat form
        return render(request, 'llm/chatbot.html')

def extract_text_from_file(file_path, file_name):
    """Extract text from various file types"""
    ext = os.path.splitext(file_name)[1].lower()
    text = ''
    
    try:
        if ext == '.pdf':
            try:
                with pdfplumber.open(file_path) as pdf:
                    text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
            except Exception:
                doc = fitz.open(file_path)
                text = '\n'.join(page.get_text() for page in doc)
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(file_path)
            text = '\n'.join([p.text for p in doc.paragraphs])
        elif ext in ['.txt']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif ext in ['.xlsx', '.xls']:
            # For Excel files, we'll extract basic text content
            import pandas as pd
            df = pd.read_excel(file_path)
            text = df.to_string()
        else:
            return None, f'Unsupported file type: {ext}'
            
        return text, None
    except Exception as e:
        return None, f'Failed to extract text: {str(e)}'

def get_extraction_prompt(document_type, text):
    """Get appropriate extraction prompt based on document type"""
    base_prompt = f"""
You are an expert business analyst. Analyze the following {document_type} document and extract relevant business information.

Document Content:
{text}

"""
    if document_type == 'faq':
        return base_prompt + """
Extract and organize the following information as a JSON array of objects, each with these keys:
[
  {"question": "...", "answer": "..."}
]
If no FAQs are found, return an empty array. Return ONLY the JSON, no explanation or extra text.
"""
    elif document_type == 'about':
        return base_prompt + """
Extract the following information and return it as a JSON object with these keys:
{
  "company_history": "...",
  "mission": "...",
  "vision": "...",
  "core_values": "...",
  "team_info": "...",
  "achievements": "...",
  "unique_selling_points": "..."
}
If any field is missing, use an empty string. Return ONLY the JSON object, no explanation or extra text.
"""
    elif document_type == 'services':
        return base_prompt + """
Extract the following information as a JSON array of objects, each with these keys:
[
  {"service_name": "...", "description": "...", "target_audience": "...", "benefits": "...", "specialization": "..."}
]
If no services are found, return an empty array. Return ONLY the JSON, no explanation or extra text.
"""
    elif document_type == 'pricing':
        return base_prompt + """
Extract the following information as a JSON array of objects, each with these keys:
[
  {"service_or_package": "...", "price": "...", "payment_terms": "...", "discounts": "...", "additional_fees": "...", "notes": "..."}
]
If no pricing info is found, return an empty array. Return ONLY the JSON, no explanation or extra text.
"""
    elif document_type == 'policies':
        return base_prompt + """
Extract the following information as a JSON array of objects, each with these keys:
[
  {"policy_type": "...", "content": "..."}
]
If no policies are found, return an empty array. Return ONLY the JSON, no explanation or extra text.
"""
    elif document_type == 'training':
        return base_prompt + """
Extract the following information as a JSON array of objects, each with these keys:
[
  {"title": "...", "content": "..."}
]
If no training materials are found, return an empty array. Return ONLY the JSON, no explanation or extra text.
"""
    elif document_type == 'scripts':
        return base_prompt + """
Extract the following information as a JSON array of objects, each with these keys:
[
  {"script_type": "...", "content": "..."}
]
If no scripts are found, return an empty array. Return ONLY the JSON, no explanation or extra text.
"""
    else:
        return base_prompt + """
Extract any relevant business information as a JSON object. Return ONLY the JSON object, no explanation or extra text.
"""

def parse_and_store_extracted_content(document_type, extracted_content, business_doc):
    """
    Parse the extracted content and store it in the appropriate model(s) based on document_type.
    Returns a summary string of what was stored.
    """
    summary = ""
    try:
        data = None
        try:
            data = json.loads(extracted_content)
        except Exception:
            data = None
        # FAQ
        if document_type == 'faq':
            faqs = []
            if data and isinstance(data, list):
                faqs = data
            else:
                import re
                faqs = re.findall(r'Q[:：](.*?)A[:：](.*?)(?=Q[:：]|$)', extracted_content, re.DOTALL|re.IGNORECASE)
                faqs = [{'question': q.strip(), 'answer': a.strip()} for q, a in faqs]
            for faq in faqs:
                if faq.get('question') and faq.get('answer'):
                    FAQEntry.objects.create(document=business_doc, question=faq['question'], answer=faq['answer'])
            summary = f"Stored {len(faqs)} FAQ entries."
        # About Us
        elif document_type == 'about':
            if data and isinstance(data, dict):
                AboutUsInfo.objects.create(
                    document=business_doc,
                    company_history=data.get('company_history', ''),
                    mission=data.get('mission', ''),
                    vision=data.get('vision', ''),
                    core_values=data.get('core_values', ''),
                    team_info=data.get('team_info', ''),
                    achievements=data.get('achievements', ''),
                    unique_selling_points=data.get('unique_selling_points', ''),
                )
                summary = "About Us info stored."
            else:
                # Fallback: try to extract all fields using regex
                import re
                def extract_field(field):
                    match = re.search(rf"{field}[:：]\s*(.*?)(?=\n\w+[:：]|$)", extracted_content, re.IGNORECASE|re.DOTALL)
                    return match.group(1).strip() if match else ''
                AboutUsInfo.objects.create(
                    document=business_doc,
                    company_history=extract_field('company_history'),
                    mission=extract_field('mission'),
                    vision=extract_field('vision'),
                    core_values=extract_field('core_values'),
                    team_info=extract_field('team_info'),
                    achievements=extract_field('achievements'),
                    unique_selling_points=extract_field('unique_selling_points'),
                )
                summary = "About Us info (regex fallback) stored."
        # Services
        elif document_type == 'services':
            services = []
            if data and isinstance(data, list):
                services = data
            elif data and isinstance(data, dict):
                # Accept any key that contains 'service' in its name and is a list
                for k, v in data.items():
                    if 'service' in k.lower() and isinstance(v, list):
                        services = v
                        break
            else:
                # Fallback: parse Service: ... Description: ...
                import re
                services = re.findall(r'Service[:：](.*?)Description[:：](.*?)(?=Service[:：]|$)', extracted_content, re.DOTALL|re.IGNORECASE)
                services = [{'service_name': s[0].strip(), 'description': s[1].strip()} for s in services]
            for s in services:
                ServiceInfo.objects.create(
                    document=business_doc,
                    service_name=s.get('service_name', ''),
                    description=s.get('description', ''),
                    target_audience=', '.join(s['target_audience']) if isinstance(s.get('target_audience'), list) else s.get('target_audience', ''),
                    benefits=', '.join(s['benefits']) if isinstance(s.get('benefits'), list) else s.get('benefits', ''),
                    specialization=', '.join(s['specialization']) if isinstance(s.get('specialization'), list) else s.get('specialization', ''),
                )
            summary = f"Stored {len(services)} services."
        # Pricing
        elif document_type == 'pricing':
            pricings = []
            if data and isinstance(data, list):
                pricings = data
            elif data and isinstance(data, dict) and 'pricing' in data and isinstance(data['pricing'], list):
                pricings = data['pricing']
            elif data and isinstance(data, dict) and 'pricings' in data and isinstance(data['pricings'], list):
                pricings = data['pricings']
            else:
                # Fallback: parse Package: ... Price: ...
                import re
                pricings = re.findall(r'(Service|Package)[:：](.*?)Price[:：](.*?)(?=(Service|Package)[:：]|$)', extracted_content, re.DOTALL|re.IGNORECASE)
                pricings = [{'service_or_package': p[1].strip(), 'price': p[2].strip()} for p in pricings]
            for p in pricings:
                PricingInfo.objects.create(
                    document=business_doc,
                    service_or_package=p.get('service_or_package', ''),
                    price=p.get('price', ''),
                    payment_terms=p.get('payment_terms', ''),
                    discounts=p.get('discounts', ''),
                    additional_fees=p.get('additional_fees', ''),
                    notes=p.get('notes', ''),
                )
            summary = f"Stored {len(pricings)} pricing entries."
        # Policies
        elif document_type == 'policies':
            policies = []
            if data and isinstance(data, list):
                policies = data
            elif data and isinstance(data, dict) and 'policies' in data and isinstance(data['policies'], list):
                policies = data['policies']
            else:
                # Fallback: parse Policy: ... Content: ...
                import re
                policies = re.findall(r'Policy[:：](.*?)Content[:：](.*?)(?=Policy[:：]|$)', extracted_content, re.DOTALL|re.IGNORECASE)
                policies = [{'policy_type': p[0].strip(), 'content': p[1].strip()} for p in policies]
            for p in policies:
                PolicyInfo.objects.create(
                    document=business_doc,
                    policy_type=p.get('policy_type', ''),
                    content=p.get('content', ''),
                )
            summary = f"Stored {len(policies)} policies."
        # Training
        elif document_type == 'training':
            trainings = []
            if data and isinstance(data, list):
                trainings = data
            elif data and isinstance(data, dict) and 'training' in data and isinstance(data['training'], list):
                trainings = data['training']
            elif data and isinstance(data, dict) and 'trainings' in data and isinstance(data['trainings'], list):
                trainings = data['trainings']
            else:
                # Fallback: parse Title: ... Content: ...
                import re
                trainings = re.findall(r'Title[:：](.*?)Content[:：](.*?)(?=Title[:：]|$)', extracted_content, re.DOTALL|re.IGNORECASE)
                trainings = [{'title': t[0].strip(), 'content': t[1].strip()} for t in trainings]
            for t in trainings:
                TrainingMaterial.objects.create(
                    document=business_doc,
                    title=t.get('title', ''),
                    content=t.get('content', ''),
                )
            summary = f"Stored {len(trainings)} training materials."
        # Scripts
        elif document_type == 'scripts':
            scripts = []
            if data and isinstance(data, list):
                scripts = data
            elif data and isinstance(data, dict) and 'scripts' in data and isinstance(data['scripts'], list):
                scripts = data['scripts']
            else:
                # Fallback: parse Script Type: ... Content: ...
                import re
                scripts = re.findall(r'Script Type[:：](.*?)Content[:：](.*?)(?=Script Type[:：]|$)', extracted_content, re.DOTALL|re.IGNORECASE)
                scripts = [{'script_type': s[0].strip(), 'content': s[1].strip()} for s in scripts]
            for s in scripts:
                CallScript.objects.create(
                    document=business_doc,
                    script_type=s.get('script_type', ''),
                    content=s.get('content', ''),
                )
            summary = f"Stored {len(scripts)} call scripts."
        else:
            summary = "Document processed, but no structured storage for this type."
    except Exception as e:
        summary = f"Error parsing and storing structured data: {str(e)}"
    return summary

@csrf_exempt
def upload_business_doc(request):
    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        file = request.FILES.get('document')
        document_type = request.POST.get('document_type', 'other')
        
        if not file:
            return JsonResponse({'error': 'No document uploaded.'}, status=400)
        
        # Save file temporarily
        file_path = default_storage.save(f'business_docs/{file.name}', file)
        abs_path = default_storage.path(file_path)
        
        # Extract text from document
        text, error = extract_text_from_file(abs_path, file.name)
        if error:
            return JsonResponse({'error': error}, status=500)
        
        # Create BusinessDocument record
        business_doc = BusinessDocument.objects.create(
            user=user,
            document_type=document_type,
            document=file_path
        )
        
        # Extract relevant information using LLM
        try:
            prompt = get_extraction_prompt(document_type, text)
            print("\n--- LLM PROMPT ---\n", prompt)
            response = chat(model='llama3.2:1B', messages=[
                {'role': 'user', 'content': prompt},
            ])
            extracted_content = response.message.content if hasattr(response, 'message') else str(response)
            print("\n--- LLM extracted_content ---\n", extracted_content)
            if not extracted_content or not extracted_content.strip():
                business_doc.delete()
                return JsonResponse({'error': 'LLM returned no content. Is Ollama running and the model available?'}, status=500)
            # Update the document with extracted content
            business_doc.extracted_content = extracted_content
            business_doc.is_processed = True
            business_doc.save()
            # Parse and store structured data
            summary = parse_and_store_extracted_content(document_type, extracted_content, business_doc)
            return JsonResponse({
                'message': f'{business_doc.get_document_type_display()} processed successfully. {summary}',
                'document_id': business_doc.id,
                'extracted_content': extracted_content[:500] + '...' if len(extracted_content) > 500 else extracted_content
            })
        except Exception as e:
            import traceback
            print("\n--- LLM ERROR ---\n", traceback.format_exc())
            business_doc.delete()
            return JsonResponse({'error': f'Failed to process document: {str(e)}. Is Ollama running and the model available?'}, status=500)
    
    return JsonResponse({'error': 'Only POST allowed.'}, status=405)

@csrf_exempt
def upload_business_doc_legacy(request):
    """Legacy function for backward compatibility"""
    if request.method == 'POST':
        user = request.user if request.user.is_authenticated else None
        file = request.FILES.get('document')
        if not file:
            return JsonResponse({'error': 'No document uploaded.'}, status=400)
        # Save file temporarily
        file_path = default_storage.save(f'business_docs/{file.name}', file)
        abs_path = default_storage.path(file_path)
        # Extract text
        text, error = extract_text_from_file(abs_path, file.name)
        if error:
            return JsonResponse({'error': error}, status=500)
        
        # Use LLM to extract info
        prompt = f"""
You are an expert business analyst. Carefully read the following business document and extract the following fields.

For each field, if the information is not present or cannot be confidently determined, reply with "MISSING" for that field.

Return your answer as a JSON object with these keys:
- business_type (string, max 100 chars)
- services_offered (string or comma-separated list, max 300 chars)
- hours_of_operation (string, max 100 chars)
- booking_conditions (string, max 300 chars)
- contact_preferences (string, max 200 chars)

Each value should be concise and not exceed the specified character limit.

Document:
{text}

Respond ONLY with the JSON object, no explanation or extra text.
"""
        response = chat(model='llama3.2:1B', messages=[
            {'role': 'user', 'content': prompt},
        ])
        content = response.message.content
        def extract_field(field):
            import re
            match = re.search(rf"{field}:(.*?)(?:\n|$)", content, re.IGNORECASE)
            return match.group(1).strip() if match else ''
        fields = {
            'business_type': extract_field('Business type'),
            'services_offered': extract_field('Services offered'),
            'hours_of_operation': extract_field('Hours of operation'),
            'booking_conditions': extract_field('Booking conditions'),
            'contact_preferences': extract_field('Contact preferences'),
        }
        missing = [k for k, v in fields.items() if v.upper() == 'MISSING' or not v]
        # Save what we have
        business_info = BusinessInfo.objects.create(
            user=user,
            business_type=truncate(fields['business_type'], 100) if fields['business_type'].upper() != 'MISSING' else '',
            services_offered=truncate(fields['services_offered'], 300) if fields['services_offered'].upper() != 'MISSING' else '',
            hours_of_operation=truncate(fields['hours_of_operation'], 100) if fields['hours_of_operation'].upper() != 'MISSING' else '',
            booking_conditions=truncate(fields['booking_conditions'], 300) if fields['booking_conditions'].upper() != 'MISSING' else '',
            contact_preferences=truncate(fields['contact_preferences'], 200) if fields['contact_preferences'].upper() != 'MISSING' else '',
            document=file_path
        )
        if missing:
            return JsonResponse({
                'message': 'Some fields are missing. Please provide them.',
                'missing_fields': missing,
                'business_info_id': business_info.id
            })
        return JsonResponse({'message': 'Business info extracted and saved successfully.'})
    return JsonResponse({'error': 'Only POST allowed.'}, status=405)

@login_required
def business_upload_view(request):
    return render(request, 'llm/business_upload.html')

@login_required
def business_documents_view(request):
    """View to display uploaded business documents with structured data."""
    documents = BusinessDocument.objects.filter(user=request.user)
    # Build a dict of structured data for each document
    structured_data = {}
    for doc in documents:
        structured_data[doc.id] = {
            'faq_entries': [{k: str(v) for k, v in entry.items()} for entry in doc.faq_entries.values('question', 'answer')],
            'about_us': [{k: str(v) for k, v in entry.items()} for entry in doc.about_us_info.values()],
            'services': [{k: str(v) for k, v in entry.items()} for entry in doc.service_infos.values()],
            'pricing': [{k: str(v) for k, v in entry.items()} for entry in doc.pricing_infos.values()],
            'policies': [{k: str(v) for k, v in entry.items()} for entry in doc.policy_infos.values()],
            'training': [{k: str(v) for k, v in entry.items()} for entry in doc.training_materials.values()],
            'scripts': [{k: str(v) for k, v in entry.items()} for entry in doc.call_scripts.values()],
        }
    return render(request, 'llm/business_documents.html', {
        'documents': documents,
        'structured_data': structured_data,
    })

def truncate(val, maxlen):
    return val[:maxlen] if val and len(val) > maxlen else val

# Load models once
speech2text_model = Speech2TextForConditionalGeneration.from_pretrained("facebook/s2t-small-librispeech-asr")
speech2text_processor = Speech2TextProcessor.from_pretrained("facebook/s2t-small-librispeech-asr")

def get_business_context(user):
    try:
        context_parts = []
        
        # Get all FAQ entries for the user
        faqs = FAQEntry.objects.filter(document__user=user)
        if faqs.exists():
            context_parts.append("=== FAQS ===")
            for faq in faqs:
                context_parts.append(f"Q: {faq.question} A: {faq.answer}")
        
        # Get all About Us info for the user
        abouts = AboutUsInfo.objects.filter(document__user=user)
        if abouts.exists():
            context_parts.append("=== ABOUT US ===")
            for about in abouts:
                if about.mission:
                    context_parts.append(f"Mission: {about.mission}")
                if about.vision:
                    context_parts.append(f"Vision: {about.vision}")
                if about.unique_selling_points:
                    context_parts.append(f"USP: {about.unique_selling_points}")
                if about.core_values:
                    context_parts.append(f"Core Values: {about.core_values}")
                if about.achievements:
                    context_parts.append(f"Achievements: {about.achievements}")
        
        # Get all services for the user
        services = ServiceInfo.objects.filter(document__user=user)
        if services.exists():
            context_parts.append("=== SERVICES ===")
            for service in services:
                service_info = f"Service: {service.service_name}"
                if service.description:
                    service_info += f" - {service.description}"
                if service.target_audience:
                    service_info += f" (Target: {service.target_audience})"
                if service.benefits:
                    service_info += f" (Benefits: {service.benefits})"
                context_parts.append(service_info)
        
        # Get all pricing info for the user
        pricings = PricingInfo.objects.filter(document__user=user)
        if pricings.exists():
            context_parts.append("=== PRICING ===")
            for pricing in pricings:
                pricing_info = f"Package: {pricing.service_or_package} - {pricing.price}"
                if pricing.payment_terms:
                    pricing_info += f" (Terms: {pricing.payment_terms})"
                if pricing.discounts:
                    pricing_info += f" (Discounts: {pricing.discounts})"
                context_parts.append(pricing_info)
        
        # Get all policies for the user
        policies = PolicyInfo.objects.filter(document__user=user)
        if policies.exists():
            context_parts.append("=== POLICIES ===")
            for policy in policies:
                context_parts.append(f"Policy: {policy.policy_type} - {policy.content}")
        
        # Get all training materials for the user
        trainings = TrainingMaterial.objects.filter(document__user=user)
        if trainings.exists():
            context_parts.append("=== TRAINING MATERIALS ===")
            for training in trainings:
                context_parts.append(f"Training: {training.title} - {training.content[:200]}...")
        
        # Get all call scripts for the user
        scripts = CallScript.objects.filter(document__user=user)
        if scripts.exists():
            context_parts.append("=== CALL SCRIPTS ===")
            for script in scripts:
                script_type = script.script_type or "General"
                context_parts.append(f"Script ({script_type}): {script.content[:200]}...")
        
        if not context_parts:
            return "No business information available. Please upload business documents first."
        
        return '\n'.join(context_parts)
    except Exception as e:
        return f"(Error loading business context: {e})"

def get_available_slots(user):
    slots = AvailableTimeSlot.objects.filter(user=user, is_available=True)
    slot_strs = []
    for slot in slots:
        slot_strs.append(f"{slot.get_day_of_week_display()} {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}")
    return ", ".join(slot_strs)

@login_required
@csrf_exempt
def audio_chat_view(request):
    if request.method == 'POST':
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'error': 'No audio file provided.'}, status=400)
        # Save temp audio
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, audio_file.name)
        with open(temp_path, 'wb+') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        # Convert to wav and resample to 16kHz if needed
        wav_path = temp_path + '.wav'
        try:
            audio = AudioSegment.from_file(temp_path)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio.export(wav_path, format='wav')
        except Exception as e:
            return JsonResponse({'error': f'Audio conversion failed: {str(e)}'}, status=500)
        # Transcribe
        try:
            waveform, sr = ta.load(wav_path)
        except Exception as e:
            return JsonResponse({'error': f'Failed to load audio: {str(e)}'}, status=500)
        inputs = speech2text_processor(waveform.squeeze().numpy(), sampling_rate=sr, return_tensors="pt")
        with torch.no_grad():
            generated_ids = speech2text_model.generate(inputs["input_features"], attention_mask=inputs["attention_mask"])
        transcription = speech2text_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        # LLM prompt
        business_context = get_business_context(request.user)
        slots = get_available_slots(request.user)
        starter = f"Business info: {business_context} Available slots: {slots}"
        user_message = transcription
        prompt = f"{starter}\nClient: {user_message}\nAssistant:"
        from ollama import chat
        response = chat(model='llama3.2:1B', messages=[{'role': 'user', 'content': prompt}])
        bot_reply = response.message.content if hasattr(response, 'message') else str(response)
        # TTS
        output_path = os.path.join(settings.MEDIA_ROOT, 'tts_generated', f'output_{request.user.id}.wav')
        # Load TTS model only when needed
        tts_model = ChatterboxTTS.from_pretrained(device="cpu")
        wav = tts_model.generate(bot_reply)
        ta.save(output_path, wav, tts_model.sr)
        audio_url = f"/tts/audio/output_{request.user.id}.wav"
        return JsonResponse({'reply': bot_reply, 'audio_url': audio_url, 'transcription': transcription})
    else:
        return render(request, 'llm/audio_chat.html')
