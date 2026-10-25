from django.urls import path

from contract.other.views import (AgreementCreateView, AgreementListView,
                                 MemorandumCreateView, MemorandumListView)

urlpatterns = [
    path('other-agreement/', AgreementListView.as_view(), name='other-agreement-list'),
    path('memorandum/', MemorandumListView.as_view(), name='memorandum-list'),
    path('memorandum/create', MemorandumCreateView.as_view(), name='memorandum-create'),
    path('other-agreement/create', AgreementCreateView.as_view(), name='other-agreement'),
]
