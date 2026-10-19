import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


accent_color_validator = RegexValidator(
    regex=r'^#[0-9A-Fa-f]{6}$',
    message='Accent color must be a six-digit hex color such as #1A7A48.',
)


class CustomForm(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        CLOSED = 'CLOSED', 'Closed'

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='custom_forms/logos/', null=True, blank=True)
    accent_color = models.CharField(max_length=7, default='#1A7A48', validators=[accent_color_validator])
    background_color = models.CharField(max_length=7, default='#FFFFFF', validators=[accent_color_validator])
    confirmation_message = models.TextField(default='Thanks for your response!')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='custom_forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def share_path(self):
        return f'/forms/{self.public_id}'

    @property
    def share_url(self):
        base_url = getattr(settings, 'PUBLIC_FRONTEND_URL', '').rstrip('/')
        return f'{base_url}{self.share_path}' if base_url else self.share_path

    def __str__(self):
        return self.title


class CustomFormField(models.Model):
    class Type(models.TextChoices):
        SHORT_TEXT = 'SHORT_TEXT', 'Short text'
        LONG_TEXT = 'LONG_TEXT', 'Long text'
        EMAIL = 'EMAIL', 'Email'
        PHONE = 'PHONE', 'Phone'
        NUMBER = 'NUMBER', 'Number'
        DATE = 'DATE', 'Date'
        SINGLE_CHOICE = 'SINGLE_CHOICE', 'Single choice'
        MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', 'Multiple choice'
        DROPDOWN = 'DROPDOWN', 'Dropdown'
        RATING = 'RATING', 'Rating'

    form = models.ForeignKey(CustomForm, on_delete=models.CASCADE, related_name='fields')
    field_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    position = models.PositiveIntegerField()
    field_type = models.CharField(max_length=20, choices=Type.choices)
    label = models.CharField(max_length=300)
    help_text = models.TextField(blank=True)
    placeholder = models.CharField(max_length=300, blank=True)
    required = models.BooleanField(default=False)
    choices = models.JSONField(default=list, blank=True)
    validation = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['position', 'id']
        constraints = [models.UniqueConstraint(fields=['form', 'position'], name='custom_form_unique_position')]

    def __str__(self):
        return f'{self.form.title}: {self.label}'


class CustomFormResponse(models.Model):
    form = models.ForeignKey(CustomForm, on_delete=models.CASCADE, related_name='responses')
    answers = models.JSONField(default=dict)
    schema_snapshot = models.JSONField(default=list)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        indexes = [models.Index(fields=['form', '-submitted_at'])]

    def __str__(self):
        return f'{self.form.title} response #{self.id}'
