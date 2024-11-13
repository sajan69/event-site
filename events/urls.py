from django.urls import path
from . import views
from .sitemaps import EventSitemap
from django.contrib.sitemaps.views import sitemap


app_name = 'events'

sitemaps = {
    'events': EventSitemap,
}
urlpatterns = [
    path('', views.home, name='home'),
    path('<uuid:event_id>/', views.event_detail, name='event_detail'),
        path('search/', views.search, name='search'),  # Add this line
        path('about/',views.about, name='about'),
    path('contact/', views.contact, name='contact'),
        path('organizer/<uuid:organizer_id>/', views.organizer_profile, name='organizer_profile'),
    path('search/autocomplete/', views.event_search_autocomplete, name='event_search_autocomplete'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django_sitemap'),
        path('robots.txt', views.robots_txt, name='robots_txt'),
        path('newsletter/subscribe/', views.subscribe_newsletter, name='newsletter_subscribe'),
          path('newsletter/unsubscribe/<str:email>/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),


]