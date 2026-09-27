"""
travel_api URL Configuration.

All API routes are versioned under /api/v1/. ViewSet routes are registered
on a single DefaultRouter; app-specific function-based and class-based
views live under their own namespaced app urls.py files.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# ViewSets are registered here as each app implements them, e.g.:
# router.register(r'itineraries', ItineraryViewSet, basename='itinerary')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Versioned API root — ViewSet routes
    path('api/v1/', include(router.urls)),

    # App-level routes (function-based + class-based views)
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/destinations/', include('destinations.urls')),
    path('api/v1/itineraries/', include('itineraries.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/reviews/', include('reviews.urls')),
    path('api/v1/budgets/', include('budgets.urls')),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
