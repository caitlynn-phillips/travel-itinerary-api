from django_filters import rest_framework as filters
from .models import Booking, Accommodation, Activity


class BookingFilter(filters.FilterSet):
    """
    Filters for user bookings.
    """

    status = filters.ChoiceFilter(choices=Booking.StatusChoices.choices)
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    booking_date_after = filters.DateFilter(field_name='booking_date', lookup_expr='gte')
    booking_date_before = filters.DateFilter(field_name='booking_date', lookup_expr='lte')
    has_accommodation = filters.BooleanFilter(field_name='accommodation', lookup_expr='isnull', exclude=True)
    has_activity = filters.BooleanFilter(field_name='activity', lookup_expr='isnull', exclude=True)

    class Meta:
        model = Booking
        fields = ['status', 'itinerary', 'user']


class AccommodationFilter(filters.FilterSet):
    accommodation_type = filters.ChoiceFilter(choices=Accommodation.TypeChoices.choices)
    min_price = filters.NumberFilter(field_name='price_per_night', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price_per_night', lookup_expr='lte')

    class Meta:
        model = Accommodation
        fields = ['destination', 'accommodation_type', 'is_available']


class ActivityFilter(filters.FilterSet):
    category = filters.ChoiceFilter(choices=Activity.CategoryChoices.choices)
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Activity
        fields = ['destination', 'category', 'is_available']
