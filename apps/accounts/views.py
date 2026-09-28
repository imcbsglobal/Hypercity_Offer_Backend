import re
import secrets
from datetime import timedelta

from django.conf import settings
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
from .sms import build_otp_message, is_enabled as sms_enabled, send_sms
from apps.activity_logs.utils import log_activity


def generate_otp():
    return f'{secrets.randbelow(1000000):06d}'


def _normalize_phone(value):
    return re.sub(r'\D', '', value or '')


def _last_ten_digits(value):
    digits = _normalize_phone(value)
    return digits[-10:] if len(digits) >= 10 else ''


def is_known_customer(phone):
    digits = _last_ten_digits(phone)
    if not digits:
        return False
    from apps.synctool.models import AccMaster
    return (
        AccMaster.objects.exclude(phone2__isnull=True)
        .exclude(phone2='')
        .filter(phone2__endswith=digits)
        .exists()
    )


def _token_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'phone': user.phone,
            'name': user.name,
            'is_customer': user.is_customer,
            'role': user.role,
        }
    }


def _get_valid_otp(phone, code):
    entry = OTP.objects.filter(phone=phone, is_used=False).order_by('-created_at').first()
    if not entry:
        return None, 'Invalid OTP'

    if entry.is_expired:
        entry.delete()
        return None, 'OTP expired'

    if entry.attempts >= settings.SMS_MAX_ATTEMPTS:
        entry.delete()
        return None, 'Too many incorrect attempts. Please request a new OTP.'

    if not entry.check_code(code):
        entry.attempts += 1
        entry.save(update_fields=['attempts'])
        if entry.attempts >= settings.SMS_MAX_ATTEMPTS:
            entry.delete()
            return None, 'Too many incorrect attempts. Please request a new OTP.'
        return None, 'Invalid OTP'

    return entry, None


def _consume_otp(entry):
    entry.is_used = True
    entry.save(update_fields=['is_used'])


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SendOTPSerializer

    @extend_schema(request=SendOTPSerializer, responses={200: dict})
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = _last_ten_digits(serializer.validated_data['phone'])

        if not is_known_customer(phone):
            return Response(
                {'error': 'No customer account found with this number. Please contact admin.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_sent = OTP.objects.filter(phone=phone).order_by('-created_at').first()
        if last_sent:
            elapsed = (timezone.now() - last_sent.created_at).total_seconds()
            if elapsed < settings.SMS_RESEND_COOLDOWN:
                wait = int(settings.SMS_RESEND_COOLDOWN - elapsed) + 1
                return Response(
                    {'error': f'Please wait {wait} seconds before requesting a new OTP.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        code = generate_otp()
        entry = OTP.objects.create(
            phone=phone,
            otp='',
            expires_at=timezone.now() + timedelta(minutes=settings.SMS_OTP_EXPIRY_MINUTES),
        )
        entry.set_code(code)
        entry.save(update_fields=['otp'])

        result = send_sms(phone, build_otp_message(code))
        if sms_enabled() and not result['ok']:
            entry.delete()
            return Response(
                {'error': 'Could not send OTP. Please try again later.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if result['submission_id']:
            entry.sms_submission_id = result['submission_id'][:100]
            entry.save(update_fields=['sms_submission_id'])

        data = {'message': 'OTP sent successfully'}
        if settings.DEBUG and not sms_enabled():
            data['otp'] = code
        return Response(data, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    @extend_schema(request=VerifyOTPSerializer, responses={200: dict})
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = _last_ten_digits(serializer.validated_data['phone'])
        otp_code = serializer.validated_data['otp']

        otp_entry, error = _get_valid_otp(phone, otp_code)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        _consume_otp(otp_entry)

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

        return Response(_token_payload(user), status=status.HTTP_200_OK)


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    @extend_schema(request=SignupSerializer, responses={201: dict})
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = _last_ten_digits(serializer.validated_data['phone'])
        otp_code = serializer.validated_data['otp']
        name = serializer.validated_data['name']

        otp_entry, error = _get_valid_otp(phone, otp_code)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone=phone).exists():
            return Response({'error': 'Account already exists. Please login.'}, status=status.HTTP_400_BAD_REQUEST)

        _consume_otp(otp_entry)

        user = User.objects.create_user(
            phone=phone,
            name=name,
            role='CUSTOMER',
            is_customer=True,
        )

        return Response(_token_payload(user), status=status.HTTP_201_CREATED)


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
