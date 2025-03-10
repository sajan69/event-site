from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.db import IntegrityError
from events.models import (
    EventCategory, EventOrganizer, EventTag, Event, 
    GlobalSettings, NewsletterSubscriber
)
from tickets.models import TicketType, Ticket, Transaction
from datetime import timedelta
import json
import random
from pathlib import Path
import requests
from urllib.parse import urlparse
import os

User = get_user_model()

class Command(BaseCommand):
    help = '''
    Seed database with sample data. 
    You can choose to load all data or specific data types.
    Use --clear-[type] to clear specific data before seeding.
    '''

    def add_arguments(self, parser):
        # Mode argument
        parser.add_argument(
            '--mode',
            type=str,
            choices=['minimal', 'full'],
            default='minimal',
            help='Mode of operation: minimal or full'
        )

        # Data type arguments
        parser.add_argument(
            '--categories',
            action='store_true',
            help='Load event categories'
        )
        parser.add_argument(
            '--organizers',
            action='store_true',
            help='Load event organizers'
        )
        parser.add_argument(
            '--tags',
            action='store_true',
            help='Load event tags'
        )
        parser.add_argument(
            '--events',
            action='store_true',
            help='Load events'
        )
        parser.add_argument(
            '--tickets',
            action='store_true',
            help='Load ticket types'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Create superuser'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Load all data types'
        )

        # Clear specific data type arguments
        parser.add_argument(
            '--clear-categories',
            action='store_true',
            help='Clear existing categories before seeding'
        )
        parser.add_argument(
            '--clear-organizers',
            action='store_true',
            help='Clear existing organizers before seeding'
        )
        parser.add_argument(
            '--clear-tags',
            action='store_true',
            help='Clear existing tags before seeding'
        )
        parser.add_argument(
            '--clear-events',
            action='store_true',
            help='Clear existing events before seeding'
        )
        parser.add_argument(
            '--clear-tickets',
            action='store_true',
            help='Clear existing ticket types before seeding'
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all existing data before seeding'
        )

    def clear_specific_data(self, model, model_name):
        """Clear data for a specific model"""
        try:
            count = model.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ Cleared {count} {model_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error clearing {model_name}: {str(e)}'))

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seed...')
        
        # Load fixture data
        fixtures_path = Path(__file__).resolve().parent.parent.parent / 'fixtures'
        
        # Check if any specific data type is selected
        specific_types_selected = any([
            kwargs['categories'],
            kwargs['organizers'],
            kwargs['tags'],
            kwargs['events'],
            kwargs['tickets'],
            kwargs['superuser']
        ])

        # If --all is specified or no specific type is selected, load everything
        load_all = kwargs['all'] or not specific_types_selected

        # Handle clearing data
        if kwargs['clear_all']:
            self.clear_data()
        else:
            if kwargs['clear_categories']:
                self.clear_specific_data(EventCategory, 'categories')
            if kwargs['clear_organizers']:
                self.clear_specific_data(EventOrganizer, 'organizers')
            if kwargs['clear_tags']:
                self.clear_specific_data(EventTag, 'tags')
            if kwargs['clear_events']:
                self.clear_specific_data(Event, 'events')
            if kwargs['clear_tickets']:
                self.clear_specific_data(TicketType, 'ticket types')

        try:
            # Create superuser if requested or loading all
            if load_all or kwargs['superuser']:
                self.create_superuser()
                self.stdout.write(self.style.SUCCESS('✓ Created superuser'))

            # Load categories if requested or loading all
            if load_all or kwargs['categories']:
                added, skipped = self.load_categories(fixtures_path / 'categories.json')
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Categories: {added} added, {skipped} skipped (already exist)'
                ))

            # Load organizers if requested or loading all
            if load_all or kwargs['organizers']:
                added, skipped = self.load_organizers(fixtures_path / 'organizers.json')
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Organizers: {added} added, {skipped} skipped (already exist)'
                ))

            # Load tags if requested or loading all
            if load_all or kwargs['tags']:
                added, skipped = self.load_tags(fixtures_path / 'tags.json')
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Tags: {added} added, {skipped} skipped (already exist)'
                ))

            # Load events if requested or loading all
            if load_all or kwargs['events']:
                added, skipped = self.load_events(fixtures_path / 'events.json')
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Events: {added} added, {skipped} skipped (already exist)'
                ))

            # Load ticket types if requested or loading all
            if load_all or kwargs['tickets']:
                added, skipped = self.load_ticket_types(fixtures_path / 'ticket_types.json')
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Ticket Types: {added} added, {skipped} skipped (already exist)'
                ))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'Error: Could not find fixture file - {str(e)}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            return

        self.stdout.write(self.style.SUCCESS('\nDatabase seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data"""
        self.stdout.write('Clearing existing data...')
        models = [Ticket, TicketType, Event, EventTag, EventOrganizer, EventCategory]
        for model in models:
            model.objects.all().delete()

    def create_superuser(self):
        """Create a superuser"""
        if not User.objects.filter(email='admin@example.com').exists():
            User.objects.create_superuser(
                'admin@example.com',
                'admin123',
                first_name='Admin',
                last_name='User'
            )

    def load_categories(self, path):
        """Load event categories"""
        added = skipped = 0
        with open(path) as f:
            categories = json.load(f)
            for category in categories:
                try:
                    EventCategory.objects.create(**category)
                    added += 1
                except IntegrityError:
                    skipped += 1
        return added, skipped

    def download_image_from_url(self, url, model_name):
        """
        Download image from URL and return as ContentFile
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Get the filename from the URL
                filename = os.path.basename(urlparse(url).path)
                if not filename:
                    filename = f"{model_name}_{random.randint(1000, 9999)}.jpg"
                
                # Create ContentFile from the response content
                return ContentFile(response.content, name=filename)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Failed to download image from {url}: {str(e)}'))
        return None

    def load_organizers(self, path):
        """Load event organizers"""
        added = skipped = 0
        with open(path) as f:
            organizers = json.load(f)
            for organizer in organizers:
                try:
                    # Handle profile picture
                    profile_pic_url = organizer.pop('profile_picture', None)
                    
                    # Create organizer without image first
                    org_instance = EventOrganizer.objects.create(**organizer)
                    
                    # Download and save image if URL exists
                    if profile_pic_url:
                        image_content = self.download_image_from_url(profile_pic_url, f'organizer_{org_instance.id}')
                        if image_content:
                            org_instance.profile_picture.save(
                                image_content.name,
                                image_content,
                                save=True
                            )
                    added += 1
                except IntegrityError:
                    skipped += 1
        return added, skipped

    def load_tags(self, path):
        """Load event tags"""
        added = skipped = 0
        with open(path) as f:
            tags = json.load(f)
            for tag in tags:
                try:
                    EventTag.objects.create(**tag)
                    added += 1
                except IntegrityError:
                    skipped += 1
        return added, skipped

    def load_events(self, path):
        """Load events"""
        added = skipped = 0
        with open(path) as f:
            events = json.load(f)
            for event_data in events:
                # Extract relationship fields
                category_name = event_data.pop('category')
                organizer_name = event_data.pop('organizer')
                tags = event_data.pop('tags', [])
                poster_url = event_data.pop('poster', None)
                
                # Get related objects
                category = EventCategory.objects.get(name=category_name)
                organizer = EventOrganizer.objects.get(name=organizer_name)
                
                # Create event without image first
                event = Event.objects.create(
                    category=category,
                    organizer=organizer,
                    **event_data
                )
                
                # Download and save poster if URL exists
                if poster_url:
                    image_content = self.download_image_from_url(poster_url, f'event_{event.id}')
                    if image_content:
                        event.poster.save(
                            image_content.name,
                            image_content,
                            save=True
                        )
                
                # Add tags
                for tag_name in tags:
                    tag = EventTag.objects.get(name=tag_name)
                    event.tags.add(tag)
                added += 1
        return added, skipped

    def load_ticket_types(self, path):
        """Load ticket types"""
        added = skipped = 0
        with open(path) as f:
            ticket_types = json.load(f)
            for ticket_data in ticket_types:
                event_title = ticket_data.pop('event')
                event = Event.objects.get(title=event_title)
                try:
                    TicketType.objects.create(event=event, **ticket_data)
                    added += 1
                except IntegrityError:
                    skipped += 1
        return added, skipped 