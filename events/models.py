from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.conf import settings
import uuid

class EventCategory(models.Model):
    """
    Categories for events to help with organization and filtering
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    icon = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=120)

    def save(self, *args, **kwargs):
        """
        Automatically generate slug if not provided
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Event Categories"


class EventOrganizer(models.Model):
    """
    Organizer of the event
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='organizer_profiles/', null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    slug = models.SlugField(unique=True, max_length=120)


    def save(self, *args, **kwargs):
        """
        Automatically generate slug if not provided
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

    @property
    def events_count(self):
        return self.organized_events.count()
    
    class Meta:
        verbose_name_plural = "Event Organizers"
        

class Event(models.Model):
    """
    Comprehensive Event Model
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Event Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    description = models.TextField()
    
    # Event Categorization
    category = models.ForeignKey(
        EventCategory, 
        on_delete=models.SET_NULL, 
        related_name='events', 
        null=True
    )
    
    # Event Timing
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    # Location Details
    venue_name = models.CharField(max_length=300)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    # Event Metadata
    poster = models.ImageField(
        upload_to='event_posters/', 
        null=True, 
        blank=True
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    
    # Organizer Information
    organizer = models.ForeignKey(
       EventOrganizer, 
        on_delete=models.CASCADE, 
        related_name='organized_events'
    )
    
    # Pricing and Capacity
    is_free = models.BooleanField(default=False)
    total_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total number of tickets available"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Featured
    is_featured = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        """
        Automatically generate slug if not provided
        """
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Ensure start datetime is before end datetime
        if self.start_datetime and self.end_datetime:
            if self.start_datetime > self.end_datetime:
                self.start_datetime, self.end_datetime = self.end_datetime, self.start_datetime
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['start_datetime', 'status']),
            models.Index(fields=['slug'])
        ]

class EventTag(models.Model):
    """
    Tags for events to provide additional categorization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    events = models.ManyToManyField(Event, related_name='tags', blank=True)

    def __str__(self):
        return self.name