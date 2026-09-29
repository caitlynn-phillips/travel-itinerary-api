from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from destinations.models import Destination


class Itinerary(models.Model):
    """
    Main itinerary model representing a user's trip plan.
    """

    class StatusChoices(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        BOOKED = 'booked', 'Booked'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    title = models.CharField(max_length=200, help_text="Trip title.")
    description = models.TextField(blank=True, help_text="Trip summary or notes.")
    destination = models.ForeignKey(
        Destination,
        on_delete=models.PROTECT,
        related_name='itineraries',
        help_text="Target destination.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_itineraries',
        help_text="Owner/creator of the trip.",
    )
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Collaboration',
        related_name='shared_itineraries',
        blank=True,
    )
    start_date = models.DateField(help_text="Trip start date.")
    end_date = models.DateField(help_text="Trip end date.")
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total target budget.",
    )
    actual_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Tracked actual expenditure.",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNING,
    )
    is_public = models.BooleanField(default=False, help_text="Whether trip is publicly discoverable.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Itinerary'
        verbose_name_plural = 'Itineraries'
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.destination.name}"

    def clean(self):
        """Ensures end_date is on or after start_date and budget is non-negative."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date must be on or after start date.'})
        if self.budget is not None and self.budget < 0:
            raise ValidationError({'budget': 'Budget must be greater than or equal to 0.'})

    @property
    def duration_days(self):
        """Calculates total trip duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def budget_remaining(self):
        """Calculates remaining budget."""
        return (self.budget or 0) - (self.actual_spent or 0)

    def add_collaborator(self, user, role='viewer'):
        """Adds a user as collaborator with specified role."""
        collaboration, created = Collaboration.objects.get_or_create(
            itinerary=self,
            user=user,
            defaults={'role': role}
        )
        if not created and collaboration.role != role:
            collaboration.role = role
            collaboration.save(update_fields=['role'])
        return collaboration


class Collaboration(models.Model):
    """
    Through model for itinerary collaboration with role-based access.
    """

    class RoleChoices(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        EDITOR = 'editor', 'Editor'
        ADMIN = 'admin', 'Admin'

    itinerary = models.ForeignKey(
        Itinerary,
        on_delete=models.CASCADE,
        related_name='collaborations',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collaborations',
    )
    role = models.CharField(
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.VIEWER,
    )
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['itinerary', 'user']
        verbose_name = 'Collaboration'
        verbose_name_plural = 'Collaborations'

    def __str__(self):
        return f"{self.user.username} - {self.itinerary.title} ({self.role})"


class DailyPlan(models.Model):
    """
    Day-by-day plan within an itinerary.
    """

    itinerary = models.ForeignKey(
        Itinerary,
        on_delete=models.CASCADE,
        related_name='daily_plans',
    )
    day_number = models.PositiveIntegerField()
    date = models.DateField()
    title = models.CharField(max_length=200, help_text="Day focus/title.")
    notes = models.TextField(blank=True, help_text="Notes for the day.")
    activities = models.ManyToManyField(
        'bookings.Activity',
        related_name='daily_plans',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ['itinerary', 'day_number']
        verbose_name = 'Daily Plan'
        verbose_name_plural = 'Daily Plans'

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"

    def clean(self):
        """Ensures day_number is greater than 0."""
        if self.day_number is not None and self.day_number < 1:
            raise ValidationError({'day_number': 'Day number must be at least 1.'})
