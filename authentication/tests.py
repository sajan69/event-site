from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from authentication.models import OTP, Contact
from django.utils import timezone
from datetime import timedelta

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    TEMPLATE_DIRS=('tests/templates',)
)
class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        self.login_url = reverse('authentication:login')
        self.register_url = reverse('authentication:register')
        
    def test_login_view(self):
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('events:home'))
        
    def test_register_view(self):
        response = self.client.post(self.register_url, {
            'email': 'newuser@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 302)


class OTPTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
    def test_otp_validation(self):
        otp = OTP.objects.create(
            user=self.user,
            otp='123456',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        self.assertTrue(otp.is_valid())
        
        # Test expired OTP
        expired_otp = OTP.objects.create(
            user=self.user,
            otp='654321',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertFalse(expired_otp.is_valid())
