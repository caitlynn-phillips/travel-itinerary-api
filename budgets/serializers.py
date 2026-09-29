from rest_framework import serializers
from .models import Budget, Expense


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for Budget allocations.
    """

    total_budget = serializers.ReadOnlyField(help_text="Calculated sum of all category budgets.")
    itinerary_title = serializers.CharField(source='itinerary.title', read_only=True)
    total_expenses = serializers.SerializerMethodField(help_text="Sum of all recorded expenses.")

    class Meta:
        model = Budget
        fields = [
            'id', 'itinerary', 'itinerary_title', 'accommodation_budget',
            'activities_budget', 'food_budget', 'transport_budget',
            'shopping_budget', 'miscellaneous_budget', 'total_budget',
            'total_expenses', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'itinerary', 'created_at', 'updated_at']

    def get_total_expenses(self, obj):
        from django.db.models import Sum
        result = obj.itinerary.expenses.aggregate(Sum('amount'))
        return result['amount__sum'] or 0.00


class ExpenseSerializer(serializers.ModelSerializer):
    """
    Serializer for recorded expenses.
    """

    itinerary_title = serializers.CharField(source='itinerary.title', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'itinerary', 'itinerary_title', 'category',
            'description', 'amount', 'date', 'receipt',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        """Field-level validation for expense amount."""
        if value <= 0:
            raise serializers.ValidationError("Expense amount must be greater than zero.")
        return value
