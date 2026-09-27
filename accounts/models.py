from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the Travel Itinerary Planning & Booking API.

    Extends Django's AbstractUser with the traveler-specific profile fields
    the platform needs (contact info, bio, preferences) while keeping the
    built-in auth fields (username, password, is_staff, etc.).
    """

    email = models.EmailField(unique=True, help_text="Unique email, used for login and notifications.")
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number.")
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, help_text="Short traveler bio.")
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    travel_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Free-form preferences used for recommendations, e.g. {'climate': 'tropical'}.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        """Convenience accessor combining first/last name, falling back to username."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
