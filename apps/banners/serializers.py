from rest_framework import serializers
from .models import Banner


class BannerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image', 'link_url', 'linked_offer', 'order', 'is_active']


class BannerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'


class BannerCreateSerializer(serializers.ModelSerializer):
    branches = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Banner
        fields = ['title', 'image', 'link_url', 'linked_offer', 'order',
                  'start_date', 'end_date', 'is_active', 'branches']

    def create(self, validated_data):
        branch_ids = validated_data.pop('branches', [])
        banner = Banner.objects.create(**validated_data)
        banner.branches.set(branch_ids)
        return banner

    def update(self, instance, validated_data):
        branch_ids = validated_data.pop('branches', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if branch_ids is not None:
            instance.branches.set(branch_ids)
        return instance
