from django.db import models

# Create your models here.

# --- Main Business Info ---
class BusinessInfo(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='business_infos')
    business_type = models.CharField(max_length=255, blank=True, null=True)
    services_offered = models.TextField(blank=True, null=True)
    hours_of_operation = models.CharField(max_length=255, blank=True, null=True)
    booking_conditions = models.TextField(blank=True, null=True)
    contact_preferences = models.CharField(max_length=255, blank=True, null=True)
    # Link to all business documents for this business
    documents = models.ManyToManyField('BusinessDocument', blank=True, related_name='business_infos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Business Info for {self.user.username} ({self.id})"

# --- Document Uploads ---
class BusinessDocument(models.Model):
    DOCUMENT_TYPES = [
        ('faq', 'FAQ Document'),
        ('about', 'About Us'),
        ('services', 'Services Brochure'),
        ('pricing', 'Pricing Guide'),
        ('policies', 'Company Policies'),
        ('training', 'Training Materials'),
        ('scripts', 'Call Scripts'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='business_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document = models.FileField(upload_to='business_docs/', max_length=500)
    extracted_content = models.TextField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']

# --- Structured Models for Each Document Type ---
class FAQEntry(models.Model):
    """Stores a single FAQ question/answer extracted from a FAQ document."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='faq_entries')
    question = models.CharField(max_length=500)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FAQ: {self.question[:40]}..."

class AboutUsInfo(models.Model):
    """Stores About Us details extracted from About Us documents."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='about_us_info')
    company_history = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    core_values = models.TextField(blank=True)
    team_info = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    unique_selling_points = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"About Us Info for {self.document.user.username} ({self.id})"

class ServiceInfo(models.Model):
    """Stores a single service extracted from a Services Brochure document."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='service_infos')
    service_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_audience = models.CharField(max_length=255, blank=True)
    benefits = models.TextField(blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Service: {self.service_name}"

class PricingInfo(models.Model):
    """Stores pricing details extracted from a Pricing Guide document."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='pricing_infos')
    service_or_package = models.CharField(max_length=255)
    price = models.CharField(max_length=100)
    payment_terms = models.TextField(blank=True)
    discounts = models.TextField(blank=True)
    additional_fees = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pricing: {self.service_or_package} - {self.price}"

class PolicyInfo(models.Model):
    """Stores policy details extracted from a Company Policies document."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='policy_infos')
    policy_type = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Policy: {self.policy_type}"

class TrainingMaterial(models.Model):
    """Stores training material details extracted from Training Materials documents."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='training_materials')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Training: {self.title}"

class CallScript(models.Model):
    """Stores call script details extracted from Call Scripts documents."""
    document = models.ForeignKey(BusinessDocument, on_delete=models.CASCADE, related_name='call_scripts')
    script_type = models.CharField(max_length=100, blank=True)  # e.g., Opening, Objection Handling
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call Script: {self.script_type or 'General'}"
