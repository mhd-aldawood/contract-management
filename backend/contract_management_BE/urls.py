"""
URL configuration for contract_management_BE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from contract.planning import PlanningAgreementListView
from contract.dashboard import DashboardView
from contract.agreement_orders import AgreementOrderListView, AgreementOrderFileView
from contract.security_views import SecuritySettingsView
from contract.requests_api import ContractRequestListCreateView, ContractRequestDetailView
from contract.doctoral import DoctoralContractListCreateView, DoctoralContractDetailView
from contract.file_access import DownloadGrantView, SecureDownloadView

urlpatterns = [
    path('api/contract-requests/', ContractRequestListCreateView.as_view(), name='contract-request-list'),
    path('api/contract-requests/<int:pk>/', ContractRequestDetailView.as_view(), name='contract-request-detail'),
    path('api/doctoral-contracts/', DoctoralContractListCreateView.as_view(), name='doctoral-contract-list'),
    path('api/doctoral-contracts/<int:pk>/', DoctoralContractDetailView.as_view(), name='doctoral-contract-detail'),
    path('api/files/grants/', DownloadGrantView.as_view(), name='download-grant'),
    path('api/files/download/', SecureDownloadView.as_view(), name='secure-download'),
    path('api/security-settings/', SecuritySettingsView.as_view(), name='security-settings'),
    path('api/agreement-orders/<slug:kind>/<int:pk>/', AgreementOrderListView.as_view(), name='agreement-orders'),
    path('api/agreement-orders/<slug:kind>/<int:pk>/<int:order_id>/file/', AgreementOrderFileView.as_view(), name='agreement-order-file'),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/planning/agreements/', PlanningAgreementListView.as_view(), name='planning-agreements'),
    path('api/finance/', include('contract.finance_urls')),
    path('api/dean/', include('contract.dean_urls')),
    path('admin/', admin.site.urls),
    path('api/auth/', include('contract.urls')),
    # Educational content — separate prefix
    path('api/', include('contract.educational_content.urls')),
    path('api/', include('contract.nafath_center.urls')),
    path('api/', include('contract.life_long.urls')),
    path('api/', include('contract.other.urls')),
]
