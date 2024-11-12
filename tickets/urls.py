from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('add_to_cart/<uuid:event_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirm_checkout/', views.confirm_checkout, name='confirm_checkout'),

    path('initiate-payment/', views.initiate_stripe_payment, name='initiate_payment'),
    path('verify-payment/', views.verify_payment, name='payment_verify'),
    path('order-confirmation/<str:token>/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('verify_ticket/', views.verify_ticket, name='verify_ticket'),
    


]