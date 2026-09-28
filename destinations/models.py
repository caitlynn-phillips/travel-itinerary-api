"""
Models for the destinations app.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg
from django.utils.text import slugify


class Destination(models.Model):
    """
    A tourist destination that itineraries, accommodations,
    activities and reviews attach to.
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

    name = models.CharField(max_length=200, unique=True, help_text='Destination name, e.g. Paris.')
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text='URL-friendly name. Generated automatically from the name.',
    )
    country = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    climate = models.CharField(max_length=20, choices=ClimateChoices.choices)
    best_time_to_visit = models.CharField(max_length=200)
    avg_daily_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Average daily cost per traveler.',
    )
    image = models.ImageField(upload_to='destinations/', null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['country', 'category']),
            models.Index(fields=['climate']),
            models.Index(fields=['avg_daily_cost']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country}"

    def clean(self):
        """Latitude and longitude must be given together or not at all."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError('Provide both latitude and longitude, or neither.')

    def save(self, *args, **kwargs):
        """Generate a unique slug from the name the first time we save."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2
            while Destination.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        """Average review rating, rounded to one decimal, or 0 if unreviewed."""
        result = self.reviews.aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else 0

    @property
    def budget_category(self):
        """Label the destination as budget, moderate or luxury by daily cost."""
        if self.avg_daily_cost < 100:
            return 'budget'
        if self.avg_daily_cost < 250:
            return 'moderate'
        return 'luxury'