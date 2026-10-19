import django.core.validators
import django.db.models.deletion
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='CustomForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='custom_forms/logos/')),
                ('accent_color', models.CharField(default='#1A7A48', max_length=7, validators=[django.core.validators.RegexValidator(message='Accent color must be a six-digit hex color such as #1A7A48.', regex='^#[0-9A-Fa-f]{6}$')])),
                ('confirmation_message', models.TextField(default='Thanks for your response!')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('CLOSED', 'Closed')], default='DRAFT', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='custom_forms', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CustomFormField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_key', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('position', models.PositiveIntegerField()),
                ('field_type', models.CharField(choices=[('SHORT_TEXT', 'Short text'), ('LONG_TEXT', 'Long text'), ('EMAIL', 'Email'), ('PHONE', 'Phone'), ('NUMBER', 'Number'), ('DATE', 'Date'), ('SINGLE_CHOICE', 'Single choice'), ('MULTIPLE_CHOICE', 'Multiple choice'), ('DROPDOWN', 'Dropdown'), ('RATING', 'Rating')], max_length=20)),
                ('label', models.CharField(max_length=300)),
                ('help_text', models.TextField(blank=True)),
                ('placeholder', models.CharField(blank=True, max_length=300)),
                ('required', models.BooleanField(default=False)),
                ('choices', models.JSONField(blank=True, default=list)),
                ('validation', models.JSONField(blank=True, default=dict)),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='custom_forms.customform')),
            ],
            options={'ordering': ['position', 'id']},
        ),
        migrations.CreateModel(
            name='CustomFormResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answers', models.JSONField(default=dict)),
                ('schema_snapshot', models.JSONField(default=list)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='custom_forms.customform')),
            ],
            options={'ordering': ['-submitted_at']},
        ),
        migrations.AddConstraint(
            model_name='customformfield',
            constraint=models.UniqueConstraint(fields=('form', 'position'), name='custom_form_unique_position'),
        ),
        migrations.AddIndex(
            model_name='customformresponse',
            index=models.Index(fields=['form', '-submitted_at'], name='custom_form_form_id_8d7e57_idx'),
        ),
    ]
