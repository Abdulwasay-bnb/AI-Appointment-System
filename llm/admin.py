from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import *
# Register your models here.
class BusinessAdmin(ModelAdmin):
    list_display = ( 'business_type', 'services_offered', 'hours_of_operation', 'booking_conditions', 'contact_preferences')

class BusinessDocumentAdmin(ModelAdmin):
    list_display = ('user', 'document_type', 'is_processed', 'created_at')
    list_filter = ('document_type', 'is_processed', 'created_at')
    search_fields = ('user__username', 'document_type')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(BusinessInfo, BusinessAdmin)
admin.site.register(BusinessDocument, BusinessDocumentAdmin)