from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API
    path('api/', include('apps.accounts.urls')),
    path('api/branches/', include('apps.branches.urls')),
    path('api/offers/', include('apps.offers.urls')),
    path('api/banners/', include('apps.banners.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/activity-logs/', include('apps.activity_logs.urls')),
    path('api/dashboard/', include('apps.admin_dashboard.urls')),
    path('api/synctool/', include('apps.synctool.urls')),

    # Swagger docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
