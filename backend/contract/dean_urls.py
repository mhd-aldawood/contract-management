from django.urls import path

from contract.dean import (DeanAgreementListView, DeanAgreementDetailView,
                           DeanAgreementVisibilityView, DeanOrderFileView)

urlpatterns = [
    path('agreements/', DeanAgreementListView.as_view(), name='dean-agreements'),
    path('agreements/<slug:kind>/<int:pk>/', DeanAgreementDetailView.as_view(), name='dean-agreement'),
    path('agreements/<slug:kind>/<int:pk>/visibility/', DeanAgreementVisibilityView.as_view(), name='dean-visibility'),
    path('agreements/<slug:kind>/<int:pk>/orders/<int:order_id>/file/', DeanOrderFileView.as_view(), name='dean-order-file'),
]
