from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from destinations.models import Destination
from bookings.models import Activity

User = get_user_model()


class DestinationTests(APITestCase):
    """
    Tests for Destination model, views, filters, and custom actions.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='destuser', email='destuser@example.com', password='Password123!')
        self.destination = Destination.objects.create(
            name='Paris',
            country='France',
            description='City of Lights.',
            category=Destination.CategoryChoices.CULTURAL,
            climate=Destination.ClimateChoices.TEMPERATE,
            best_time_to_visit='Spring',
            avg_daily_cost=180.00,
            latitude=48.8566,
            longitude=2.3522,
        )
        self.activity = Activity.objects.create(
            name='Eiffel Tower Tour',
            destination=self.destination,
            category=Activity.CategoryChoices.TOUR,
            description='Guided tour of Eiffel Tower.',
            duration_hours=2.5,
            price=50.00,
        )

    def test_destination_model_str_and_clean(self):
        """Test Destination __str__ representation and clean validation."""
        self.assertEqual(str(self.destination), 'Paris, France')
        # Test clean method for invalid latitude
        invalid_dest = Destination(
            name='Invalid',
            country='Invalid',
            category='city',
            climate='dry',
            avg_daily_cost=100,
            latitude=100.0,  # Invalid lat > 90
        )
        with self.assertRaises(ValidationError):
            invalid_dest.clean()

    def test_destination_list_api(self):
        """Test retrieving destinations list."""
        url = reverse('destination-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_destination_detail_api(self):
        """Test retrieving destination detail."""
        url = reverse('destination-detail', kwargs={'pk': self.destination.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Paris')
        self.assertIn('summary', response.data)

    def test_destination_popular_activities_action(self):
        """Test popular_activities custom action."""
        url = reverse('destination-popular-activities', kwargs={'pk': self.destination.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['popular_activities']), 1)

    def test_destination_weather_info_action(self):
        """Test weather_info custom action."""
        url = reverse('destination-weather-info', kwargs={'pk': self.destination.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['climate'], 'temperate')

    def test_destination_search_advanced_cbv(self):
        """Test advanced destination search CBV (GET & POST)."""
        url = reverse('destinations:destination-search-advanced')
        # GET search
        get_res = self.client.get(f"{url}?q=Paris&climate=temperate")
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['count'], 1)

        # POST save search preferences
        self.client.force_authenticate(user=self.user)
        post_res = self.client.post(url, {'category': 'cultural', 'climate': 'temperate'}, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.travel_preferences['preferred_category'], 'cultural')
