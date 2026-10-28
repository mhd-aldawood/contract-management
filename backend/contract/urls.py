from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    MeView,
    TokenRefreshView,
    AccessControlView,
    ChangePasswordView,
    UserManagementView,
    UserManagementDetailView,
    RefreshCsrfView,
)
urlpatterns = [
    path('csrf/', RefreshCsrfView.as_view(), name='refresh-csrf'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('access-control/', AccessControlView.as_view(), name='access-control'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('users/', UserManagementView.as_view(), name='user-management'),
    path('users/<int:pk>/', UserManagementDetailView.as_view(), name='user-management-detail'),
]
