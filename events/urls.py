from django.urls import path
from . import views


app_name = 'events'

urlpatterns = [
    path('', views.home, name='home'),
    path('<uuid:event_id>/', views.event_detail, name='event_detail'),
        path('search/', views.search, name='search'),  # Add this line
        path('about/',views.about, name='about'),
    path('contact/', views.contact, name='contact'),
        path('organizer/<int:organizer_id>/', views.organizer_profile, name='organizer_profile'),


]