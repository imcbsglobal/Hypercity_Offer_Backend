from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomFormViewSet

router = DefaultRouter()
router.register('', CustomFormViewSet, basename='custom-forms')

urlpatterns = [path('', include(router.urls))]
