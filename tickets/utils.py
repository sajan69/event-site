from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.storage import default_storage
from events.models import NewsletterSubscriber, GlobalSettings
from email.mime.image import MIMEImage
import uuid
def send_featured_event_email(event, ticket_types):
    """
    Send email notification about a new featured event with CID images
    """
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    if not subscribers:
        return
    
    site_settings = GlobalSettings.load()
    event_url = f"{settings.SITE_URL}{reverse('events:event_detail', args=[str(event.id)])}"
    
    # Generate Content-ID for event poster
    poster_cid = None
    poster_image = None
    if event.poster and default_storage.exists(event.poster.name):
        try:
            poster_cid = f"poster_{uuid.uuid4().hex}"
            with default_storage.open(event.poster.name, 'rb') as f:
                poster_data = f.read()
            poster_image = MIMEImage(poster_data)
            poster_image.add_header('Content-ID', f'<{poster_cid}>')
            poster_image.add_header('Content-Disposition', 'inline')
        except Exception as e:
            print(f"Error processing event poster: {str(e)}")
    
    for subscriber in subscribers:
        try:
            # Generate unsubscribe token for each subscriber
            unsubscribe_token = subscriber.get_unsubscribe_token()
            
            # Create context with subscriber-specific data
            context = {
                'event': event,
                'ticket_types': ticket_types,
                'event_url': event_url,
                'site_name': site_settings.site_name,
                'year': timezone.now().year,
                'poster_cid': f'cid:{poster_cid}' if poster_cid else None,
                'subscriber': subscriber,
                'unsubscribe_token': unsubscribe_token,
                'site_url': settings.SITE_URL
            }
            
            html_message = render_to_string('tickets/email/featured_event.html', context)
            plain_message = strip_tags(html_message)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=f'New Featured Event: {event.title}',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscriber.email]
            )
            
            # Attach HTML content
            msg.attach_alternative(html_message, "text/html")
            
            # Attach poster image if exists
            if poster_image:
                msg.attach(poster_image)
            
            # Send email
            msg.send()
            
            subscriber.last_sent_at = timezone.now()
            subscriber.save()
        except Exception as e:
            print(f"Failed to send email to {subscriber.email}: {str(e)}")

def send_new_tickets_email(event, new_ticket_types):
    """
    Send email notification about new ticket types with CID images
    """
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    if not subscribers:
        return
    
    site_settings = GlobalSettings.load()
    event_url = f"{settings.SITE_URL}{reverse('events:event_detail', args=[str(event.id)])}"
    
    # Generate Content-ID for event poster
    poster_cid = None
    poster_image = None
    if event.poster and default_storage.exists(event.poster.name):
        try:
            poster_cid = f"poster_{uuid.uuid4().hex}"
            with default_storage.open(event.poster.name, 'rb') as f:
                poster_data = f.read()
            poster_image = MIMEImage(poster_data)
            poster_image.add_header('Content-ID', f'<{poster_cid}>')
            poster_image.add_header('Content-Disposition', 'inline')
        except Exception as e:
            print(f"Error processing event poster: {str(e)}")
    
    for subscriber in subscribers:
        try:
            # Generate unsubscribe token for each subscriber
            unsubscribe_token = subscriber.get_unsubscribe_token()
            
            # Create context with subscriber-specific data
            context = {
                'event': event,
                'new_ticket_types': new_ticket_types,
                'event_url': event_url,
                'site_name': site_settings.site_name,
                'year': timezone.now().year,
                'poster_cid': f'cid:{poster_cid}' if poster_cid else None,
                'subscriber': subscriber,
                'unsubscribe_token': unsubscribe_token,
                'site_url': settings.SITE_URL
            }
            
            html_message = render_to_string('tickets/email/new_tickets.html', context)
            plain_message = strip_tags(html_message)
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=f'New Tickets Available for {event.title}',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscriber.email]
            )
            
            # Attach HTML content
            msg.attach_alternative(html_message, "text/html")
            
            # Attach poster image if exists
            if poster_image:
                msg.attach(poster_image)
            
            # Send email
            msg.send()
            
            subscriber.last_sent_at = timezone.now()
            subscriber.save()
        except Exception as e:
            print(f"Failed to send email to {subscriber.email}: {str(e)}")