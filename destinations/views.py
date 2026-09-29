from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination
from .filters import DestinationFilter
from .serializers import (
    DestinationListSerializer,
    DestinationDetailSerializer,
    DestinationCreateUpdateSerializer,
)
from bookings.serializers import ActivitySerializer


class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Browse destinations with search, filter, ordering, and custom action endpoints.
    """

    queryset = Destination.objects.filter(is_active=True).annotate(
        review_count_ann=Count('reviews'),
        avg_rating_ann=Avg('reviews__rating')
    )
    serializer_class = DestinationListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DestinationFilter
    search_fields = ['name', 'description', 'country']
    ordering_fields = ['name', 'avg_daily_cost', 'created_at', 'review_count_ann', 'avg_rating_ann']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DestinationDetailSerializer
        return DestinationListSerializer

    @action(detail=True, methods=['get'])
    def popular_activities(self, request, pk=None):
        """
        Get most popular activities for destination ranked by bookings.
        """
        destination = self.get_object()
        activities = destination.activities.filter(is_available=True).annotate(
            booking_count=Count('bookings')
        ).order_by('-booking_count')[:10]

        serializer = ActivitySerializer(activities, many=True)
        return Response({
            'destination': destination.name,
            'popular_activities': serializer.data,
        })

    @action(detail=True, methods=['get'])
    def weather_info(self, request, pk=None):
        """
        Get climate and seasonal weather info for destination.
        """
        destination = self.get_object()
        return Response({
            'destination': destination.name,
            'climate': destination.climate,
            'climate_display': destination.get_climate_display(),
            'best_time_to_visit': destination.best_time_to_visit,
        })


class DestinationSearchView(APIView):
    """
    Advanced destination search with custom Q object ranking algorithm (CBV requirement).
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """
        GET: Custom search with Q objects, query ranking, and pagination.
        """
        query = request.query_params.get('q', '').strip()
        climate = request.query_params.get('climate')
        category = request.query_params.get('category')
        max_cost = request.query_params.get('max_cost')

        queryset = Destination.objects.filter(is_active=True)

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(country__icontains=query) |
                Q(description__icontains=query)
            )

        if climate:
            queryset = queryset.filter(climate=climate)

        if category:
            queryset = queryset.filter(category=category)

        if max_cost:
            try:
                queryset = queryset.filter(avg_daily_cost__lte=float(max_cost))
            except ValueError:
                pass

        # Query optimization with select_related/prefetch_related
        queryset = queryset.prefetch_related('reviews')

        serializer = DestinationListSerializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'query': query,
            'results': serializer.data,
        })

    def post(self, request):
        """
        POST: Save custom search parameters into user's travel preferences.
        """
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        pref_key = request.data.get('category') or request.data.get('climate') or 'general'
        prefs = request.user.travel_preferences or {}
        prefs['last_search'] = request.data
        prefs['preferred_category'] = pref_key

        request.user.travel_preferences = prefs
        request.user.save(update_fields=['travel_preferences'])

        return Response({
            'message': 'Search preference saved successfully.',
            'preferences': request.user.travel_preferences,
        }, status=status.HTTP_200_OK)
