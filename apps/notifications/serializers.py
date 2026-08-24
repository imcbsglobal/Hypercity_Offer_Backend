from rest_framework import serializers
from .models import Notification, UserNotification


class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'image', 'type', 'linked_offer', 'is_active', 'sent_at']


class NotificationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class UserNotificationSerializer(serializers.ModelSerializer):
    notification_detail = NotificationListSerializer(source='notification', read_only=True)

    class Meta:
        model = UserNotification
        fields = ['id', 'notification', 'notification_detail', 'is_read', 'read_at']


class MarkReadSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField()
