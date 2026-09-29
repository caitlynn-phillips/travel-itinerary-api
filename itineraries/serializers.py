from rest_framework import serializers
from .models import Itinerary, Collaboration, DailyPlan
from destinations.models import Destination
from destinations.serializers import DestinationListSerializer
from bookings.serializers import ActivitySerializer
from accounts.serializers import BaseUserSerializer


class CollaborationSerializer(serializers.ModelSerializer):
    """
    Serializer for itinerary collaborations through model.
    """

    user = BaseUserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Collaboration
        fields = ['id', 'user', 'user_id', 'username', 'role', 'invited_at']
        read_only_fields = ['id', 'invited_at']


class DailyPlanSerializer(serializers.ModelSerializer):
    """
    Daily plan serializer with nested activities.
    """

    activities_detail = ActivitySerializer(source='activities', many=True, read_only=True)
    activities_count = serializers.SerializerMethodField(help_text="Number of activities planned for this day.")

    class Meta:
        model = DailyPlan
        fields = [
            'id', 'itinerary', 'day_number', 'date', 'title',
            'notes', 'activities', 'activities_detail', 'activities_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_activities_count(self, obj):
        return obj.activities.count()


class ItineraryListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing itineraries.
    """

    destination_name = serializers.CharField(source='destination.name', read_only=True)
    destination_country = serializers.CharField(source='destination.country', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    duration_days = serializers.ReadOnlyField()
    budget_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Itinerary
        fields = [
            'id', 'title', 'destination', 'destination_name', 'destination_country',
            'owner', 'owner_username', 'start_date', 'end_date', 'duration_days',
            'budget', 'actual_spent', 'budget_remaining', 'status', 'is_public',
            'created_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at']


class ItineraryDetailSerializer(serializers.ModelSerializer):
    """
    Full detailed itinerary serializer with nested destination, daily plans, collaborations.
    """

    destination = DestinationListSerializer(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.all(),
        source='destination',
        write_only=True,
    )
    owner = BaseUserSerializer(read_only=True)
    daily_plans = DailyPlanSerializer(many=True, read_only=True)
    collaborations = CollaborationSerializer(many=True, read_only=True)
    bookings_count = serializers.SerializerMethodField(help_text="Total reservations under this itinerary.")
    duration_days = serializers.ReadOnlyField()
    budget_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Itinerary
        fields = [
            'id', 'title', 'description', 'destination', 'destination_id',
            'owner', 'collaborations', 'daily_plans', 'start_date', 'end_date',
            'duration_days', 'budget', 'actual_spent', 'budget_remaining',
            'status', 'is_public', 'bookings_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_bookings_count(self, obj):
        return obj.bookings.count()

    def validate(self, attrs):
        """Custom validation: check end_date >= start_date and positive budget."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date must be on or after start date.'})

        return attrs

    def create(self, validated_data):
        """Create itinerary and automatically initialize budget object."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['owner'] = request.user

        itinerary = super().create(validated_data)

        # Auto-create associated budget
        from budgets.models import Budget
        Budget.objects.get_or_create(itinerary=itinerary)

        return itinerary

    def update(self, instance, validated_data):
        """Update itinerary details."""
        return super().update(instance, validated_data)


class ItineraryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer dedicated to create/update operations.
    """

    class Meta:
        model = Itinerary
        fields = [
            'title', 'description', 'destination',
            'start_date', 'end_date', 'budget', 'is_public', 'status',
        ]

    def validate_budget(self, value):
        """Field-level validation for budget."""
        if value <= 0:
            raise serializers.ValidationError("Budget must be greater than zero.")
        return value

    def validate(self, attrs):
        """Custom validation for dates."""
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        return attrs
