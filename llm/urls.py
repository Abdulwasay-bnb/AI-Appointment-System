from django.urls import path
from .views import chatbot_view, upload_business_doc, upload_business_doc_legacy, business_upload_view, business_documents_view, audio_chat_view

urlpatterns = [
    path('chatbot/', chatbot_view, name='chatbot'),
    path('upload-business-doc/', upload_business_doc, name='upload_business_doc'),
    path('upload-business-doc-legacy/', upload_business_doc_legacy, name='upload_business_doc_legacy'),
    path('business-upload/', business_upload_view, name='business_upload'),
    path('business-documents/', business_documents_view, name='business_documents'),
    path('audio-chat/', audio_chat_view, name='audio_chat'),
] 