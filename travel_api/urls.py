from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.routers import DefaultRouter

from destinations.views import DestinationViewSet
from itineraries.views import ItineraryViewSet
from bookings.views import BookingViewSet, AccommodationViewSet, ActivityViewSet
from reviews.views import ReviewViewSet
from budgets.views import BudgetViewSet, ExpenseViewSet, TripAnalyticsViewSet

router = DefaultRouter()
router.register(r'itineraries', ItineraryViewSet, basename='itinerary')
router.register(r'destinations', DestinationViewSet, basename='destination')
router.register(r'accommodations', AccommodationViewSet, basename='accommodation')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'analytics', TripAnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Documentation (Swagger & ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # App-Specific Endpoints
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/destinations/', include('destinations.urls')),
    path('api/v1/itineraries/', include('itineraries.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/reviews/', include('reviews.urls')),
    path('api/v1/budgets/', include('budgets.urls')),

    # API v1 Router Endpoints (last, so the specific paths above match first)
    path('api/v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
