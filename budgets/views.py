from django.db.models import Q, Sum, Avg, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Budget, Expense
from .filters import ExpenseFilter
from .serializers import BudgetSerializer, ExpenseSerializer
from itineraries.models import Itinerary


class BudgetViewSet(viewsets.ModelViewSet):
    """
    Manage trip budget allocations per itinerary.
    """

    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Budget.objects.none()
        return Budget.objects.filter(
            Q(itinerary__owner=user) | Q(itinerary__collaborators=user)
        ).select_related('itinerary').distinct()


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    Manage individual recorded trip expenses.
    """

    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExpenseFilter
    search_fields = ['description', 'notes']
    ordering_fields = ['date', 'amount', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Expense.objects.none()
        return Expense.objects.filter(
            Q(itinerary__owner=user) | Q(itinerary__collaborators=user)
        ).select_related('itinerary').distinct()


class TripAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet Example 4: Custom ViewSet for trip analytics and statistics.
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Overall user trip statistics: aggregates, totals, averages.
        """
        user = request.user
        trips = Itinerary.objects.filter(Q(owner=user) | Q(collaborators=user)).distinct()

        total_trips = trips.count()
        completed_trips = trips.filter(status=Itinerary.StatusChoices.COMPLETED).count()

        agg = trips.aggregate(
            total_budget=Sum('budget'),
            avg_budget=Avg('budget'),
            total_spent=Sum('actual_spent'),
        )

        return Response({
            'total_trips': total_trips,
            'completed_trips': completed_trips,
            'total_budget': float(agg['total_budget'] or 0.00),
            'average_trip_budget': float(agg['avg_budget'] or 0.00),
            'total_spent': float(agg['total_spent'] or 0.00),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def budget_summary(self, request):
        """
        Budget analysis across all trips using F expressions and aggregations.
        """
        user = request.user
        trips = Itinerary.objects.filter(Q(owner=user) | Q(collaborators=user)).distinct()

        # Query optimization: F expressions and annotations
        over_budget_trips = trips.filter(actual_spent__gt=F('budget')).values('id', 'title', 'budget', 'actual_spent')

        # Spending by category
        expenses = Expense.objects.filter(itinerary__in=trips)
        category_spending = expenses.values('category').annotate(
            total_amount=Sum('amount'),
            expense_count=Count('id')
        ).order_by('-total_amount')

        return Response({
            'total_expense_records': expenses.count(),
            'category_breakdown': list(category_spending),
            'over_budget_trips_count': len(over_budget_trips),
            'over_budget_trips': list(over_budget_trips),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def destination_preferences(self, request):
        """
        Analyze user's destination preferences based on planned trips.
        """
        user = request.user
        trips = Itinerary.objects.filter(Q(owner=user) | Q(collaborators=user)).distinct()

        top_destinations = trips.values(
            'destination__name', 'destination__country', 'destination__category'
        ).annotate(
            trip_count=Count('id')
        ).order_by('-trip_count')[:5]

        return Response({
            'top_destinations': list(top_destinations),
            'saved_preferences': user.travel_preferences,
        }, status=status.HTTP_200_OK)
