from rest_framework import serializers

from .models import AccMaster, Misel, AccInvMast


class AccMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccMaster
        fields = '__all__'


class MiselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Misel
        fields = '__all__'


class AccInvMastSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccInvMast
        fields = '__all__'