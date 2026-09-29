from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from destinations.models import Destination
from bookings.models import Accommodation, Activity


class Review(models.Model):
    """
    User reviews for destinations, accommodations, or activities.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
    )
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating score between 1 and 5.",
    )
    title = models.CharField(max_length=200, help_text="Review title.")
    content = models.TextField(help_text="Detailed review content.")
    visit_date = models.DateField(help_text="Date of visit.")
    images = models.JSONField(default=list, blank=True, help_text="List of image URLs.")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Helpful upvote count.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        indexes = [
            models.Index(fields=['destination', 'rating']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username} ({self.rating}/5)"

    def clean(self):
        """Ensures review is associated with exactly one item."""
        targets = [self.destination, self.accommodation, self.activity]
        specified_count = sum(1 for t in targets if t is not None)
        if specified_count != 1:
            raise ValidationError('Review must be for exactly one item (destination, accommodation, or activity).')
