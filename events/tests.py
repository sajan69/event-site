from django.test import TestCase, Client, override_settings
from django.urls import reverse
from events.models import Event, EventCategory, EventOrganizer, EventTag
from django.utils import timezone
from datetime import timedelta

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class EventModelTests(TestCase):
    def setUp(self):
        self.category = EventCategory.objects.create(
            name='Conference',
            description='Tech conferences'
        )
        self.organizer = EventOrganizer.objects.create(
            name='Test Organizer',
            email='organizer@test.com',
            phone='1234567890'
        )
        
    def test_event_creation(self):
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            category=self.category,
            organizer=self.organizer,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=2),
            venue_name='Test Venue',
            total_capacity=100,
            address='Test Address',
            city='Test City',
            country='Test Country'
        )
        self.assertEqual(str(event), 'Test Event')
        self.assertTrue(event.slug)

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class EventViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = EventCategory.objects.create(name='Conference')
        self.organizer = EventOrganizer.objects.create(
            name='Test Organizer',
            email='organizer@test.com',
            phone='1234567890'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            category=self.category,
            organizer=self.organizer,
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=2),
            venue_name='Test Venue',
            total_capacity=100,
            address='Test Address',
            city='Test City',
            country='Test Country'
        )