from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Budget(models.Model):
    """
    Detailed category budget allocation for an itinerary.
    """

    itinerary = models.OneToOneField(
        'itineraries.Itinerary',
        on_delete=models.CASCADE,
        related_name='budget_detail',
    )
    accommodation_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    activities_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    food_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    transport_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    shopping_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    miscellaneous_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'

    def __str__(self):
        return f"Budget for {self.itinerary.title}"

    @property
    def total_budget(self):
        """Calculates total budget sum across categories."""
        return (
            (self.accommodation_budget or 0) +
            (self.activities_budget or 0) +
            (self.food_budget or 0) +
            (self.transport_budget or 0) +
            (self.shopping_budget or 0) +
            (self.miscellaneous_budget or 0)
        )


class Expense(models.Model):
    """
    Individual tracked expense item within a trip budget.
    """

    class CategoryChoices(models.TextChoices):
        ACCOMMODATION = 'accommodation', 'Accommodation'
        ACTIVITIES = 'activities', 'Activities'
        FOOD = 'food', 'Food'
        TRANSPORT = 'transport', 'Transport'
        SHOPPING = 'shopping', 'Shopping'
        MISCELLANEOUS = 'miscellaneous', 'Miscellaneous'

    itinerary = models.ForeignKey(
        'itineraries.Itinerary',
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        help_text="Expense category.",
    )
    description = models.CharField(max_length=200, help_text="Short description of item or receipt.")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Amount spent.",
    )
    date = models.DateField(help_text="Expense date.")
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'

    def __str__(self):
        return f"{self.description} - ${self.amount}"

    def clean(self):
        """Validates that amount is positive."""
        if self.amount is not None and self.amount < 0:
            raise ValidationError({'amount': 'Expense amount must be greater than or equal to 0.'})
