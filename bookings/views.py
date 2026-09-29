from drf_spectacular.utils import extend_schema
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Accommodation, Activity, Booking
from .filters import BookingFilter, AccommodationFilter, ActivityFilter
from .permissions import IsBookingOwner
from .serializers import (
    AccommodationSerializer,
    ActivitySerializer,
    BookingSerializer,
    BookingDetailSerializer,
    BulkBookingUpdateSerializer,
)


class AccommodationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Browse accommodations with filtering and search.
    """

    queryset = Accommodation.objects.filter(is_available=True).select_related('destination')
    serializer_class = AccommodationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AccommodationFilter
    search_fields = ['name', 'description', 'address', 'destination__name']
    ordering_fields = ['name', 'price_per_night', 'created_at']


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Browse tours and activities with filtering and search.
    """

    queryset = Activity.objects.filter(is_available=True).select_related('destination')
    serializer_class = ActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ActivityFilter
    search_fields = ['name', 'description', 'destination__name']
    ordering_fields = ['name', 'price', 'duration_hours', 'created_at']


class BookingViewSet(viewsets.ModelViewSet):
    """
    Manage user bookings for accommodations or activities.
    """

    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookingFilter
    search_fields = ['confirmation_code', 'notes']
    ordering_fields = ['booking_date', 'price', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Booking.objects.none()
        return Booking.objects.filter(user=user).select_related(
            'accommodation', 'activity', 'itinerary', 'user'
        )

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy', 'confirm', 'cancel']:
            return [IsAuthenticated(), IsBookingOwner()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a pending booking.
        """
        booking = self.get_object()
        booking.confirm_booking()
        serializer = self.get_serializer(booking)
        return Response({
            'message': 'Booking confirmed successfully.',
            'booking': serializer.data,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        """
        booking = self.get_object()
        booking.cancel_booking()
        serializer = self.get_serializer(booking)
        return Response({
            'message': 'Booking cancelled.',
            'booking': serializer.data,
        }, status=status.HTTP_200_OK)


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    CBV Example 3: Retrieve, update, or delete a specific booking.
    """

    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated, IsBookingOwner]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related(
            'accommodation', 'activity', 'itinerary'
        )


@extend_schema(request=BulkBookingUpdateSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_bookings(request):
    """
    FBV Example 3: Bulk update multiple bookings in a single request.
    """
    serializer = BulkBookingUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    booking_ids = serializer.validated_data['booking_ids']
    new_status = serializer.validated_data['status']

    with transaction.atomic():
        updated_count = Booking.objects.filter(
            id__in=booking_ids,
            user=request.user,
        ).update(status=new_status)

    return Response({
        'message': f'Successfully updated {updated_count} bookings to {new_status}.',
        'updated_count': updated_count,
        'requested_count': len(booking_ids),
    }, status=status.HTTP_200_OK)
