from django.urls import path
from .views import (
    trip_search,
    generate_trip_report,
    ItineraryListCreateView,
    TripCollaborationView,
)

app_name = 'itineraries'

urlpatterns = [
    path('search/', trip_search, name='trip-search'),
    path('<int:trip_id>/report/', generate_trip_report, name='trip-report'),
    path('create/', ItineraryListCreateView.as_view(), name='itinerary-create'),
    path('<int:trip_id>/collaborators/', TripCollaborationView.as_view(), name='trip-collaborators'),
    path('<int:trip_id>/collaborators/<int:user_id>/', TripCollaborationView.as_view(), name='trip-collaborators-detail'),
]
