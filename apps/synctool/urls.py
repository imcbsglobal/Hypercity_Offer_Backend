from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .my_invoices import MyInvoicesView
from .views import AccMasterViewSet, MiselViewSet, AccInvMastViewSet

router = DefaultRouter()
router.register('acc-master', AccMasterViewSet, basename='acc-master')
router.register('misel', MiselViewSet, basename='misel')
router.register('acc-invmast', AccInvMastViewSet, basename='acc-invmast')

urlpatterns = [
    path('my-invoices/', MyInvoicesView.as_view(), name='synctool-my-invoices'),
    path('', include(router.urls)),
]