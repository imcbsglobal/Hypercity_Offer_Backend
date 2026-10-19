from decimal import Decimal, InvalidOperation
import json

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.core.validators import EmailValidator
from django.utils.dateparse import parse_date
from rest_framework import serializers

from .models import CustomForm, CustomFormField, CustomFormResponse


CHOICE_TYPES = {
    CustomFormField.Type.SINGLE_CHOICE,
    CustomFormField.Type.MULTIPLE_CHOICE,
    CustomFormField.Type.DROPDOWN,
}


class CustomFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFormField
        fields = ['field_key', 'position', 'field_type', 'label', 'help_text', 'placeholder', 'required', 'choices', 'validation']
        extra_kwargs = {'field_key': {'required': False}}

    def validate(self, attrs):
        field_type = attrs.get('field_type', getattr(self.instance, 'field_type', None))
        choices = attrs.get('choices', getattr(self.instance, 'choices', []))
        validation = attrs.get('validation', getattr(self.instance, 'validation', {}))

        if field_type in CHOICE_TYPES:
            minimum_choices = 1 if field_type == CustomFormField.Type.SINGLE_CHOICE else 2
            if not isinstance(choices, list) or len(choices) < minimum_choices:
                raise serializers.ValidationError({
                    'choices': f'{field_type.replace("_", " ").title()} fields require at least {minimum_choices} option{ "s" if minimum_choices > 1 else "" }.'
                })
            cleaned = [str(choice).strip() for choice in choices]
            if any(not choice for choice in cleaned) or len(set(cleaned)) != len(cleaned):
                raise serializers.ValidationError({'choices': 'Options must be unique and non-empty.'})
            attrs['choices'] = cleaned
        elif choices:
            attrs['choices'] = []

        if field_type == CustomFormField.Type.RATING:
            if not isinstance(validation, dict):
                raise serializers.ValidationError({'validation': 'Rating validation must be an object.'})
            minimum = validation.get('min', 1)
            maximum = validation.get('max', 5)
            if not isinstance(minimum, int) or not isinstance(maximum, int) or minimum < 1 or maximum > 10 or minimum >= maximum:
                raise serializers.ValidationError({'validation': 'Rating min and max must be whole numbers between 1 and 10.'})
            attrs['validation'] = {**validation, 'min': minimum, 'max': maximum}
        elif validation and not isinstance(validation, dict):
            raise serializers.ValidationError({'validation': 'Validation must be an object.'})
        return attrs


