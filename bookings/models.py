from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from destinations.models import Destination


class Accommodation(models.Model):
    """
    Hotels, hostels, vacation rentals, resorts, B&Bs.
    """

    class TypeChoices(models.TextChoices):
        HOTEL = 'hotel', 'Hotel'
        HOSTEL = 'hostel', 'Hostel'
        RENTAL = 'rental', 'Vacation Rental'
        RESORT = 'resort', 'Resort'
        BNB = 'bnb', 'B&B'

    name = models.CharField(max_length=200, help_text="Accommodation property name.")
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='accommodations',
        help_text="Target destination.",
    )
    accommodation_type = models.CharField(
        max_length=10,
        choices=TypeChoices.choices,
        help_text="Property type.",
    )
    description = models.TextField(help_text="Overview and amenities description.")
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Nightly rate.",
    )
    max_guests = models.PositiveIntegerField(default=2, help_text="Maximum guest capacity.")
    amenities = models.JSONField(default=list, blank=True, help_text="List of amenities e.g. WiFi, Pool.")
    address = models.CharField(max_length=300, help_text="Physical address.")
    contact_email = models.EmailField(help_text="Contact email.")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Contact phone.")
    image = models.ImageField(upload_to='accommodations/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Accommodation'
        verbose_name_plural = 'Accommodations'
        indexes = [
            models.Index(fields=['destination', 'accommodation_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_accommodation_type_display()})"


class Activity(models.Model):
    """
    Tours, attractions, experiences, and activities.
    """

    class CategoryChoices(models.TextChoices):
        TOUR = 'tour', 'Tour'
        ATTRACTION = 'attraction', 'Attraction'
        DINING = 'dining', 'Dining'
        SHOPPING = 'shopping', 'Shopping'
        ENTERTAINMENT = 'entertainment', 'Entertainment'
        OUTDOOR = 'outdoor', 'Outdoor'

    name = models.CharField(max_length=200, help_text="Activity title.")
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='activities',
        help_text="Target destination.",
    )
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        help_text="Activity category.",
    )
    description = models.TextField(help_text="Description of experience.")
    duration_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0)],
        help_text="Duration in hours.",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Cost per person.",
    )
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    requirements = models.TextField(blank=True, help_text="Prerequisites or clothing recommendations.")
    image = models.ImageField(upload_to='activities/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        indexes = [
            models.Index(fields=['destination', 'category']),
        ]

    def __str__(self):
        return f"{self.name} - {self.destination.name}"


class Booking(models.Model):
    """
    User reservations for accommodations or activities linked to an itinerary.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    itinerary = models.ForeignKey(
        'itineraries.Itinerary',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
    )
    booking_date = models.DateField(help_text="Date of booking.")
    check_in = models.DateField(null=True, blank=True, help_text="Check-in date for accommodation.")
    check_out = models.DateField(null=True, blank=True, help_text="Check-out date for accommodation.")
    guests_count = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total calculated booking price.",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    confirmation_code = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['itinerary']),
        ]

    def __str__(self):
        if self.accommodation:
            return f"Booking ({self.status}): {self.accommodation.name}"
        elif self.activity:
            return f"Booking ({self.status}): {self.activity.name}"
        return f"Booking #{self.id}"

    def clean(self):
        """Validates booking constraints."""
        if not self.accommodation and not self.activity:
            raise ValidationError('Booking must have either an accommodation or an activity.')
        if self.accommodation and self.activity:
            raise ValidationError('Booking cannot have both an accommodation and an activity.')
        if self.accommodation:
            if self.check_in and self.check_out and self.check_out < self.check_in:
                raise ValidationError({'check_out': 'Check-out date must be after check-in date.'})

    def confirm_booking(self):
        """Business logic method: Confirms the booking and sets confirmation code if empty."""
        import uuid
        self.status = self.StatusChoices.CONFIRMED
        if not self.confirmation_code:
            self.confirmation_code = f"CONF-{uuid.uuid4().hex[:8].upper()}"
        self.save()

    def cancel_booking(self):
        """Business logic method: Cancels the booking."""
        self.status = self.StatusChoices.CANCELLED
        self.save()
