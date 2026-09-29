from django_filters import rest_framework as filters
from .models import Destination


class DestinationFilter(filters.FilterSet):
    """
    Advanced destination filtering with custom budget_range logic.
    """

    min_cost = filters.NumberFilter(field_name='avg_daily_cost', lookup_expr='gte')
    max_cost = filters.NumberFilter(field_name='avg_daily_cost', lookup_expr='lte')
    climate = filters.MultipleChoiceFilter(choices=Destination.ClimateChoices.choices)
    category = filters.MultipleChoiceFilter(choices=Destination.CategoryChoices.choices)
    country = filters.CharFilter(lookup_expr='icontains')
    budget_range = filters.CharFilter(method='filter_by_budget')

    class Meta:
        model = Destination
        fields = ['country', 'category', 'climate', 'is_active']

    def filter_by_budget(self, queryset, name, value):
        """Custom filtering logic for budget ranges."""
        if value == 'budget':
            return queryset.filter(avg_daily_cost__lt=100)
        elif value == 'moderate':
            return queryset.filter(avg_daily_cost__gte=100, avg_daily_cost__lt=250)
        elif value == 'luxury':
            return queryset.filter(avg_daily_cost__gte=250)
        return queryset
