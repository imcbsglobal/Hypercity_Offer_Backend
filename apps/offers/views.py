from django.utils import timezone
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Offer
from .serializers import OfferListSerializer, OfferDetailSerializer, OfferCreateSerializer
from apps.accounts.permissions import IsSuperAdminOrMarketing, IsSuperAdminOrBranchManager
from apps.activity_logs.utils import log_activity


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'branches']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'view_count', 'start_date', 'end_date']

    def _auto_update_statuses(self):
        now = timezone.now()
        Offer.objects.filter(is_active=False, start_date__lte=now, end_date__gte=now).update(is_active=True)
        Offer.objects.filter(is_active=True, end_date__lt=now).update(is_active=False)

    def get_serializer_class(self):
        if self.action == 'list':
            return OfferListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return OfferCreateSerializer
        return OfferDetailSerializer

    def get_queryset(self):
        self._auto_update_statuses()
        qs = Offer.objects.all()
        user = self.request.user

        if user.is_authenticated and user.role == 'BRANCH_MGR' and user.managed_branch:
            qs = qs.filter(branches=user.managed_branch)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        branch = self.request.query_params.get('branch')
        if branch:
            qs = qs.filter(branches__id=branch)

        expiring = self.request.query_params.get('expiring_soon')
        if expiring:
            now = timezone.now()
            three_days = now + timezone.timedelta(days=3)
            qs = qs.filter(end_date__gte=now, end_date__lte=three_days)

        return qs.prefetch_related('offerbranch_set__branch')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSuperAdminOrMarketing()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        log_activity(self.request.user, 'CREATE', 'offer', instance.id, instance.title)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'UPDATE', 'offer', instance.id, instance.title)

    def perform_destroy(self, instance):
        log_activity(self.request.user, 'DELETE', 'offer', instance.id, instance.title)
        instance.delete()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def admin_all(self, request):
        """List all offers including inactive/expired (admin only)"""
        self._auto_update_statuses()
        qs = Offer.objects.all()
        if request.user.role == 'BRANCH_MGR' and request.user.managed_branch:
            qs = qs.filter(branches=request.user.managed_branch)
        qs = qs.prefetch_related('offerbranch_set__branch')
        serializer = OfferListSerializer(qs, many=True)
        return Response(serializer.data)
