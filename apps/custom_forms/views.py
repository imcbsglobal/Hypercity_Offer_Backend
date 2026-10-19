import csv
import json
from io import StringIO

from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomForm, CustomFormResponse
from .permissions import IsStaffUser
from .serializers import (
    CustomFormResponseSerializer,
    CustomFormSerializer,
    PublicFormSerializer,
    PublicResponseSerializer,
)


class CustomFormViewSet(viewsets.ModelViewSet):
    serializer_class = CustomFormSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffUser]

    def get_queryset(self):
        return CustomForm.objects.annotate(response_count=Count('responses')).prefetch_related('fields')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if self.get_object().status != CustomForm.Status.DRAFT:
            raise ValidationError('Published forms are locked. Close or reopen only changes their availability.')
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        form = self.get_object()
        if form.status != CustomForm.Status.DRAFT:
            raise ValidationError('Only draft forms can be published.')
        if not form.fields.exists():
            raise ValidationError('Add at least one field before publishing.')
        form.status = CustomForm.Status.PUBLISHED
        form.published_at = timezone.now()
        form.save(update_fields=['status', 'published_at', 'updated_at'])
        return Response(self.get_serializer(form).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        form = self.get_object()
        if form.status != CustomForm.Status.PUBLISHED:
            raise ValidationError('Only published forms can be closed.')
        form.status = CustomForm.Status.CLOSED
        form.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(form).data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        form = self.get_object()
        if form.status != CustomForm.Status.CLOSED:
            raise ValidationError('Only closed forms can be reopened.')
        form.status = CustomForm.Status.PUBLISHED
        form.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(form).data)

    def _response_queryset(self, form):
        queryset = form.responses.all()
        submitted_after = self.request.query_params.get('submitted_after')
        submitted_before = self.request.query_params.get('submitted_before')
        if submitted_after:
            parsed = parse_date(submitted_after)
            if not parsed:
                raise ValidationError({'submitted_after': 'Use YYYY-MM-DD.'})
            queryset = queryset.filter(submitted_at__date__gte=parsed)
        if submitted_before:
            parsed = parse_date(submitted_before)
            if not parsed:
                raise ValidationError({'submitted_before': 'Use YYYY-MM-DD.'})
            queryset = queryset.filter(submitted_at__date__lte=parsed)
        return queryset

    @action(detail=True, methods=['get'])
    def responses(self, request, pk=None):
        form = self.get_object()
        queryset = self._response_queryset(form)
        page = self.paginate_queryset(queryset)
        serializer = CustomFormResponseSerializer(page if page is not None else queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=True, methods=['get'], url_path=r'responses/(?P<response_id>[^/.]+)')
    def response_detail(self, request, pk=None, response_id=None):
        response = get_object_or_404(self.get_object().responses, id=response_id)
        return Response(CustomFormResponseSerializer(response).data)

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        form = self.get_object()
        fields = list(form.fields.all())
        stream = StringIO()
        writer = csv.writer(stream)
        writer.writerow(['Submitted at', *[field.label for field in fields]])
        for response in self._response_queryset(form):
            row = [response.submitted_at.isoformat()]
            for field in fields:
                value = response.answers.get(str(field.field_key), '')
                row.append(', '.join(value) if isinstance(value, list) else value)
            writer.writerow(row)
        http_response = HttpResponse(stream.getvalue(), content_type='text/csv')
        http_response['Content-Disposition'] = f'attachment; filename="form-{form.id}-responses.csv"'
        return http_response


class PublicFormView(APIView):
    permission_classes = [permissions.AllowAny]

    def _get_form(self, public_id):
        return get_object_or_404(
            CustomForm.objects.prefetch_related('fields'),
            public_id=public_id,
            status=CustomForm.Status.PUBLISHED,
        )

    def get(self, request, public_id):
        return Response(PublicFormSerializer(self._get_form(public_id)).data)


class PublicFormResponseView(PublicFormView):
    def post(self, request, public_id):
        form = self._get_form(public_id)
        serializer = PublicResponseSerializer(data=request.data, context={'form': form})
        serializer.is_valid(raise_exception=True)
        schema_snapshot = [
            {
                'field_key': str(field.field_key),
                'label': field.label,
                'field_type': field.field_type,
                'choices': field.choices,
            }
            for field in form.fields.all()
        ]
        with transaction.atomic():
            CustomFormResponse.objects.create(
                form=form,
                answers=serializer.validated_data['answers'],
                schema_snapshot=schema_snapshot,
            )
        return Response({'message': form.confirmation_message}, status=status.HTTP_201_CREATED)
