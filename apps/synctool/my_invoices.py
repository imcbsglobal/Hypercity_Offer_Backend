import re

from django.db import DatabaseError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccInvMast, AccMaster


def _last_ten_digits(value):
    digits = re.sub(r'\D', '', value or '')
    return digits[-10:] if len(digits) >= 10 else ''


class MyInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccInvMast
        fields = ['id', 'slno', 'invdate', 'customerid', 'nettotal', 'client_id', 'synced_at']


class MyInvoicesView(APIView):
    def get(self, request):
        try:
            limit_raw = request.query_params.get('limit', '20')
            offset_raw = request.query_params.get('offset', '0')
            limit = int(limit_raw)
            offset = int(offset_raw)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'limit and offset must be integers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if limit < 1:
            limit = 1
        elif limit > 100:
            limit = 100
        if offset < 0:
            offset = 0

        phone = _last_ten_digits(getattr(request.user, 'phone', ''))

        try:
            masters = list(
                AccMaster.objects.exclude(phone2__isnull=True).exclude(phone2='')
                .values_list('code', 'name', 'phone2')
            )
        except DatabaseError:
            return Response(
                {'detail': 'Invoice sync data unavailable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        matched = [m for m in masters if _last_ten_digits(m[2]) and _last_ten_digits(m[2]) == phone]

        if not matched:
            return Response(
                {'detail': 'No customer account found with this number. Please contact admin.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        codes = [m[0] for m in matched]
        customer_name = matched[0][1] or None

        try:
            queryset = (
                AccInvMast.objects.filter(customerid__in=codes)
                .order_by('-invdate', '-slno')
            )
            total = queryset.count()
            results = queryset[offset:offset + limit]
            serializer = MyInvoiceSerializer(results, many=True)
        except DatabaseError:
            return Response(
                {'detail': 'Invoice sync data unavailable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'customerid': codes[0],
            'customer_name': customer_name,
            'results': serializer.data,
        })
