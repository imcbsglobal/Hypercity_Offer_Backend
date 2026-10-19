import django.core.validators

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('custom_forms', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='customform',
            name='background_color',
            field=models.CharField(
                default='#FFFFFF',
                max_length=7,
                validators=[django.core.validators.RegexValidator(
                    message='Accent color must be a six-digit hex color such as #1A7A48.',
                    regex='^#[0-9A-Fa-f]{6}$',
                )],
            ),
        ),
    ]
