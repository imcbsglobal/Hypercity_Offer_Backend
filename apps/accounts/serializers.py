from rest_framework import serializers
from .models import User, OTP
from apps.branches.models import Branch


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


class SignupSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)
    name = serializers.CharField(max_length=100)

    def validate_phone(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()


class UserProfileSerializer(serializers.ModelSerializer):
    preferred_branches = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Branch.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'email', 'fcm_token',
                  'preferred_branches', 'role', 'is_customer']
        read_only_fields = ['id', 'phone', 'role', 'is_customer']


class UpdateFCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=500)

    def validate_fcm_token(self, value):
        if not value.strip():
            raise serializers.ValidationError("FCM token cannot be empty")
        return value.strip()


class AdminLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'role', 'is_customer', 'is_active', 'date_joined']


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'password', 'role', 'managed_branch', 'is_active']
        read_only_fields = ['id']

    def validate_role(self, value):
        if value == 'SUPER_ADMIN':
            raise serializers.ValidationError("Cannot create Super Admin via API. Use createsuperuser command.")
        if value not in ['BRANCH_MGR', 'MARKETING']:
            raise serializers.ValidationError("Role must be BRANCH_MGR or MARKETING.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        user.is_staff = True
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StaffListSerializer(serializers.ModelSerializer):
    managed_branch_name = serializers.CharField(source='managed_branch.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'role', 'managed_branch', 'managed_branch_name',
                  'is_active', 'is_staff', 'date_joined', 'last_login']
