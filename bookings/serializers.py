from rest_framework import serializers
from .models import Accommodation, Activity, Booking
from accounts.serializers import BaseUserSerializer


class AccommodationSerializer(serializers.ModelSerializer):
    """
    Serializer for accommodation properties.
    """

    destination_name = serializers.CharField(source='destination.name', read_only=True)

    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'destination', 'destination_name', 'accommodation_type',
            'description', 'price_per_night', 'max_guests', 'amenities',
            'address', 'contact_email', 'contact_phone', 'image',
            'is_available', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_price_per_night(self, value):
        """Field-level validation: nightly price must be greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("Price per night must be greater than 0.")
        return value


class ActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for tours and activities.
    """

    destination_name = serializers.CharField(source='destination.name', read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'name', 'destination', 'destination_name', 'category',
            'description', 'duration_hours', 'price', 'max_participants',
            'requirements', 'image', 'is_available', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_price(self, value):
        """Field-level validation: activity price cannot be negative."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for booking creation, list, and update operations.
    """

    accommodation_detail = AccommodationSerializer(source='accommodation', read_only=True)
    activity_detail = ActivitySerializer(source='activity', read_only=True)
    accommodation = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(),
        required=False,
        allow_null=True,
    )
    activity = serializers.PrimaryKeyRelatedField(
        queryset=Activity.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'itinerary', 'accommodation', 'accommodation_detail',
            'activity', 'activity_detail', 'booking_date', 'check_in', 'check_out',
            'guests_count', 'price', 'status', 'confirmation_code', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Custom validation: check accommodation or activity exclusive presence."""
        acc = attrs.get('accommodation')
        act = attrs.get('activity')

        # On update, check instance defaults if not provided in attrs
        if self.instance:
            acc = acc if 'accommodation' in attrs else self.instance.accommodation
            act = act if 'activity' in attrs else self.instance.activity

        if not acc and not act:
            raise serializers.ValidationError("Booking must specify either an accommodation or an activity.")
        if acc and act:
            raise serializers.ValidationError("Booking cannot have both accommodation and activity.")

        check_in = attrs.get('check_in')
        check_out = attrs.get('check_out')
        if acc and check_in and check_out and check_out < check_in:
            raise serializers.ValidationError({"check_out": "Check-out date must be after check-in date."})

        return attrs

    def create(self, validated_data):
        """Override create to assign current user and calculate price if default."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        # Auto-calculate price if 0 or not provided
        acc = validated_data.get('accommodation')
        act = validated_data.get('activity')
        price = validated_data.get('price')

        if not price or price == 0:
            if acc:
                nights = 1
                cin = validated_data.get('check_in')
                cout = validated_data.get('check_out')
                if cin and cout:
                    nights = max((cout - cin).days, 1)
                validated_data['price'] = acc.price_per_night * nights * validated_data.get('guests_count', 1)
            elif act:
                validated_data['price'] = act.price * validated_data.get('guests_count', 1)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Override update to handle status updates and recalculations."""
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Override to_representation to inject item summary."""
        data = super().to_representation(instance)
        if instance.accommodation:
            data['item_type'] = 'accommodation'
            data['item_name'] = instance.accommodation.name
        elif instance.activity:
            data['item_type'] = 'activity'
            data['item_name'] = instance.activity.name
        else:
            data['item_type'] = 'unknown'
            data['item_name'] = 'N/A'
        return data


class BookingDetailSerializer(BookingSerializer):
    """
    Detailed serializer including user info.
    """

    user = BaseUserSerializer(read_only=True)


class BulkBookingUpdateSerializer(serializers.Serializer):
    """
    Serializer for bulk booking updates FBV.
    """

    booking_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of booking IDs to update.",
    )
    status = serializers.ChoiceField(
        choices=Booking.StatusChoices.choices,
        help_text="Target status for bulk update.",
    )

    def validate_booking_ids(self, value):
        if not value:
            raise serializers.ValidationError("booking_ids list cannot be empty.")
        return value