class CustomFormSerializer(serializers.ModelSerializer):
    fields = CustomFormFieldSerializer(many=True, required=False)
    share_url = serializers.ReadOnlyField()
    response_count = serializers.IntegerField(read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomForm
        fields = [
            'id', 'public_id', 'title', 'description', 'logo', 'logo_url', 'accent_color', 'background_color',
            'confirmation_message', 'status', 'share_url', 'response_count', 'created_by',
            'created_at', 'updated_at', 'published_at', 'fields',
        ]
        read_only_fields = ['public_id', 'status', 'share_url', 'response_count', 'created_by', 'created_at', 'updated_at', 'published_at']

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else ''

    def to_internal_value(self, data):
        raw_fields = data.get('fields') if hasattr(data, 'get') else None
        if isinstance(raw_fields, str):
            try:
                # A multipart request is a QueryDict. DRF treats nested values
                # in a QueryDict as HTML form lists, so normalize it to a plain
                # dict before handing the JSON field schema to the nested serializer.
                data = {key: data.get(key) for key in data.keys()}
                data['fields'] = json.loads(raw_fields)
            except json.JSONDecodeError:
                raise serializers.ValidationError({'fields': 'Fields must be valid JSON.'})
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        form = CustomForm.objects.create(**validated_data)
        self._replace_fields(form, fields_data)
        return form

    @transaction.atomic
    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if fields_data is not None:
            self._replace_fields(instance, fields_data)
        return instance

    @staticmethod
    def _replace_fields(form, fields_data):
        # Recreate draft fields so a drag-and-drop reorder never violates the
        # unique form/position constraint during an intermediate save.
        form.fields.all().delete()
        for field_data in fields_data:
            field_key = field_data.pop('field_key', None)
            if field_key:
                CustomFormField.objects.create(form=form, field_key=field_key, **field_data)
            else:
                CustomFormField.objects.create(form=form, **field_data)


class PublicFormSerializer(serializers.ModelSerializer):
    fields = CustomFormFieldSerializer(many=True, read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomForm
        fields = ['public_id', 'title', 'description', 'logo_url', 'accent_color', 'background_color', 'confirmation_message', 'fields']

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else ''


class PublicResponseSerializer(serializers.Serializer):
    answers = serializers.DictField()

    def validate_answers(self, answers):
        form = self.context['form']
        fields = list(form.fields.all())
        expected_keys = {str(field.field_key) for field in fields}
        submitted_keys = set(answers.keys())
        unknown_keys = submitted_keys - expected_keys
        if unknown_keys:
            raise serializers.ValidationError({key: 'Unknown form field.' for key in unknown_keys})

        errors = {}
        cleaned = {}
        for field in fields:
            key = str(field.field_key)
            value = answers.get(key)
            empty = value is None or value == '' or value == []
            if empty:
                if field.required:
                    errors[key] = 'This field is required.'
                continue
            try:
                cleaned[key] = self._validate_value(field, value)
            except (serializers.ValidationError, DjangoValidationError) as exc:
                errors[key] = getattr(exc, 'detail', exc.messages)

        if errors:
            raise serializers.ValidationError(errors)
        return cleaned

    @staticmethod
    def _validate_value(field, value):
        if field.field_type in {CustomFormField.Type.SHORT_TEXT, CustomFormField.Type.LONG_TEXT}:
            if not isinstance(value, str):
                raise serializers.ValidationError('Enter text.')
            return value.strip()
        if field.field_type == CustomFormField.Type.EMAIL:
            if not isinstance(value, str):
                raise serializers.ValidationError('Enter a valid email address.')
            EmailValidator()(value.strip())
            return value.strip()
        if field.field_type == CustomFormField.Type.PHONE:
            if not isinstance(value, str) or not value.strip():
                raise serializers.ValidationError('Enter a valid phone number.')
            digits = ''.join(char for char in value if char.isdigit())
            if len(digits) < 7 or len(digits) > 15:
                raise serializers.ValidationError('Enter a valid phone number.')
            return value.strip()
        if field.field_type == CustomFormField.Type.NUMBER:
            try:
                number = Decimal(str(value))
            except (InvalidOperation, ValueError):
                raise serializers.ValidationError('Enter a valid number.')
            minimum = field.validation.get('min')
            maximum = field.validation.get('max')
            if minimum is not None and number < Decimal(str(minimum)):
                raise serializers.ValidationError(f'Value must be at least {minimum}.')
            if maximum is not None and number > Decimal(str(maximum)):
                raise serializers.ValidationError(f'Value must be at most {maximum}.')
            return str(number)
        if field.field_type == CustomFormField.Type.DATE:
            if not isinstance(value, str) or not parse_date(value):
                raise serializers.ValidationError('Enter a valid date.')
            return value
        if field.field_type in {CustomFormField.Type.SINGLE_CHOICE, CustomFormField.Type.DROPDOWN}:
            if value not in field.choices:
                raise serializers.ValidationError('Choose a valid option.')
            return value
        if field.field_type == CustomFormField.Type.MULTIPLE_CHOICE:
            if not isinstance(value, list) or not value:
                raise serializers.ValidationError('Choose at least one option.')
            if any(choice not in field.choices for choice in value):
                raise serializers.ValidationError('Choose only valid options.')
            return value
        if field.field_type == CustomFormField.Type.RATING:
            try:
                rating = int(value)
            except (TypeError, ValueError):
                raise serializers.ValidationError('Choose a valid rating.')
            minimum = field.validation.get('min', 1)
            maximum = field.validation.get('max', 5)
            if rating < minimum or rating > maximum:
                raise serializers.ValidationError(f'Rating must be between {minimum} and {maximum}.')
            return rating
        raise serializers.ValidationError('Unsupported field type.')


class CustomFormResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFormResponse
        fields = ['id', 'submitted_at', 'answers', 'schema_snapshot']
