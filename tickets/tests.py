from django.test import TestCase, Client, override_settings
from django.urls import reverse
from tickets.models import TicketType, Ticket, Transaction
from events.models import Event, EventCategory, EventOrganizer
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class TicketModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
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
            end_datetime=timezone.now() + timezone.timedelta(hours=2),
            venue_name='Test Venue',
            total_capacity=100,
            address='Test Address',
            city='Test City',
            country='Test Country'
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name='standard',
            price=Decimal('10.00'),
            total_quantity=50,
            available_quantity=50
        )

@override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)
class TicketViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create event and ticket type
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
            end_datetime=timezone.now() + timezone.timedelta(hours=2),
            venue_name='Test Venue',
            total_capacity=100,
            address='Test Address',
            city='Test City',
            country='Test Country'
        )
        self.ticket_type = TicketType.objects.create(
            event=self.event,
            name='standard',
            price=Decimal('10.00'),
            total_quantity=50,
            available_quantity=50
        )