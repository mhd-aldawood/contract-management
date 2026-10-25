from django.urls import path
from contract.finance import (FinanceAgreementListView, DisbursementOrderListView,
                              DisbursementOrderDetailView, DisbursementOrderFileView)

urlpatterns = [
    path('agreements/', FinanceAgreementListView.as_view(), name='finance-agreements'),
    path('agreements/<slug:kind>/<int:pk>/orders/', DisbursementOrderListView.as_view(), name='finance-orders'),
    path('agreements/<slug:kind>/<int:pk>/orders/<int:order_id>/', DisbursementOrderDetailView.as_view(), name='finance-order'),
    path('agreements/<slug:kind>/<int:pk>/orders/<int:order_id>/file/', DisbursementOrderFileView.as_view(), name='finance-order-file'),
]
