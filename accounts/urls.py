"""
URL routes for the accounts app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('password/change/', views.ChangePasswordView.as_view(), name='password-change'),
    path('password/reset/', views.password_reset_request, name='password-reset'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
]