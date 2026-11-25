from decimal import Decimal, InvalidOperation

from django.db import DatabaseError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccMaster
from .my_invoices import _last_ten_digits


class CustomerPointsSerializer(serializers.Serializer):
    customerid = serializers.CharField()
    customer_name = serializers.CharField(allow_null=True)
    client_id = serializers.CharField()
    points_raw = serializers.CharField(allow_blank=True, allow_null=True)
    points = serializers.DecimalField(
        max_digits=20, decimal_places=3, allow_null=True, coerce_to_string=False
    )
    synced_at = serializers.DateTimeField()


def _parse_points(raw):
    if not raw:
        return None
    cleaned = str(raw).strip().replace(',', '')
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


class MyPointsView(APIView):
    def get(self, request):
        phone = _last_ten_digits(getattr(request.user, 'phone', ''))
        if not phone:
            return Response(
                {'detail': 'No customer account found with this number. Please contact admin.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            masters = list(
                AccMaster.objects.exclude(phone2__isnull=True).exclude(phone2='')
                .values_list('code', 'name', 'phone2', 'exregnodate', 'client_id', 'synced_at')
            )
        except DatabaseError:
            return Response(
                {'detail': 'Account sync data unavailable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        matched = [
            master for master in masters
            if _last_ten_digits(master[2]) and _last_ten_digits(master[2]) == phone
        ]
        if not matched:
            return Response(
                {'detail': 'No customer account found with this number. Please contact admin.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        accounts = [
            {
                'customerid': code,
                'customer_name': name or None,
                'client_id': client_id,
                'points_raw': exregnodate,
                'points': _parse_points(exregnodate),
                'synced_at': synced_at,
            }
            for code, name, phone2, exregnodate, client_id, synced_at in matched
        ]
        serializer = CustomerPointsSerializer(accounts, many=True)

        return Response({
            'customerid': accounts[0]['customerid'],
            'customer_name': accounts[0]['customer_name'],
            'accounts': serializer.data,
        })
