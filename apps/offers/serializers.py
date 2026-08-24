from django.utils import timezone
from rest_framework import serializers
from .models import Offer, OfferBranch
from apps.branches.serializers import BranchListSerializer


class OfferBranchSerializer(serializers.ModelSerializer):
    branch_detail = BranchListSerializer(source='branch', read_only=True)

    class Meta:
        model = OfferBranch
        fields = ['id', 'branch', 'branch_detail', 'is_active']


class OfferListSerializer(serializers.ModelSerializer):
    branches = OfferBranchSerializer(source='offerbranch_set', many=True, read_only=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'description', 'image',
                  'start_date', 'end_date', 'is_active', 'view_count', 'branches']


class OfferDetailSerializer(serializers.ModelSerializer):
    branches = OfferBranchSerializer(source='offerbranch_set', many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = Offer
        fields = '__all__'

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        return data


class OfferCreateSerializer(serializers.ModelSerializer):
    branch_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Offer
        fields = ['title', 'description', 'image',
                  'start_date', 'end_date', 'terms_conditions', 'branch_ids', 'is_active']

    def create(self, validated_data):
        branch_ids = validated_data.pop('branch_ids')
        start = validated_data.get('start_date')
        if start and start > timezone.now():
            validated_data['is_active'] = False
        offer = Offer.objects.create(**validated_data)
        for branch_id in branch_ids:
            OfferBranch.objects.create(offer=offer, branch_id=branch_id)
        return offer

    def update(self, instance, validated_data):
        branch_ids = validated_data.pop('branch_ids', None)
        start = validated_data.get('start_date') or instance.start_date
        if start > timezone.now():
            validated_data['is_active'] = False
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if branch_ids is not None:
            instance.offerbranch_set.all().delete()
            for branch_id in branch_ids:
                OfferBranch.objects.create(offer=instance, branch_id=branch_id)

        return instance
