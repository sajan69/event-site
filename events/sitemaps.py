from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Event

class EventSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Event.objects.filter(status='published')  # Only include published events

    def location(self, item):
        return reverse('events:event_detail', args=[item.id])  

    def lastmod(self, item):
        return item.updated_at  