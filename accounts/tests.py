from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

User = get_user_model()


class UserAccountTests(APITestCase):
    """
    Unit and integration tests for accounts app: authentication, registration, profiles, and password management.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe',
        )

    def test_user_model_str_and_full_name(self):
        """Test User string representation and full_name property."""
        self.assertEqual(str(self.user), 'testuser')
        self.assertEqual(self.user.full_name, 'John Doe')

    def test_user_registration_success(self):
        """Test user registration endpoint."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)

    def test_user_registration_password_mismatch(self):
        """Test registration fails when passwords do not match."""
        url = reverse('accounts:register')
        data = {
            'username': 'baduser',
            'email': 'baduser@example.com',
            'password': 'Password123!',
            'password2': 'Mismatch123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """Test login with valid credentials."""
        url = reverse('accounts:login')
        data = {
            'username': 'testuser',
            'password': 'TestPassword123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

    def test_user_login_invalid_credentials(self):
        """Test login fails with invalid password."""
        url = reverse('accounts:login')
        data = {
            'username': 'testuser',
            'password': 'WrongPassword',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_and_update_profile(self):
        """Test authenticated user profile retrieval and update."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:profile')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

        # Update bio and travel preferences
        update_data = {
            'bio': 'Avid world traveler.',
            'travel_preferences': {'climate': 'tropical', 'budget': 'moderate'},
        }
        patch_res = self.client.patch(url, update_data, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Avid world traveler.')
        self.assertEqual(self.user.travel_preferences['climate'], 'tropical')

    def test_password_change(self):
        """Test password change endpoint."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:password-change')
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'UpdatedPassword123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password('UpdatedPassword123!'))

    def test_password_reset_flow(self):
        """Test password reset request and confirmation flow."""
        request_url = reverse('accounts:password-reset')
        req_res = self.client.post(request_url, {'email': 'testuser@example.com'})
        self.assertEqual(req_res.status_code, status.HTTP_200_OK)
        self.assertIn('uid', req_res.data)
        self.assertIn('token', req_res.data)

        confirm_url = reverse('accounts:password-reset-confirm')
        confirm_data = {
            'uid': req_res.data['uid'],
            'token': req_res.data['token'],
            'new_password': 'ResetPass123!',
        }
        conf_res = self.client.post(confirm_url, confirm_data)
        self.assertEqual(conf_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ResetPass123!'))
