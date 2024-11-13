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
        
class EventTag(models.Model):
    """
    Tags for events to provide additional categorization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
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

    # Event Tag
    tags = models.ManyToManyField(
        EventTag, 
        related_name='events', 
        blank=True
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
        Automatically generate slug if not provided and handle featured event notifications
        """
        is_new = self.pk is None
        was_featured = False
        
        if not is_new:
            old_instance = Event.objects.get(pk=self.pk)
            was_featured = old_instance.is_featured
        
        # Generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Ensure start datetime is before end datetime
        if self.start_datetime and self.end_datetime:
            if self.start_datetime > self.end_datetime:
                self.start_datetime, self.end_datetime = self.end_datetime, self.start_datetime
        
        super().save(*args, **kwargs)
        
        # Send email if event becomes featured
        if self.is_featured and not was_featured:
            from tickets.utils import send_featured_event_email
            ticket_types = self.ticket_types.all()
            send_featured_event_email(self, ticket_types)


    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['start_datetime', 'status']),
            models.Index(fields=['slug'])
        ]

class GlobalSettings(models.Model):
    """
    Global settings for the website including site information and social media links
    """
    # Site Information
    site_name = models.CharField(max_length=100, default="EventMaster")
    site_logo = models.ImageField(upload_to='site/', null=True, blank=True)
    
    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Contact Information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Global Settings"
        verbose_name_plural = "Global Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and GlobalSettings.objects.exists():
            return
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

from django.core.signing import Signer

class NewsletterSubscriber(models.Model):
    """
    Model to store newsletter subscribers
    """
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    def get_unsubscribe_token(self):
        """Generate a secure token for unsubscribe link"""
        signer = Signer()
        return signer.sign(self.email)

    def verify_unsubscribe_token(self, token):
        """Verify the unsubscribe token"""
        signer = Signer()
        try:
            email = signer.unsign(token)
            return email == self.email
        except:
            return False

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
        ordering = ['-subscribed_at']