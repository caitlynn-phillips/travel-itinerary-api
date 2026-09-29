from datetime import date
from django.db import transaction
from django.db.models import Q, Count, Sum, F, Prefetch
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Itinerary, Collaboration, DailyPlan
from .filters import ItineraryFilter
from .permissions import IsTripOwner, IsTripOwnerOrCollaborator, CanEditItinerary
from .serializers import (
    ItineraryListSerializer,
    ItineraryDetailSerializer,
    ItineraryCreateUpdateSerializer,
    CollaborationSerializer,
    DailyPlanSerializer,
)

User = get_user_model()


class ItineraryViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD operations for itineraries plus custom actions.
    """

    permission_classes = [IsAuthenticated, CanEditItinerary]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ItineraryFilter
    search_fields = ['title', 'description', 'destination__name', 'destination__country']
    ordering_fields = ['created_at', 'start_date', 'budget']

    def get_queryset(self):
        """Query optimization using select_related, prefetch_related, and Prefetch."""
        user = self.request.user
        if not user.is_authenticated:
            return Itinerary.objects.none()

        return Itinerary.objects.filter(
            Q(owner=user) | Q(collaborators=user) | Q(is_public=True)
        ).select_related(
            'destination', 'owner'
        ).prefetch_related(
            'daily_plans__activities',
            'bookings__accommodation',
            'bookings__activity',
            Prefetch('collaborations', queryset=Collaboration.objects.select_related('user'))
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ItineraryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ItineraryDetailSerializer
        return ItineraryDetailSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate an existing itinerary for a new trip.
        """
        original = self.get_object()
        with transaction.atomic():
            cloned = Itinerary.objects.create(
                title=f"Copy of {original.title}",
                description=original.description,
                destination=original.destination,
                owner=request.user,
                start_date=original.start_date,
                end_date=original.end_date,
                budget=original.budget,
                status=Itinerary.StatusChoices.PLANNING,
                is_public=False,
            )
            # Duplicate daily plans
            for dp in original.daily_plans.all():
                new_dp = DailyPlan.objects.create(
                    itinerary=cloned,
                    day_number=dp.day_number,
                    date=dp.date,
                    title=dp.title,
                    notes=dp.notes,
                )
                new_dp.activities.set(dp.activities.all())

        serializer = ItineraryDetailSerializer(cloned, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """
        Export itinerary as formatted text/PDF report.
        """
        itinerary = self.get_object()
        content = f"ITINERARY REPORT\n{'='*30}\n"
        content += f"Title: {itinerary.title}\n"
        content += f"Destination: {itinerary.destination.name}, {itinerary.destination.country}\n"
        content += f"Dates: {itinerary.start_date} to {itinerary.end_date} ({itinerary.duration_days} days)\n"
        content += f"Budget: ${itinerary.budget} | Spent: ${itinerary.actual_spent}\n"
        content += f"Status: {itinerary.get_status_display()}\n\n"

        content += f"DAILY PLANS\n{'-'*30}\n"
        for plan in itinerary.daily_plans.all():
            content += f"Day {plan.day_number} ({plan.date}): {plan.title}\n"
            for act in plan.activities.all():
                content += f"  - Activity: {act.name} (${act.price})\n"

        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="itinerary_{itinerary.id}.txt"'
        return response

    @action(detail=True, methods=['post'], url_path='share')
    def share_with_user(self, request, pk=None):
        """
        Share itinerary with another user as a collaborator.
        """
        itinerary = self.get_object()
        username = request.data.get('username')
        role = request.data.get('role', 'viewer')

        if not username:
            return Response({'error': 'username is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'User {username} not found.'}, status=status.HTTP_404_NOT_FOUND)

        if target_user == itinerary.owner:
            return Response({'error': 'Owner cannot be added as collaborator.'}, status=status.HTTP_400_BAD_REQUEST)

        collaboration = itinerary.add_collaborator(target_user, role=role)
        serializer = CollaborationSerializer(collaboration)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming_trips(self, request):
        """
        Get user's upcoming future trips.
        """
        queryset = self.get_queryset().filter(
            start_date__gte=date.today()
        ).order_by('start_date')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ItineraryListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ItineraryListSerializer(queryset, many=True)
        return Response(serializer.data)


# --------------------------------------------------------------------------
# Function-Based Views (FBVs)
# --------------------------------------------------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def trip_search(request):
    """
    FBV Example 1: Trip search with custom filters and ranking.
    GET: Search trips with Q objects and custom ranking.
    POST: Save search preferences.
    """
    if request.method == 'GET':
        query = request.query_params.get('q', '').strip()
        min_budget = request.query_params.get('min_budget')
        max_budget = request.query_params.get('max_budget')
        status_param = request.query_params.get('status')

        qs = Itinerary.objects.filter(
            Q(owner=request.user) | Q(collaborators=request.user) | Q(is_public=True)
        ).select_related('destination', 'owner').distinct()

        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(destination__name__icontains=query) |
                Q(destination__country__icontains=query)
            )

        if min_budget:
            qs = qs.filter(budget__gte=min_budget)
        if max_budget:
            qs = qs.filter(budget__lte=max_budget)
        if status_param:
            qs = qs.filter(status=status_param)

        serializer = ItineraryListSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'results': serializer.data,
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        pref = request.data.get('preference', {})
        request.user.travel_preferences['search_saved'] = pref
        request.user.save(update_fields=['travel_preferences'])
        return Response({
            'message': 'Search preference saved.',
            'travel_preferences': request.user.travel_preferences,
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_trip_report(request, trip_id):
    """
    FBV Example 2: Generate comprehensive trip report with budget, bookings, and itinerary.
    """
    try:
        itinerary = Itinerary.objects.select_related(
            'destination', 'owner', 'budget_detail'
        ).prefetch_related(
            'daily_plans__activities', 'bookings', 'expenses'
        ).get(pk=trip_id)
    except Itinerary.DoesNotExist:
        return Response({'error': 'Itinerary not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Permission check: must be owner, collaborator, or public
    if itinerary.owner != request.user and not itinerary.collaborators.filter(id=request.user.id).exists() and not itinerary.is_public:
        return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    total_bookings_cost = itinerary.bookings.aggregate(Sum('price'))['price__sum'] or 0.00
    total_expenses_cost = itinerary.expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00
    total_spent = float(total_bookings_cost) + float(total_expenses_cost)

    report_data = {
        'trip_id': itinerary.id,
        'title': itinerary.title,
        'destination': f"{itinerary.destination.name}, {itinerary.destination.country}",
        'owner': itinerary.owner.username,
        'start_date': itinerary.start_date,
        'end_date': itinerary.end_date,
        'duration_days': itinerary.duration_days,
        'budget': float(itinerary.budget),
        'total_bookings_cost': float(total_bookings_cost),
        'total_expenses_cost': float(total_expenses_cost),
        'total_spent': total_spent,
        'budget_remaining': float(itinerary.budget) - total_spent,
        'bookings_count': itinerary.bookings.count(),
        'daily_plans_count': itinerary.daily_plans.count(),
    }

    return Response(report_data, status=status.HTTP_200_OK)


# --------------------------------------------------------------------------
# Class-Based Views (CBVs)
# --------------------------------------------------------------------------

class ItineraryListCreateView(generics.ListCreateAPIView):
    """
    CBV Example 2: List user's itineraries or create a new one.
    """
    serializer_class = ItineraryDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Itinerary.objects.filter(
            Q(owner=self.request.user) | Q(collaborators=self.request.user)
        ).select_related('destination', 'owner').prefetch_related('daily_plans', 'collaborators').distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TripCollaborationView(APIView):
    """
    CBV Example 4: Manage trip collaborators (add, update role, remove).
    """
    permission_classes = [IsAuthenticated, IsTripOwner]

    def get_object(self, trip_id):
        try:
            itinerary = Itinerary.objects.get(pk=trip_id)
            self.check_object_permissions(self.request, itinerary)
            return itinerary
        except Itinerary.DoesNotExist:
            return None

    def post(self, request, trip_id):
        """Add collaborator to trip."""
        itinerary = self.get_object(trip_id)
        if not itinerary:
            return Response({'error': 'Itinerary not found or permission denied.'}, status=status.HTTP_404_NOT_FOUND)

        username = request.data.get('username')
        role = request.data.get('role', 'viewer')

        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'User {username} not found.'}, status=status.HTTP_404_NOT_FOUND)

        collaboration = itinerary.add_collaborator(target_user, role=role)
        serializer = CollaborationSerializer(collaboration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, trip_id, user_id=None):
        """Update collaborator permission role."""
        itinerary = self.get_object(trip_id)
        if not itinerary:
            return Response({'error': 'Itinerary not found or permission denied.'}, status=status.HTTP_404_NOT_FOUND)

        target_user_id = user_id or request.data.get('user_id')
        role = request.data.get('role')

        try:
            collaboration = Collaboration.objects.get(itinerary=itinerary, user_id=target_user_id)
        except Collaboration.DoesNotExist:
            return Response({'error': 'Collaboration not found.'}, status=status.HTTP_404_NOT_FOUND)

        if role:
            collaboration.role = role
            collaboration.save()

        serializer = CollaborationSerializer(collaboration)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, trip_id, user_id=None):
        """Remove collaborator from trip."""
        itinerary = self.get_object(trip_id)
        if not itinerary:
            return Response({'error': 'Itinerary not found or permission denied.'}, status=status.HTTP_404_NOT_FOUND)

        target_user_id = user_id or request.data.get('user_id')
        deleted_count, _ = Collaboration.objects.filter(itinerary=itinerary, user_id=target_user_id).delete()

        if deleted_count > 0:
            return Response({'message': 'Collaborator removed successfully.'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Collaborator not found.'}, status=status.HTTP_404_NOT_FOUND)
