from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from destinations.models import Destination
from itineraries.models import Itinerary
from bookings.models import Accommodation, Activity, Booking

User = get_user_model()


class BookingTests(APITestCase):
    """
    Tests for bookings app models, views, custom permissions, and bulk operations.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='booker', email='booker@example.com', password='Password123!')
        self.other_user = User.objects.create_user(username='otherbooker', email='otherbooker@example.com', password='Password123!')

        self.destination = Destination.objects.create(
            name='Tokyo',
            country='Japan',
            description='Metropolis.',
            category=Destination.CategoryChoices.CITY,
            climate=Destination.ClimateChoices.TEMPERATE,
            best_time_to_visit='Autumn',
            avg_daily_cost=200.00,
        )

        self.itinerary = Itinerary.objects.create(
            title='Tokyo Adventure',
            destination=self.destination,
            owner=self.user,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=12),
            budget=3000.00,
        )

        self.hotel = Accommodation.objects.create(
            name='Shinjuku Prince Hotel',
            destination=self.destination,
            accommodation_type=Accommodation.TypeChoices.HOTEL,
            description='Nice hotel in Shinjuku.',
            price_per_night=120.00,
            address='Shinjuku, Tokyo',
            contact_email='hotel@tokyo.com',
        )

        self.activity = Activity.objects.create(
            name='Mt Fuji Day Tour',
            destination=self.destination,
            category=Activity.CategoryChoices.TOUR,
            description='Tour to Mt Fuji.',
            duration_hours=8.0,
            price=100.00,
        )

        self.booking = Booking.objects.create(
            user=self.user,
            itinerary=self.itinerary,
            accommodation=self.hotel,
            booking_date=date.today(),
            check_in=self.itinerary.start_date,
            check_out=self.itinerary.start_date + timedelta(days=3),
            price=360.00,
            status=Booking.StatusChoices.PENDING,
        )

    def test_booking_model_methods_and_clean(self):
        """Test Booking model methods, clean validation, confirm/cancel logic."""
        self.assertIn('Shinjuku Prince Hotel', str(self.booking))

        # Test confirm booking method
        self.booking.confirm_booking()
        self.assertEqual(self.booking.status, Booking.StatusChoices.CONFIRMED)
        self.assertTrue(self.booking.confirmation_code.startswith('CONF-'))

        # Test cancel booking method
        self.booking.cancel_booking()
        self.assertEqual(self.booking.status, Booking.StatusChoices.CANCELLED)

        # Test invalid clean validation (both acc and act set)
        invalid_booking = Booking(
            user=self.user,
            itinerary=self.itinerary,
            accommodation=self.hotel,
            activity=self.activity,  # Both set!
            booking_date=date.today(),
            price=100,
        )
        with self.assertRaises(ValidationError):
            invalid_booking.clean()

    def test_booking_list_and_create_api(self):
        """Test listing and creating bookings via API."""
        self.client.force_authenticate(user=self.user)

        # List bookings
        list_url = reverse('booking-list')
        res_list = self.client.get(list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data['results']), 1)

        # Create activity booking
        data = {
            'itinerary': self.itinerary.id,
            'activity': self.activity.id,
            'booking_date': str(date.today()),
            'guests_count': 2,
            'price': 200.00,
        }
        res_create = self.client.post(list_url, data)
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.filter(user=self.user).count(), 2)

    def test_booking_confirm_and_cancel_actions(self):
        """Test confirm and cancel custom actions."""
        self.client.force_authenticate(user=self.user)

        confirm_url = reverse('booking-confirm', kwargs={'pk': self.booking.pk})
        res_conf = self.client.post(confirm_url)
        self.assertEqual(res_conf.status_code, status.HTTP_200_OK)
        self.assertEqual(res_conf.data['booking']['status'], 'confirmed')

        cancel_url = reverse('booking-cancel', kwargs={'pk': self.booking.pk})
        res_canc = self.client.post(cancel_url)
        self.assertEqual(res_canc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_canc.data['booking']['status'], 'cancelled')

    def test_booking_detail_cbv(self):
        """Test BookingDetailView CBV (GET, PATCH, DELETE)."""
        self.client.force_authenticate(user=self.user)
        url = reverse('bookings:booking-detail', kwargs={'pk': self.booking.pk})

        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

        res_patch = self.client.patch(url, {'notes': 'Extra pillows requested.'})
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.notes, 'Extra pillows requested.')

    def test_bulk_update_bookings_fbv(self):
        """Test bulk_update_bookings FBV."""
        self.client.force_authenticate(user=self.user)
        url = reverse('bookings:bulk-update')

        data = {
            'booking_ids': [self.booking.id],
            'status': 'confirmed',
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['updated_count'], 1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

    def test_cannot_modify_others_booking(self):
        """Test permission check: cannot modify another user's booking."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('bookings:booking-detail', kwargs={'pk': self.booking.pk})
        res = self.client.patch(url, {'notes': 'Unauthorized edit.'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
