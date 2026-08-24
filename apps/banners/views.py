from django.utils import timezone
from rest_framework import viewsets, permissions
from .models import Banner
from .serializers import BannerListSerializer, BannerDetailSerializer, BannerCreateSerializer
from apps.accounts.permissions import IsSuperAdminOrMarketing
from apps.activity_logs.utils import log_activity


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return BannerListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return BannerCreateSerializer
        return BannerDetailSerializer

    def get_queryset(self):
        qs = Banner.objects.all()

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSuperAdminOrMarketing()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'CREATE', 'banner', instance.id, instance.title)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'UPDATE', 'banner', instance.id, instance.title)

    def perform_destroy(self, instance):
        log_activity(self.request.user, 'DELETE', 'banner', instance.id, instance.title)
        instance.delete()
