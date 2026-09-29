from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Destination(models.Model):
    """
    Tourist destination with details and ratings.
    """

    class ClimateChoices(models.TextChoices):
        TROPICAL = 'tropical', 'Tropical'
        DRY = 'dry', 'Dry'
        TEMPERATE = 'temperate', 'Temperate'
        CONTINENTAL = 'continental', 'Continental'
        POLAR = 'polar', 'Polar'

    class CategoryChoices(models.TextChoices):
        BEACH = 'beach', 'Beach'
        MOUNTAIN = 'mountain', 'Mountain'
        CITY = 'city', 'City'
        CULTURAL = 'cultural', 'Cultural'
        ADVENTURE = 'adventure', 'Adventure'
        RELAXATION = 'relaxation', 'Relaxation'

    name = models.CharField(max_length=200, unique=True, help_text="Destination name.")
    country = models.CharField(max_length=100, help_text="Country where destination is located.")
    description = models.TextField(help_text="Detailed description of the destination.")
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        help_text="Category/type of destination.",
    )
    climate = models.CharField(
        max_length=20,
        choices=ClimateChoices.choices,
        help_text="Climate zone.",
    )
    best_time_to_visit = models.CharField(max_length=200, help_text="Optimal months/seasons to visit.")
    avg_daily_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Estimated average daily cost per person.",
    )
    image = models.ImageField(upload_to='destinations/', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Destination'
        verbose_name_plural = 'Destinations'
        indexes = [
            models.Index(fields=['country', 'category']),
            models.Index(fields=['climate']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country}"

    def clean(self):
        """Model validation for coordinates and costs."""
        if self.latitude is not None and (self.latitude < -90 or self.latitude > 90):
            raise ValidationError({'latitude': 'Latitude must be between -90 and 90 degrees.'})
        if self.longitude is not None and (self.longitude < -180 or self.longitude > 180):
            raise ValidationError({'longitude': 'Longitude must be between -180 and 180 degrees.'})
        if self.avg_daily_cost is not None and self.avg_daily_cost < 0:
            raise ValidationError({'avg_daily_cost': 'Average daily cost cannot be negative.'})

    @property
    def average_rating(self):
        """Calculates average rating from associated reviews."""
        ratings = self.reviews.aggregate(models.Avg('rating'))
        return round(ratings['rating__avg'] or 0.0, 2)
