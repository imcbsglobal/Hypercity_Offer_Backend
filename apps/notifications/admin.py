from django.contrib import admin
from .models import Notification, UserNotification

class UserNotificationInline(admin.TabularInline):
    model = UserNotification
    extra = 0
    readonly_fields = ['user', 'is_read', 'read_at']
    can_delete = False

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'is_active', 'sent_at']
    list_filter = ['type', 'is_active', 'target_branches']
    search_fields = ['title', 'body']
    filter_horizontal = ['target_branches']

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification', 'is_read', 'read_at']
    list_filter = ['is_read']
