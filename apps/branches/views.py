from rest_framework import viewsets, permissions
from .models import Branch
from .serializers import BranchListSerializer, BranchDetailSerializer
from apps.accounts.permissions import IsSuperAdminOrBranchManager
from apps.activity_logs.utils import log_activity


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    search_fields = ['name', 'address']

    def get_serializer_class(self):
        if self.action == 'list':
            return BranchListSerializer
        return BranchDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Branch.objects.all()
        if user.is_authenticated and user.role == 'BRANCH_MGR' and user.managed_branch:
            qs = qs.filter(id=user.managed_branch.id)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsSuperAdminOrBranchManager()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'CREATE', 'branch', instance.id, instance.name)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'UPDATE', 'branch', instance.id, instance.name)

    def perform_destroy(self, instance):
        log_activity(self.request.user, 'DELETE', 'branch', instance.id, instance.name)
        instance.delete()
