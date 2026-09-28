from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, SMSSendLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['phone', 'name', 'role', 'managed_branch', 'is_customer', 'is_staff', 'is_active']
    list_filter = ['role', 'is_customer', 'is_staff', 'is_active']
    search_fields = ['phone', 'name', 'email']
    list_editable = ['role', 'is_active']

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('name', 'email')}),
        ('Role & Branch', {'fields': ('role', 'managed_branch', 'is_customer')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'password1', 'password2', 'role', 'managed_branch', 'is_staff', 'is_superuser'),
        }),
    )
    ordering = ['phone']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'BRANCH_MGR':
            return qs.filter(managed_branch=request.user.managed_branch)
        return qs


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone', 'created_at', 'expires_at', 'attempts', 'is_used', 'sms_submission_id']
    list_filter = ['is_used']
    search_fields = ['phone']
    readonly_fields = ['created_at', 'sms_submission_id']
    ordering = ['-created_at']


@admin.register(SMSSendLog)
class SMSSendLogAdmin(admin.ModelAdmin):
    list_display = ['phone', 'success', 'status_code', 'submission_id', 'created_at']
    list_filter = ['success', 'status_code']
    search_fields = ['phone', 'submission_id']
    readonly_fields = ['phone', 'body', 'success', 'status_code', 'provider_message', 'submission_id', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
