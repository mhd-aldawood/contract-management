from django.urls import path

from contract.other.views import AgreementCreateView

urlpatterns = [
    path('other-agreement/create', AgreementCreateView.as_view(), name='other-agreement'),
]