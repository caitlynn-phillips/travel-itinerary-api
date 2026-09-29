from rest_framework import serializers
from .models import Review
from accounts.serializers import BaseUserSerializer


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    """

    user = BaseUserSerializer(read_only=True)
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True)
    activity_name = serializers.CharField(source='activity.name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'destination', 'destination_name', 'accommodation',
            'accommodation_name', 'activity', 'activity_name', 'rating',
            'title', 'content', 'visit_date', 'images', 'helpful_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'helpful_count', 'created_at', 'updated_at']

    def validate_rating(self, value):
        """Field-level validation for rating between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, attrs):
        """Custom validation: review must target exactly one entity."""
        dest = attrs.get('destination')
        acc = attrs.get('accommodation')
        act = attrs.get('activity')

        if self.instance:
            dest = dest if 'destination' in attrs else self.instance.destination
            acc = acc if 'accommodation' in attrs else self.instance.accommodation
            act = act if 'activity' in attrs else self.instance.activity

        targets = [dest, acc, act]
        if sum(1 for t in targets if t is not None) != 1:
            raise serializers.ValidationError("Review must target exactly one item (destination, accommodation, or activity).")

        return attrs

    def create(self, validated_data):
        """Automatically set current authenticated user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
