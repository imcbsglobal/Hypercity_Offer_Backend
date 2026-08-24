from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP


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
    list_display = ['phone', 'otp', 'created_at', 'is_verified']
    list_filter = ['is_verified']
