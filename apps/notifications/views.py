from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Notification, UserNotification
from .serializers import (
    NotificationListSerializer, NotificationDetailSerializer,
    UserNotificationSerializer, MarkReadSerializer
)
from .tasks import send_notification_push
from apps.accounts.permissions import IsSuperAdminOrMarketing


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSuperAdminOrMarketing()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        notification = serializer.save(created_by=self.request.user)
        send_notification_push.delay(notification.id)

    @action(detail=False, methods=['get'])
    def my(self, request):
        notifications = UserNotification.objects.filter(user=request.user)
        serializer = UserNotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_notif, created = UserNotification.objects.get_or_create(
            user=request.user,
            notification_id=serializer.validated_data['notification_id'],
            defaults={'is_read': True, 'read_at': timezone.now()}
        )
        if not user_notif.is_read:
            user_notif.is_read = True
            user_notif.read_at = timezone.now()
            user_notif.save()

        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = UserNotification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
