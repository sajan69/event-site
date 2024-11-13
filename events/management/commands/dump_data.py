import json
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from django.apps import apps
from django.db import DatabaseError

class Command(BaseCommand):
    help = 'Dump all data from the database to a JSON file, ignoring errors'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='The output JSON file path')

    def handle(self, *args, **kwargs):
        output_file = kwargs['output_file']
        
        # Prepare a list to hold all serialized data
        data = []

        # Get all models in the project
        all_models = apps.get_models()
        
        # Serialize data from each model
        for model in all_models:
            model_name = model._meta.label_lower  # Use the app name and model name
            try:
                serialized_data = serialize('json', model.objects.all())
                model_data = json.loads(serialized_data)
                data.extend(model_data)  # Add the serialized data to the list
            except (DatabaseError, AttributeError) as e:
                self.stdout.write(self.style.WARNING(f'Error serializing {model_name}: {e}'))
                continue  # Skip this model and continue with the next

        # Write the data to the specified JSON file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.stdout.write(self.style.SUCCESS(f'Successfully dumped all data to {output_file}'))