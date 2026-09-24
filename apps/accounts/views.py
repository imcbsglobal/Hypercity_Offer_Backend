import random
import re
from datetime import timedelta

from django.utils import timezone
from rest_framework import status, generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from .models import User, OTP
from django.contrib.auth import authenticate
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer,
    SignupSerializer, UserProfileSerializer,
    AdminLoginSerializer, StaffCreateSerializer, StaffListSerializer,
    UpdateFCMTokenSerializer
)
from .permissions import IsSuperAdmin
from apps.activity_logs.utils import log_activity


def generate_otp():
    return str(random.randint(1000, 9999))


def _normalize_phone(value):
    return re.sub(r'\D', '', value or '')


def is_known_customer(phone):
    digits = _normalize_phone(phone)
    if len(digits) < 10:
        return False
    digits = digits[-10:]
    from apps.synctool.models import AccMaster
    phone2_list = (
        AccMaster.objects.exclude(phone2__isnull=True).exclude(phone2='')
        .values_list('phone2', flat=True)
    )
    return any(_normalize_phone(p) == digits for p in phone2_list)


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SendOTPSerializer

    @extend_schema(request=SendOTPSerializer, responses={200: dict})
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        if not is_known_customer(phone):
            return Response(
                {'error': 'No customer account found with this number. Please contact admin.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        OTP.objects.filter(phone=phone, is_verified=False).delete()

        otp_code = generate_otp()
        OTP.objects.create(phone=phone, otp=otp_code)

        # In production: send via SMS gateway (Twilio, MSG91, etc.)
        print(f"OTP for {phone}: {otp_code}")

        return Response({'message': 'OTP sent successfully', 'otp': otp_code}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    @extend_schema(request=VerifyOTPSerializer, responses={200: dict})
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        otp_code = serializer.validated_data['otp']

        otp_entry = OTP.objects.filter(
            phone=phone, otp=otp_code, is_verified=False
        ).first()

        if not otp_entry:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > otp_entry.created_at + timedelta(minutes=5):
            otp_entry.delete()
            return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)

        otp_entry.is_verified = True
        otp_entry.save()

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            if not is_known_customer(phone):
                return Response({'error': 'Account not found. Please signup first.'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.create_user(
                phone=phone,
                name='Customer',
                role='CUSTOMER',
                is_customer=True,
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'phone': user.phone,
                'name': user.name,
                'is_customer': user.is_customer,
                'role': user.role,
            }
        }, status=status.HTTP_200_OK)


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    @extend_schema(request=SignupSerializer, responses={201: dict})
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        otp_code = serializer.validated_data['otp']
        name = serializer.validated_data['name']

        otp_entry = OTP.objects.filter(
            phone=phone, otp=otp_code, is_verified=False
        ).first()

        if not otp_entry:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > otp_entry.created_at + timedelta(minutes=5):
            otp_entry.delete()
            return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone=phone).exists():
            return Response({'error': 'Account already exists. Please login.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_entry.is_verified = True
        otp_entry.save()

        user = User.objects.create_user(
            phone=phone,
            name=name,
            role='CUSTOMER',
            is_customer=True,
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'phone': user.phone,
                'name': user.name,
                'is_customer': user.is_customer,
                'role': user.role,
            }
        }, status=status.HTTP_201_CREATED)


class AdminLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AdminLoginSerializer

    @extend_schema(request=AdminLoginSerializer, responses={200: dict})
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            phone=serializer.validated_data['phone'],
            password=serializer.validated_data['password']
        )

        if not user or not user.is_staff:
            return Response({'error': 'Invalid credentials or not a staff user'}, status=status.HTTP_401_UNAUTHORIZED)

        log_activity(user, 'LOGIN', 'account', user.id, user.name)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'phone': user.phone,
                'name': user.name,
                'role': user.role,
                'managed_branch': user.managed_branch_id,
                'is_superuser': user.is_superuser,
            }
        }, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UpdateFCMTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdateFCMTokenSerializer

    def post(self, request):
        serializer = UpdateFCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.fcm_token = serializer.validated_data['fcm_token']
        request.user.save(update_fields=['fcm_token'])

        return Response({'message': 'FCM token updated successfully'}, status=status.HTTP_200_OK)


class StaffViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    search_fields = ['phone', 'name']
    ordering_fields = ['date_joined', 'name']

    def get_queryset(self):
        return User.objects.filter(is_staff=True, is_superuser=False)

    def get_serializer_class(self):
        if self.action == 'list':
            return StaffListSerializer
        return StaffCreateSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'CREATE', 'staff', instance.id, instance.name)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_activity(self.request.user, 'UPDATE', 'staff', instance.id, instance.name)

    def perform_destroy(self, instance):
        log_activity(self.request.user, 'DELETE', 'staff', instance.id, instance.name)
        instance.delete()
