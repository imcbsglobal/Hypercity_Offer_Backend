from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def _create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        return self._create_user(phone, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        BRANCH_MGR = 'BRANCH_MGR', 'Branch Manager'
        MARKETING = 'MARKETING', 'Marketing Manager'
        CUSTOMER = 'CUSTOMER', 'Customer'

    username = None
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    managed_branch = models.ForeignKey(
        'branches.Branch', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='managers'
    )
    fcm_token = models.TextField(blank=True)
    preferred_branches = models.ManyToManyField(
        'branches.Branch', blank=True, related_name='preferred_users'
    )
    is_customer = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class OTP(models.Model):
    phone = models.CharField(max_length=15, db_index=True)
    otp = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    sms_submission_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['phone', '-created_at'])]

    def __str__(self):
        return f"{self.phone} - {'used' if self.is_used else 'pending'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def set_code(self, code):
        self.otp = make_password(code)

    def check_code(self, code):
        return check_password(code, self.otp)


class SMSSendLog(models.Model):
    phone = models.CharField(max_length=15, db_index=True)
    body = models.TextField()
    success = models.BooleanField(default=False)
    status_code = models.IntegerField(null=True, blank=True)
    provider_message = models.TextField(blank=True)
    submission_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self):
        return f"{self.phone} - {'ok' if self.success else 'failed'} - {self.created_at}"
