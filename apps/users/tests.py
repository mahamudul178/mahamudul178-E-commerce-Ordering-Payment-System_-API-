from django.test import TestCase

# Create your tests here.
"""
User Management Tests
Location: apps/users/tests.py

Comprehensive test suite for user management functionality.
Tests models, serializers, views, and API endpoints.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


# ============================================
# Model Tests
# ============================================

class UserModelTest(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)
    
    def test_create_user_without_email(self):
        """Test creating user without email raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password='TestPass123!'
            )
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(**self.user_data)
        
        self.assertEqual(admin.email, self.user_data['email'])
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        expected_name = f"{self.user_data['first_name']} {self.user_data['last_name']}"
        self.assertEqual(user.get_full_name(), expected_name)
    
    def test_get_full_name_without_names(self):
        """Test get_full_name returns email when names are empty"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.assertEqual(user.get_full_name(), user.email)
    
    def test_get_short_name(self):
        """Test get_short_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), self.user_data['first_name'])
    
    def test_is_admin_property(self):
        """Test is_admin property"""
        admin = User.objects.create_superuser(**self.user_data)
        self.assertTrue(admin.is_admin)
        
        customer = User.objects.create_user(
            email='customer@example.com',
            password='TestPass123!'
        )
        self.assertFalse(customer.is_admin)
    
    def test_is_customer_property(self):
        """Test is_customer property"""
        customer = User.objects.create_user(**self.user_data)
        self.assertTrue(customer.is_customer)
        
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='TestPass123!'
        )
        self.assertFalse(admin.is_customer)


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            address_line_1='123 Main Street',
            city='Dhaka',
            country='Bangladesh'
        )
    
    def test_profile_creation(self):
        """Test profile is created correctly"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.city, 'Dhaka')
        self.assertEqual(self.profile.country, 'Bangladesh')
    
    def test_profile_str_representation(self):
        """Test profile string representation"""
        expected_str = f"Profile of {self.user.email}"
        self.assertEqual(str(self.profile), expected_str)
    
    def test_get_full_address(self):
        """Test get_full_address method"""
        address = self.profile.get_full_address()
        self.assertIn('123 Main Street', address)
        self.assertIn('Dhaka', address)
        self.assertIn('Bangladesh', address)
    
    def test_get_age(self):
        """Test get_age method"""
        from datetime import date
        
        # Set date of birth to 25 years ago
        self.profile.date_of_birth = date(
            year=date.today().year - 25,
            month=1,
            day=1
        )
        self.profile.save()
        
        age = self.profile.get_age()
        self.assertIsNotNone(age)
        self.assertGreaterEqual(age, 24)
        self.assertLessEqual(age, 26)
    
    def test_get_age_without_dob(self):
        """Test get_age returns None when date_of_birth is not set"""
        self.assertIsNone(self.profile.get_age())


# ============================================
# API Endpoint Tests
# ============================================

class UserRegistrationTest(APITestCase):
    """Test user registration endpoint"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = APIClient()
        self.register_url = reverse('users:register')
        self.valid_data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '01712345678'
        }
    
    def test_register_user_success(self):
        """Test successful user registration"""
        response = self.client.post(
            self.register_url,
            self.valid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(
            response.data['user']['email'],
            self.valid_data['email']
        )
        
        # Verify user is created in database
        user_exists = User.objects.filter(
            email=self.valid_data['email']
        ).exists()
        self.assertTrue(user_exists)
        
        # Verify profile is created
        user = User.objects.get(email=self.valid_data['email'])
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            email=self.valid_data['email'],
            password='password123'
        )
        
        response = self.client.post(
            self.register_url,
            self.valid_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_register_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.valid_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        
        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['password_confirm'] = '123'
        
        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(
            self.register_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_missing_required_fields(self):
        """Test registration with missing required fields"""
        response = self.client.post(
            self.register_url,
            {'email': 'test@example.com'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        
        
"""
Continue adding these test classes to apps/users/tests.py
"""


class UserLoginTest(APITestCase):
    """Test user login endpoint"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.login_url = reverse('users:login')
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(
            self.login_url,
            self.user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        data = self.user_data.copy()
        data['password'] = 'WrongPassword123!'
        
        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'Password123!'
        }
        
        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(
            self.login_url,
            self.user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_case_insensitive_email(self):
        """Test login with case-insensitive email"""
        data = self.user_data.copy()
        data['email'] = self.user_data['email'].upper()
        
        response = self.client.post(
            self.login_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserProfileTest(APITestCase):
    """Test user profile endpoints"""
    
    def setUp(self):
        """Set up test client and authenticated user"""
        self.client = APIClient()
        self.profile_url = reverse('users:profile')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        UserProfile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
    
    def test_get_profile(self):
        """Test getting user profile"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], self.user.email)
        self.assertIn('profile', response.data['user'])
    
    def test_update_profile_basic_info(self):
        """Test updating basic user information"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '01812345678'
        }
        
        response = self.client.patch(
            self.profile_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone, '01812345678')
    
    def test_update_profile_address(self):
        """Test updating profile address"""
        data = {
            'profile': {
                'address_line_1': '456 New Street',
                'city': 'Chittagong',
                'postal_code': '4000',
                'country': 'Bangladesh'
            }
        }
        
        response = self.client.patch(
            self.profile_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.city, 'Chittagong')
    
    def test_profile_unauthorized(self):
        """Test accessing profile without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordTest(APITestCase):
    """Test change password endpoint"""
    
    def setUp(self):
        """Set up test client and authenticated user"""
        self.client = APIClient()
        self.change_password_url = reverse('users:change_password')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='OldPass123!'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_change_password_success(self):
        """Test successful password change"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
    
    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password"""
        data = {
            'old_password': 'WrongOldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_mismatch(self):
        """Test password change with new password mismatch"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'DifferentPass123!'
        }
        
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_same_as_old(self):
        """Test changing password to same as old"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'OldPass123!',
            'new_password_confirm': 'OldPass123!'
        }
        
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_weak_new_password(self):
        """Test changing to weak password"""
        data = {
            'old_password': 'OldPass123!',
            'new_password': '123',
            'new_password_confirm': '123'
        }
        
        response = self.client.post(
            self.change_password_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserListTest(APITestCase):
    """Test user list endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.list_url = reverse('users:user_list')
        
        # Create admin user
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!'
        )
        
        # Create regular user
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='CustomerPass123!'
        )
    
    def test_list_users_as_admin(self):
        """Test listing users as admin"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_list_users_as_customer(self):
        """Test listing users as regular customer"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Customer should only see themselves
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['email'],
            self.customer.email
        )
    
    def test_list_users_unauthorized(self):
        """Test listing users without authentication"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserLogoutTest(APITestCase):
    """Test user logout endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.logout_url = reverse('users:logout')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        
        # Get refresh token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
    
    def test_logout_success(self):
        """Test successful logout"""
        data = {'refresh_token': self.refresh_token}
        response = self.client.post(
            self.logout_url,
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_logout_without_token(self):
        """Test logout without refresh token"""
        response = self.client.post(
            self.logout_url,
            {},
            format='json'
        )
        
        # Should still return 200 (graceful handling)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_logout_unauthorized(self):
        """Test logout without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        