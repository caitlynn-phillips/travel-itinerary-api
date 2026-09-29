from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory
from itineraries.permissions import (
    IsTripOwner, IsTripOwnerOrCollaborator, CanEditItinerary
)

from destinations.models import Destination
from itineraries.models import Itinerary, DailyPlan, Collaboration
from budgets.models import Budget

User = get_user_model()


class ItineraryTests(APITestCase):
    """
    Comprehensive tests for itineraries app: models, views (ViewSet, CBV, FBV), permissions, custom actions.
    """

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username='owner', email='owner@example.com', password='Password123!')
        self.collaborator = User.objects.create_user(username='collab', email='collab@example.com', password='Password123!')
        self.viewer = User.objects.create_user(username='viewer', email='viewer@example.com', password='Password123!')

        self.destination = Destination.objects.create(
            name='Rome',
            country='Italy',
            description='Eternal city.',
            category=Destination.CategoryChoices.CULTURAL,
            climate=Destination.ClimateChoices.TEMPERATE,
            best_time_to_visit='Spring',
            avg_daily_cost=150.00,
        )

        self.itinerary = Itinerary.objects.create(
            title='Rome Adventure',
            description='Visiting historical sites.',
            destination=self.destination,
            owner=self.owner,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=17),
            budget=2000.00,
            actual_spent=500.00,
            status=Itinerary.StatusChoices.PLANNING,
            is_public=False,
        )

        self.daily_plan = DailyPlan.objects.create(
            itinerary=self.itinerary,
            day_number=1,
            date=self.itinerary.start_date,
            title='Colosseum Tour',
            notes='Wear comfortable shoes.',
        )

    def test_itinerary_model_methods_and_clean(self):
        """Test Itinerary model properties, methods, and clean validation."""
        self.assertEqual(str(self.itinerary), 'Rome Adventure - Rome')
        self.assertEqual(self.itinerary.duration_days, 8)
        self.assertEqual(self.itinerary.budget_remaining, 1500.00)

        # Test invalid date order clean validation
        bad_itinerary = Itinerary(
            title='Bad Dates',
            destination=self.destination,
            owner=self.owner,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=5),
            budget=1000,
        )
        with self.assertRaises(ValidationError):
            bad_itinerary.clean()

    def test_itinerary_add_collaborator(self):
        """Test add_collaborator method."""
        collab_obj = self.itinerary.add_collaborator(self.collaborator, role='editor')
        self.assertEqual(collab_obj.role, 'editor')
        self.assertTrue(self.itinerary.collaborators.filter(id=self.collaborator.id).exists())

    def test_list_and_retrieve_itineraries_viewset(self):
        """Test retrieving list and detail itineraries."""
        self.client.force_authenticate(user=self.owner)

        list_url = reverse('itinerary-list')
        res_list = self.client.get(list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data['results']), 1)

        detail_url = reverse('itinerary-detail', kwargs={'pk': self.itinerary.pk})
        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['title'], 'Rome Adventure')

    def test_create_itinerary_auto_creates_budget(self):
        """Test creating an itinerary automatically initializes a Budget object."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itinerary-list')
        data = {
            'title': 'Venice Trip',
            'destination_id': self.destination.id,
            'start_date': str(date.today() + timedelta(days=30)),
            'end_date': str(date.today() + timedelta(days=35)),
            'budget': 1500.00,
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        new_id = res.data['id']
        self.assertTrue(Budget.objects.filter(itinerary_id=new_id).exists())

    def test_duplicate_itinerary_action(self):
        """Test duplicate custom action on itinerary viewset."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itinerary-duplicate', kwargs={'pk': self.itinerary.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Itinerary.objects.filter(owner=self.owner).count(), 2)

    def test_export_pdf_action(self):
        """Test export_pdf custom action."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itinerary-export-pdf', kwargs={'pk': self.itinerary.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(b"Rome Adventure", res.content)

    def test_share_with_user_action(self):
        """Test share_with_user action."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itinerary-share-with-user', kwargs={'pk': self.itinerary.pk})
        res = self.client.post(url, {'username': self.collaborator.username, 'role': 'editor'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(Collaboration.objects.filter(itinerary=self.itinerary, user=self.collaborator).exists())

    def test_upcoming_trips_action(self):
        """Test upcoming_trips action."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itinerary-upcoming-trips')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_trip_search_fbv(self):
        """Test trip_search FBV GET and POST."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itineraries:trip-search')

        get_res = self.client.get(f"{url}?q=Rome&min_budget=1000")
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data['count'], 1)

        post_res = self.client.post(url, {'preference': {'target': 'Europe'}}, format='json')
        self.assertEqual(post_res.status_code, status.HTTP_200_OK)

    def test_generate_trip_report_fbv(self):
        """Test generate_trip_report FBV."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itineraries:trip-report', kwargs={'trip_id': self.itinerary.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], 'Rome Adventure')

    def test_itinerary_list_create_cbv(self):
        """Test ItineraryListCreateView CBV."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itineraries:itinerary-create')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_trip_collaboration_cbv(self):
        """Test TripCollaborationView CBV (POST, PATCH, DELETE)."""
        self.client.force_authenticate(user=self.owner)
        url = reverse('itineraries:trip-collaborators', kwargs={'trip_id': self.itinerary.pk})

        # POST add
        post_res = self.client.post(url, {'username': self.collaborator.username, 'role': 'viewer'})
        self.assertEqual(post_res.status_code, status.HTTP_201_CREATED)

        # PATCH update role
        patch_res = self.client.patch(url, {'user_id': self.collaborator.id, 'role': 'editor'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(Collaboration.objects.get(itinerary=self.itinerary, user=self.collaborator).role, 'editor')

        # DELETE remove
        del_url = reverse('itineraries:trip-collaborators-detail', kwargs={'trip_id': self.itinerary.pk, 'user_id': self.collaborator.id})
        del_res = self.client.delete(del_url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

    def test_permissions_unauthorized_access(self):
        """Test unauthorized user cannot modify itinerary."""
        self.client.force_authenticate(user=self.viewer)
        detail_url = reverse('itinerary-detail', kwargs={'pk': self.itinerary.pk})
        res = self.client.patch(detail_url, {'title': 'Hacked Title'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class ItineraryPermissionTests(APITestCase):
    """
    Direct tests for the custom itinerary permission classes.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(username='powner', email='powner@example.com', password='Password123!')
        self.editor = User.objects.create_user(username='peditor', email='peditor@example.com', password='Password123!')
        self.viewer = User.objects.create_user(username='pviewer', email='pviewer@example.com', password='Password123!')
        self.stranger = User.objects.create_user(username='pstranger', email='pstranger@example.com', password='Password123!')

        destination = Destination.objects.create(
            name='Lisbon',
            country='Portugal',
            description='Hilly coastal capital.',
            category=Destination.CategoryChoices.CITY,
            climate=Destination.ClimateChoices.TEMPERATE,
            best_time_to_visit='Autumn',
            avg_daily_cost=120.00,
        )
        self.itinerary = Itinerary.objects.create(
            title='Lisbon Trip',
            destination=destination,
            owner=self.owner,
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=9),
            budget=1500.00,
        )
        Collaboration.objects.create(itinerary=self.itinerary, user=self.editor, role='editor')
        Collaboration.objects.create(itinerary=self.itinerary, user=self.viewer, role='viewer')

    def _request(self, method, user):
        """Build a request of the given HTTP method with the given user attached."""
        request = getattr(self.factory, method)('/')
        request.user = user
        return request

    def test_is_trip_owner(self):
        """Only the owner passes IsTripOwner."""
        perm = IsTripOwner()
        self.assertTrue(perm.has_object_permission(self._request('patch', self.owner), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('patch', self.editor), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('get', AnonymousUser()), None, self.itinerary))

    def test_owner_or_collaborator_read_and_write(self):
        """Collaborators can read but not write; strangers and anonymous users cannot do either."""
        perm = IsTripOwnerOrCollaborator()
        self.assertTrue(perm.has_object_permission(self._request('get', self.editor), None, self.itinerary))
        self.assertTrue(perm.has_object_permission(self._request('get', self.viewer), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('get', self.stranger), None, self.itinerary))
        self.assertTrue(perm.has_object_permission(self._request('patch', self.owner), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('patch', self.editor), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('get', AnonymousUser()), None, self.itinerary))

    def test_can_edit_itinerary_by_role(self):
        """Editors can write, viewers can only read, strangers and anonymous users are blocked."""
        perm = CanEditItinerary()
        self.assertTrue(perm.has_object_permission(self._request('patch', self.owner), None, self.itinerary))
        self.assertTrue(perm.has_object_permission(self._request('patch', self.editor), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('patch', self.viewer), None, self.itinerary))
        self.assertTrue(perm.has_object_permission(self._request('get', self.viewer), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('get', self.stranger), None, self.itinerary))
        self.assertFalse(perm.has_object_permission(self._request('patch', AnonymousUser()), None, self.itinerary))
