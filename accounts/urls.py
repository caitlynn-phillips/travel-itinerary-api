from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register,
    login,
    UserProfileView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

app_name = 'accounts'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]