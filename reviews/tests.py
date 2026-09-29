from datetime import date
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from destinations.models import Destination
from reviews.models import Review

User = get_user_model()


class ReviewTests(APITestCase):
    """
    Tests for reviews app models, validation, views, permissions, and helpful action.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='reviewer', email='reviewer@example.com', password='Password123!')
        self.other_user = User.objects.create_user(username='otherreviewer', email='otherreviewer@example.com', password='Password123!')

        self.destination = Destination.objects.create(
            name='Kyoto',
            country='Japan',
            description='Historic temples.',
            category=Destination.CategoryChoices.CULTURAL,
            climate=Destination.ClimateChoices.TEMPERATE,
            best_time_to_visit='Spring',
            avg_daily_cost=160.00,
        )

        self.review = Review.objects.create(
            user=self.user,
            destination=self.destination,
            rating=5,
            title='Amazing Experience',
            content='Kyoto is absolutely beautiful in cherry blossom season.',
            visit_date=date.today(),
        )

    def test_review_model_str_and_clean(self):
        """Test Review __str__ and clean validation."""
        self.assertIn('Amazing Experience by reviewer', str(self.review))

        # Invalid review with no targets specified
        invalid_review = Review(
            user=self.user,
            rating=4,
            title='No Target',
            content='Invalid review content.',
            visit_date=date.today(),
        )
        with self.assertRaises(ValidationError):
            invalid_review.clean()

    def test_review_list_and_create_api(self):
        """Test review list and create endpoints."""
        self.client.force_authenticate(user=self.user)

        list_url = reverse('review-list')
        res_list = self.client.get(list_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data['results']), 1)

        # Create review
        data = {
            'destination': self.destination.id,
            'rating': 4,
            'title': 'Great trip',
            'content': 'Had a wonderful time exploring temples.',
            'visit_date': str(date.today()),
        }
        res_create = self.client.post(list_url, data)
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 2)

    def test_review_helpful_action(self):
        """Test marking review as helpful."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('review-helpful', kwargs={'pk': self.review.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.helpful_count, 1)

    def test_cannot_edit_others_review(self):
        """Test read-only permission for non-owner."""
        self.client.force_authenticate(user=self.other_user)
        detail_url = reverse('review-detail', kwargs={'pk': self.review.pk})

        # GET should succeed (read-only)
        get_res = self.client.get(detail_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)

        # PATCH should fail (forbidden)
        patch_res = self.client.patch(detail_url, {'title': 'Hacked Title'})
        self.assertEqual(patch_res.status_code, status.HTTP_403_FORBIDDEN)
