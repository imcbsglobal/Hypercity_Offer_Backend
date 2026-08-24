from rest_framework import serializers
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user_id', 'user_name', 'action', 'action_display',
            'entity_type', 'entity_id', 'entity_name', 'details', 'created_at',
        ]
