import re

from rest_framework import serializers
from .models import Branch


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'address', 'phone', 'image', 'is_active']


class BranchDetailSerializer(serializers.ModelSerializer):
    def validate_phone(self, value):
        phone = value.strip()
        if not re.fullmatch(r'\d{10}', phone):
            raise serializers.ValidationError('Enter a valid 10-digit phone number.')
        return phone

    class Meta:
        model = Branch
        fields = '__all__'
