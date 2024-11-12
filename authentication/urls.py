# urls.py
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('change-password/', views.change_password, name='change_password'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    
]