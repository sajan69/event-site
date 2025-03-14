# Generated by Django 5.1.2 on 2024-11-01 16:07

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EventCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(max_length=120, unique=True)),
            ],
            options={
                'verbose_name_plural': 'Event Categories',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=220, unique=True)),
                ('description', models.TextField()),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('venue_name', models.CharField(max_length=300)),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('poster', models.ImageField(blank=True, null=True, upload_to='event_posters/')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('cancelled', 'Cancelled'), ('completed', 'Completed')], default='draft', max_length=20)),
                ('is_free', models.BooleanField(default=False)),
                ('total_capacity', models.PositiveIntegerField(help_text='Total number of tickets available', validators=[django.core.validators.MinValueValidator(1)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organizer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organized_events', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='events.eventcategory')),
            ],
            options={
                'ordering': ['-start_datetime'],
            },
        ),
        migrations.CreateModel(
            name='EventTag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('events', models.ManyToManyField(blank=True, related_name='tags', to='events.event')),
            ],
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['start_datetime', 'status'], name='events_even_start_d_750395_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['slug'], name='events_even_slug_30eb0f_idx'),
        ),
    ]
