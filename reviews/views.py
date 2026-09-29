from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Review
from .filters import ReviewFilter
from .permissions import IsReviewOwnerOrReadOnly
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    CRUD for destination, accommodation, and activity reviews.
    """

    queryset = Review.objects.select_related('user', 'destination', 'accommodation', 'activity').all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReviewFilter
    search_fields = ['title', 'content', 'destination__name', 'accommodation__name', 'activity__name']
    ordering_fields = ['rating', 'created_at', 'helpful_count']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def helpful(self, request, pk=None):
        """
        Increment helpful upvote count for a review.
        """
        review = self.get_object()
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        return Response({
            'message': 'Marked as helpful.',
            'helpful_count': review.helpful_count,
        }, status=status.HTTP_200_OK)
