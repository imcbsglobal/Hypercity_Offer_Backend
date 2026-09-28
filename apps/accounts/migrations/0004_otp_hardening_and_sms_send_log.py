from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSSendLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(db_index=True, max_length=15)),
                ('body', models.TextField()),
                ('success', models.BooleanField(default=False)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('provider_message', models.TextField(blank=True)),
                ('submission_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['-created_at'], name='accounts_sm_created_168acf_idx')],
            },
        ),
        migrations.AlterField(
            model_name='otp',
            name='otp',
            field=models.CharField(max_length=128),
        ),
        migrations.AddField(
            model_name='otp',
            name='expires_at',
            field=models.DateTimeField(default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='otp',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='otp',
            name='is_used',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='otp',
            name='sms_submission_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='otp',
            name='phone',
            field=models.CharField(db_index=True, max_length=15),
        ),
        migrations.AlterModelOptions(
            name='otp',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='otp',
            index=models.Index(fields=['phone', '-created_at'], name='accounts_ot_phone_9473c1_idx'),
        ),
        migrations.RemoveField(
            model_name='otp',
            name='is_verified',
        ),
    ]
