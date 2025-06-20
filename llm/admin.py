from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from .models import *
# Register your models here.

class FAQEntryInline(TabularInline):
    model = FAQEntry
    extra = 0
    readonly_fields = ("question", "answer", "created_at")
    can_delete = False
    show_change_link = True

class AboutUsInfoInline(StackedInline):
    model = AboutUsInfo
    extra = 0
    readonly_fields = ("company_history", "mission", "vision", "core_values", "team_info", "achievements", "unique_selling_points", "created_at")
    can_delete = False
    show_change_link = True

class ServiceInfoInline(TabularInline):
    model = ServiceInfo
    extra = 0
    readonly_fields = ("service_name", "description", "target_audience", "benefits", "specialization", "created_at")
    can_delete = False
    show_change_link = True

class PricingInfoInline(TabularInline):
    model = PricingInfo
    extra = 0
    readonly_fields = ("service_or_package", "price", "payment_terms", "discounts", "additional_fees", "notes", "created_at")
    can_delete = False
    show_change_link = True

class PolicyInfoInline(TabularInline):
    model = PolicyInfo
    extra = 0
    readonly_fields = ("policy_type", "content", "created_at")
    can_delete = False
    show_change_link = True

class TrainingMaterialInline(TabularInline):
    model = TrainingMaterial
    extra = 0
    readonly_fields = ("title", "content", "created_at")
    can_delete = False
    show_change_link = True

class CallScriptInline(TabularInline):
    model = CallScript
    extra = 0
    readonly_fields = ("script_type", "content", "created_at")
    can_delete = False
    show_change_link = True

class BusinessAdmin(ModelAdmin):
    list_display = ( 'user', 'business_type', 'services_offered', 'hours_of_operation', 'booking_conditions', 'contact_preferences', 'created_at')
    search_fields = ("user__username", "business_type", "services_offered")
    list_filter = ("business_type", "created_at")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("documents",)

class BusinessDocumentAdmin(ModelAdmin):
    list_display = ('user', 'document_type', 'is_processed', 'created_at')
    list_filter = ('document_type', 'is_processed', 'created_at')
    search_fields = ('user__username', 'document_type')
    readonly_fields = ('created_at', 'updated_at', 'extracted_content')
    inlines = [FAQEntryInline, AboutUsInfoInline, ServiceInfoInline, PricingInfoInline, PolicyInfoInline, TrainingMaterialInline, CallScriptInline]

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        type_to_inline = {
            'faq': [FAQEntryInline],
            'about': [AboutUsInfoInline],
            'services': [ServiceInfoInline],
            'pricing': [PricingInfoInline],
            'policies': [PolicyInfoInline],
            'training': [TrainingMaterialInline],
            'scripts': [CallScriptInline],
        }
        inlines = type_to_inline.get(obj.document_type, [])
        return [inline(self.model, self.admin_site) for inline in inlines]

class FAQEntryAdmin(ModelAdmin):
    list_display = ("document", "question", "created_at")
    search_fields = ("question", "answer", "document__user__username")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

class AboutUsInfoAdmin(ModelAdmin):
    list_display = ("document", "company_history", "mission", "vision", "created_at")
    search_fields = ("company_history", "mission", "vision", "document__user__username")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

class ServiceInfoAdmin(ModelAdmin):
    list_display = ("document", "service_name", "specialization", "created_at")
    search_fields = ("service_name", "description", "document__user__username")
    list_filter = ("specialization", "created_at")
    readonly_fields = ("created_at",)

class PricingInfoAdmin(ModelAdmin):
    list_display = ("document", "service_or_package", "price", "created_at")
    search_fields = ("service_or_package", "price", "document__user__username")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

class PolicyInfoAdmin(ModelAdmin):
    list_display = ("document", "policy_type", "created_at")
    search_fields = ("policy_type", "content", "document__user__username")
    list_filter = ("policy_type", "created_at")
    readonly_fields = ("created_at",)

class TrainingMaterialAdmin(ModelAdmin):
    list_display = ("document", "title", "created_at")
    search_fields = ("title", "content", "document__user__username")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

class CallScriptAdmin(ModelAdmin):
    list_display = ("document", "script_type", "created_at")
    search_fields = ("script_type", "content", "document__user__username")
    list_filter = ("script_type", "created_at")
    readonly_fields = ("created_at",)

admin.site.register(BusinessInfo, BusinessAdmin)
admin.site.register(BusinessDocument, BusinessDocumentAdmin)
admin.site.register(FAQEntry, FAQEntryAdmin)
admin.site.register(AboutUsInfo, AboutUsInfoAdmin)
admin.site.register(ServiceInfo, ServiceInfoAdmin)
admin.site.register(PricingInfo, PricingInfoAdmin)
admin.site.register(PolicyInfo, PolicyInfoAdmin)
admin.site.register(TrainingMaterial, TrainingMaterialAdmin)
admin.site.register(CallScript, CallScriptAdmin)
