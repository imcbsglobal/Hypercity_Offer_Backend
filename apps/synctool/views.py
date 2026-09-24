from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import AccMaster, Misel, AccInvMast
from .serializers import AccMasterSerializer, MiselSerializer, AccInvMastSerializer


class AccMasterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccMaster.objects.all()
    serializer_class = AccMasterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client_id']
    search_fields = ['code', 'name', 'place']
    ordering_fields = ['code', 'name', 'synced_at']


class MiselViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Misel.objects.all()
    serializer_class = MiselSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client_id']
    search_fields = ['firm_name', 'address1']
    ordering_fields = ['firm_name', 'synced_at']


class AccInvMastViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AccInvMast.objects.all()
    serializer_class = AccInvMastSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client_id', 'customerid']
    search_fields = ['customerid']
    ordering_fields = ['invdate', 'slno', 'synced_at']