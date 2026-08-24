from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'action', 'entity_type', 'entity_name', 'created_at']
    list_filter = ['action', 'entity_type', 'created_at']
    search_fields = ['user_name', 'entity_name']
    ordering = ['-created_at']
    readonly_fields = ['user_id', 'user_name', 'action', 'entity_type', 'entity_id', 'entity_name', 'details', 'created_at']
