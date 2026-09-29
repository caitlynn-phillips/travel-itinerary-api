from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from destinations.models import Destination
from itineraries.models import Itinerary
from budgets.models import Budget, Expense

User = get_user_model()


class BudgetAndAnalyticsTests(APITestCase):
    """
    Tests for budgets app: models, expense tracking, budget management, and trip analytics ViewSet.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='budgetuser', email='budgetuser@example.com', password='Password123!')

        self.destination = Destination.objects.create(
            name='Barcelona',
            country='Spain',
            description='Catalan capital.',
            category=Destination.CategoryChoices.CULTURAL,
            climate=Destination.ClimateChoices.TEMPERATE,
            best_time_to_visit='Summer',
            avg_daily_cost=140.00,
        )

        self.itinerary = Itinerary.objects.create(
            title='Barcelona Break',
            destination=self.destination,
            owner=self.user,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            budget=1500.00,
            actual_spent=600.00,
            status=Itinerary.StatusChoices.IN_PROGRESS,
        )

        # Budget object auto-created by ItineraryDetailSerializer/model or create here
        self.budget, _ = Budget.objects.get_or_create(
            itinerary=self.itinerary,
            defaults={
                'accommodation_budget': 600.00,
                'activities_budget': 300.00,
                'food_budget': 400.00,
                'transport_budget': 100.00,
                'miscellaneous_budget': 100.00,
            }
        )

        self.expense = Expense.objects.create(
            itinerary=self.itinerary,
            category=Expense.CategoryChoices.FOOD,
            description='Tapas Dinner',
            amount=75.50,
            date=date.today(),
        )

    def test_budget_and_expense_models(self):
        """Test Budget and Expense model properties, methods, and clean validation."""
        self.assertEqual(str(self.budget), f"Budget for Barcelona Break")
        self.assertEqual(self.budget.total_budget, 1500.00)

        self.assertIn('Tapas Dinner - $75.5', str(self.expense))

        invalid_expense = Expense(
            itinerary=self.itinerary,
            category='food',
            description='Negative',
            amount=-50.00,  # Invalid amount < 0
            date=date.today(),
        )
        with self.assertRaises(ValidationError):
            invalid_expense.clean()

    def test_budget_api_list_and_detail(self):
        """Test Budget ViewSet list and detail endpoints."""
        self.client.force_authenticate(user=self.user)
        url = reverse('budget-list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['results']), 1)

    def test_expense_api_list_and_create(self):
        """Test Expense ViewSet list and create endpoints."""
        self.client.force_authenticate(user=self.user)
        list_url = reverse('expense-list')

        get_res = self.client.get(list_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_res.data['results']), 1)

        post_data = {
            'itinerary': self.itinerary.id,
            'category': 'transport',
            'description': 'Metro Card',
            'amount': 25.00,
            'date': str(date.today()),
        }
        post_res = self.client.post(list_url, post_data)
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 2)

    def test_trip_analytics_viewset(self):
        """Test custom TripAnalyticsViewSet (list, budget_summary, destination_preferences)."""
        self.client.force_authenticate(user=self.user)

        # List overview stats
        list_url = reverse('analytics-list')
        res_list = self.client.get(list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(res_list.data['total_trips'], 1)

        # Budget summary action
        summary_url = reverse('analytics-budget-summary')
        res_summary = self.client.get(summary_url)
        self.assertEqual(res_summary.status_code, status.HTTP_200_OK)
        self.assertIn('category_breakdown', res_summary.data)

        # Destination preferences action
        pref_url = reverse('analytics-destination-preferences')
        res_pref = self.client.get(pref_url)
        self.assertEqual(res_pref.status_code, status.HTTP_200_OK)
        self.assertIn('top_destinations', res_pref.data)
