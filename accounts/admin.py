from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin config for the custom User model, extending Django's default UserAdmin."""

    fieldsets = UserAdmin.fieldsets + (
        ('Traveler profile', {
            'fields': ('phone', 'date_of_birth', 'bio', 'profile_picture', 'travel_preferences'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
