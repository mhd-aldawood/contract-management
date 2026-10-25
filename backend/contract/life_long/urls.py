from django.urls import path
from .views import LifeLongCreateView, LifeLongListView

urlpatterns = [
    path('life-long/', LifeLongListView.as_view(), name='life-long-list'),
    path('life-long/create', LifeLongCreateView.as_view(), name='life-long-create'),
]
