from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SendOTPView, VerifyOTPView, SignupView, ProfileView, AdminLoginView, StaffViewSet, UpdateFCMTokenView

router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    path('auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('auth/update-fcm-token/', UpdateFCMTokenView.as_view(), name='update-fcm-token'),
    path('auth/admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('', include(router.urls)),
]
