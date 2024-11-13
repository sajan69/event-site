from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Load data and disable foreign key checks temporarily'

    def handle(self, *args, **kwargs):
        # Disable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF;")
            self.stdout.write(self.style.WARNING('Foreign key checks disabled.'))

        # Load your data
        try:
            call_command('loaddata', 'output.json')  # Replace with your JSON file
            self.stdout.write(self.style.SUCCESS('Data loaded successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading data: {e}'))

        # Re-enable foreign key checks
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = ON;")
            self.stdout.write(self.style.SUCCESS('Foreign key checks re-enabled.'))