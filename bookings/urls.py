from django.urls import path
from .views import BookingDetailView, bulk_update_bookings

app_name = 'bookings'

urlpatterns = [
    path('bulk-update/', bulk_update_bookings, name='bulk-update'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
]
