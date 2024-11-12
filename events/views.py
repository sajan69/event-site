from django.shortcuts import render
from .models import Event, EventTag, EventCategory, EventOrganizer
from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404

def home(request):
    featured_events = Event.objects.filter(is_featured=True)[:5]
    categories = EventCategory.objects.all()
    featured_organizers = EventOrganizer.objects.annotate(
        event_count=models.Count('organized_events')
    ).order_by('-event_count')[:4]
    upcoming_events = Event.objects.filter(start_datetime__gte=timezone.now()).order_by('start_datetime')[:6]

    context = {
        'featured_events': featured_events,
        'categories': categories,
        'featured_organizers': featured_organizers,
        'upcoming_events': upcoming_events,
    }
    print(context)
    return render(request, 'events/home.html', context)

def event_detail(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'events/event_detail.html', {'event': event})

def organizer_profile(request, organizer_id):
    organizer = get_object_or_404(EventOrganizer, id=organizer_id)
    upcoming_events = organizer.organized_events.filter(start_datetime__gte=timezone.now()).order_by('start_datetime')
    past_events = organizer.organized_events.filter(start_datetime__lt=timezone.now()).order_by('-start_datetime')

    context = {
        'organizer': organizer,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'events/organizer_profile.html', context)

from django.shortcuts import render
from .models import Event, EventCategory
from django.contrib import messages
from django.shortcuts import redirect
from django.core.mail import send_mail
from authentication.models import Contact

from django.utils import timezone
from datetime import timedelta

def search(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', None)
    tag_id = request.GET.get('tag', None)
    date_range = request.GET.get('date_range', None)

    events = Event.objects.all()

    # Filtering by search query
    if query:
        events = events.filter(title__icontains=query)

    # Filtering by category
    if category_id:
        events = events.filter(category_id=category_id)

    # Filtering by tag
    if tag_id:
        events = events.filter(tags__id=tag_id)

    # Filtering by date range
    if date_range:
        now = timezone.now()
        if date_range == 'today':
            events = events.filter(start_datetime__date=now.date())
        elif date_range == 'tomorrow':
            tomorrow = now + timedelta(days=1)
            events = events.filter(start_datetime__date=tomorrow.date())
        elif date_range == 'this_week':
            week_start = now - timedelta(days=now.weekday())  # Start of the week (Monday)
            week_end = week_start + timedelta(days=6)         # End of the week (Sunday)
            events = events.filter(start_datetime__date__range=(week_start.date(), week_end.date()))
        elif date_range == 'this_weekend':
            saturday = now + timedelta(days=(5 - now.weekday()))  # Upcoming Saturday
            sunday = saturday + timedelta(days=1)                 # Upcoming Sunday
            events = events.filter(start_datetime__date__range=(saturday.date(), sunday.date()))
        elif date_range == 'next_week':
            next_week_start = now + timedelta(days=(7 - now.weekday()))
            next_week_end = next_week_start + timedelta(days=6)
            events = events.filter(start_datetime__date__range=(next_week_start.date(), next_week_end.date()))
        elif date_range == 'this_month':
            month_start = now.replace(day=1)  # First day of the current month
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)  # First day of next month
            month_end = next_month - timedelta(days=1)
            events = events.filter(start_datetime__date__range=(month_start.date(), month_end.date()))

    # Fetch categories and tags for filtering options
    categories = EventCategory.objects.all()
    tags = EventTag.objects.all()

    return render(request, 'events/search_results.html', {
        'events': events,
        'categories': categories,
        'tags': tags,
        'query': query,
        'selected_category': category_id,
        'selected_tag': tag_id,
        'selected_date_range': date_range,
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']
        # Send email or save to database
        # send_mail(
        #     subject,
        #     f"Message from {name} ({email}):\n\n{message}",
        #     email,
        #     ['contact@eventmaster.com'],
        #     fail_silently=False,
        # )

        Contact.objects.create(name=name, email=email, subject=subject, message=message)

        messages.success(request, f'Thank you for contacting us, {name}. We will get back to you soon.')
        return redirect('authentication:contact')
    return render(request, 'contact.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)