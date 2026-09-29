from django.urls import path
from .views import DestinationSearchView

app_name = 'destinations'

urlpatterns = [
    path('search-advanced/', DestinationSearchView.as_view(), name='destination-search-advanced'),
]
