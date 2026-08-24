from rest_framework import serializers
from .models import Branch


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'address', 'phone', 'image', 'is_active']


class BranchDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
