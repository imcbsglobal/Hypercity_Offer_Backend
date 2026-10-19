from django.urls import path

from .views import PublicFormResponseView, PublicFormView

urlpatterns = [
    path('<uuid:public_id>/', PublicFormView.as_view(), name='public-form'),
    path('<uuid:public_id>/responses/', PublicFormResponseView.as_view(), name='public-form-responses'),
]
