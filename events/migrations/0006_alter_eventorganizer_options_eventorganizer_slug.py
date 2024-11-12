# Generated by Django 5.1.2 on 2024-11-03 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_alter_event_organizer'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventorganizer',
            options={'verbose_name_plural': 'Event Organizers'},
        ),
        migrations.AddField(
            model_name='eventorganizer',
            name='slug',
            field=models.SlugField(default=1, max_length=120, unique=True),
            preserve_default=False,
        ),
    ]
