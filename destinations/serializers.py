from rest_framework import serializers
from .models import Destination


class BaseDestinationSerializer(serializers.ModelSerializer):
    """
    Base serializer for Destination model to demonstrate serializer inheritance.
    """

    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'country', 'description', 'category',
            'climate', 'best_time_to_visit', 'avg_daily_cost', 'image',
            'latitude', 'longitude', 'is_active',
        ]
        read_only_fields = ['id']


class DestinationListSerializer(BaseDestinationSerializer):
    """
    Lightweight serializer for destination list views.
    """

    average_rating = serializers.ReadOnlyField(help_text="Average review rating (0.0 to 5.0).")
    review_count = serializers.SerializerMethodField(help_text="Total number of reviews.")

    class Meta(BaseDestinationSerializer.Meta):
        fields = BaseDestinationSerializer.Meta.fields + ['average_rating', 'review_count']

    def get_review_count(self, obj):
        return obj.reviews.count()


class DestinationDetailSerializer(BaseDestinationSerializer):
    """
    Detailed serializer for destination retrieve view.
    """

    average_rating = serializers.ReadOnlyField(help_text="Average review rating.")
    total_itineraries = serializers.SerializerMethodField(help_text="Total itineraries featuring this destination.")
    top_activities = serializers.SerializerMethodField(help_text="Top activities available at destination.")

    class Meta(BaseDestinationSerializer.Meta):
        fields = BaseDestinationSerializer.Meta.fields + [
            'average_rating', 'total_itineraries', 'top_activities',
            'created_at', 'updated_at',
        ]
        read_only_fields = BaseDestinationSerializer.Meta.read_only_fields + ['created_at', 'updated_at']

    def get_total_itineraries(self, obj):
        return obj.itineraries.count()

    def get_top_activities(self, obj):
        from bookings.serializers import ActivitySerializer
        activities = obj.activities.filter(is_available=True)[:5]
        return ActivitySerializer(activities, many=True).data

    def to_representation(self, instance):
        """Override to_representation to customize output structure."""
        data = super().to_representation(instance)
        data['summary'] = f"{instance.name}, {instance.country} ({instance.get_category_display()})"
        return data


class DestinationCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating destinations.
    """

    class Meta:
        model = Destination
        fields = [
            'name', 'country', 'description', 'category',
            'climate', 'best_time_to_visit', 'avg_daily_cost',
            'image', 'latitude', 'longitude', 'is_active',
        ]

    def validate_avg_daily_cost(self, value):
        """Field-level validation: cost must be positive."""
        if value < 0:
            raise serializers.ValidationError("Average daily cost cannot be negative.")
        return value

    def validate(self, attrs):
        """Custom validation: lat and long must be provided together if provided."""
        lat = attrs.get('latitude')
        lng = attrs.get('longitude')
        if (lat is None and lng is not None) or (lat is not None and lng is None):
            raise serializers.ValidationError("Both latitude and longitude must be provided together.")
        return attrs
