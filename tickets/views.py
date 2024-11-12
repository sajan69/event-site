import base64
from django.conf import settings
from django.shortcuts import render, redirect
import requests
from .models import TicketType, Ticket, Transaction
from django.contrib import messages
from django.http import JsonResponse
import json


def add_to_cart(request, event_id):
    if request.method == 'POST':
        ticket_type_id = request.POST.get('ticket_type_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Initialize cart in session if it doesn't exist
        if 'cart' not in request.session:
            request.session['cart'] = []
        
        # Add ticket to cart
        cart_item = {
            'ticket_type_id': ticket_type_id,
            'quantity': quantity
        }
        request.session['cart'].append(cart_item)
        request.session.modified = True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'cart_count': len(request.session['cart'])
            })
        return redirect('tickets:checkout')
    
    return redirect('events:detail', event_id=event_id)

def checkout(request):
    cart = request.session.get('cart', [])
    cart_tickets = []
    total_price = 0
    
    for item in cart:
        ticket_type = TicketType.objects.get(id=item['ticket_type_id'])
        quantity = item['quantity']
        subtotal = ticket_type.price * quantity
        total_price += subtotal
        
        cart_tickets.append({
            'ticket_type': ticket_type,
            'quantity': quantity,
            'subtotal': subtotal
        })
    
    return render(request, 'tickets/checkout.html', {
        'cart_tickets': cart_tickets,
        'total_price': total_price
    })

def confirm_checkout(request):
    if request.method == 'POST':
        cart_tickets = request.POST.getlist('cart_tickets')  # Assuming cart_tickets is passed as a list
        for ticket_info in cart_tickets:
            ticket_type_id, quantity = ticket_info.split(':')  # Assuming format is 'ticket_type_id:quantity'
            ticket_type = TicketType.objects.get(id=ticket_type_id)
            for _ in range(int(quantity)):
                ticket = Ticket(ticket_type=ticket_type, user=request.user)  # Assuming user is logged in
                ticket.save()
                ticket_type.save()  # Save the updated ticket type

        messages.success(request, "Your purchase has been confirmed!")
        return redirect('events:home')
    return redirect('tickets:checkout')
# views.py
import stripe
from decimal import Decimal
import time
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import DetailView

stripe.api_key = settings.STRIPE_SECRET_KEY

def calculate_total_from_cart(request):
    cart = request.session.get('cart', [])
    total_amount = 0
    for item in cart:
        ticket_type = TicketType.objects.get(id=item['ticket_type_id'])
        total_amount += ticket_type.price * item['quantity']
    return total_amount

def initiate_stripe_payment(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
        
    try:
        cart = request.session.get('cart', [])
        if not cart:
            return JsonResponse({'status': 'error', 'message': 'Cart is empty'}, status=400)
            
        # Create line items for Stripe
        line_items = []
        for item in cart:
            ticket_type = TicketType.objects.get(id=item['ticket_type_id'])
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(ticket_type.price * 100),  # Convert to cents
                    'product_data': {
                        'name': f"{ticket_type.event.title} - {ticket_type.name}",
                    },
                },
                'quantity': item['quantity'],
            })

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('tickets:payment_verify')
            ) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('tickets:checkout')),
            customer_email=request.user.email,
            metadata={
                'user_id': request.user.id,
                'order_id': f"ORDER-{int(time.time())}"
            }
        )
        
        # Store session ID in Django session
        request.session['stripe_session_id'] = checkout_session.id
        
        return JsonResponse({
            'status': 'success',
            'payment_url': checkout_session.url
        })
        
    except TicketType.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid ticket type'
        }, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def process_order(request, transaction):
    """Process the order after successful payment"""
    cart = request.session.get('cart', [])
    created_tickets = []
    
    try:
        for item in cart:
            ticket_type = TicketType.objects.get(id=item['ticket_type_id'])
            quantity = item['quantity']
            
            # Create tickets
            for _ in range(quantity):
                ticket = Ticket.objects.create(
                    ticket_type=ticket_type,
                    user=request.user,
                    transaction=transaction
                )
                created_tickets.append(ticket)
        
        # Clear the cart only after all tickets are created successfully
        request.session['cart'] = []
        request.session.modified = True
        
        return created_tickets
        
    except Exception as e:
        # If there's an error, delete any tickets that were created
        for ticket in created_tickets:
            ticket.delete()
        raise Exception(f"Failed to process order: {str(e)}")

from django.core.files.storage import default_storage
from django.template import Template, Context
from django.utils.safestring import mark_safe
from django.core.mail import EmailMultiAlternatives
from django.core.files.storage import default_storage
from django.template import Template, Context
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
import base64
from email.mime.image import MIMEImage
import uuid

def send_ticket_email(transaction):
    """Send email with ticket details and QR codes using CID attachments"""
    subject = f'Your Tickets for Order #{transaction.id}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = transaction.user.email

    # Generate ticket data with CID references
    tickets_data = []
    qr_images = []  # Store QR code images for attachment
    
    for ticket in transaction.tickets.all():
        if ticket.qr_code and default_storage.exists(ticket.qr_code.name):
            try:
                # Generate a unique Content-ID for this QR code
                content_id = f"qr_{uuid.uuid4().hex}"  # Unique ID for each QR code
                
                # Read the QR code file
                with default_storage.open(ticket.qr_code.name, 'rb') as f:
                    qr_code_data = f.read()
                
                # Create MIMEImage object
                qr_image = MIMEImage(qr_code_data)
                qr_image.add_header('Content-ID', f'<{content_id}>')
                qr_image.add_header('Content-Disposition', 'inline')
                qr_images.append(qr_image)
                
                # Add ticket data with CID reference
                tickets_data.append({
                    'ticket': ticket,
                    'qr_code_cid': f'cid:{content_id}'  # Use CID reference in template
                })
            except Exception as e:
                print(f"Error processing QR code for ticket {ticket.id}: {str(e)}")
                tickets_data.append({
                    'ticket': ticket,
                    'qr_code_cid': None
                })

    # Create context
    context = {
        'user': transaction.user,
        'transaction': transaction,
        'tickets_data': tickets_data,
        'site_url': settings.SITE_URL
    }

    try:
        # Render the email template
        html_content = render_to_string('tickets/email/ticket_confirmation.html', context)
        text_content = strip_tags(html_content)

        # Create email message
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to_email]
        )

        # Attach HTML content
        msg.attach_alternative(html_content, "text/html")

        # Attach all QR code images
        for qr_image in qr_images:
            msg.attach(qr_image)

        msg.send()
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def verify_qr_code_data(ticket):
    """Verify QR code data is accessible"""
    if not ticket.qr_code:
        return False, "No QR code field"
    
    if not default_storage.exists(ticket.qr_code.name):
        return False, "QR code file does not exist"
        
    try:
        with default_storage.open(ticket.qr_code.name, 'rb') as f:
            data = f.read()
            return True, f"QR code data length: {len(data)} bytes"
    except Exception as e:
        return False, f"Error reading QR code: {str(e)}"
    
def verify_payment(request):
    session_id = request.GET.get('session_id')
    stored_session_id = request.session.get('stripe_session_id')
    
    if not session_id or session_id != stored_session_id:
        messages.error(request, "Invalid payment verification attempt")
        return redirect('tickets:checkout')
    
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            # Create transaction record
            transaction = Transaction.objects.create(
                user=request.user,
                amount=Decimal(checkout_session.amount_total) / 100,
                token=session_id,
                idx=checkout_session.payment_intent,
                payment_status='completed'
            )
            
            try:
                # Process the order
                process_order(request, transaction)
                request.session.pop('stripe_session_id', None)
                request.session['completed_transaction_token'] = transaction.token
                
                # Send confirmation email
                send_ticket_email(transaction)
                
                messages.success(request, "Payment successful! Your tickets have been confirmed.")
                return redirect('tickets:order_confirmation', token=transaction.token)
                
            except Exception as process_error:
                transaction.payment_status = 'failed'
                transaction.save()
                messages.error(request, str(process_error))
                return redirect('tickets:checkout')
                
        else:
            messages.error(request, f"Payment failed. Status: {checkout_session.payment_status}")
            
    except stripe.error.StripeError as e:
        messages.error(request, f"Payment verification failed: {str(e)}")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('tickets:checkout')

class OrderConfirmationView(DetailView):
    template_name = 'tickets/order_confirmation.html'
    model = Transaction
    context_object_name = 'transaction'

    def get_object(self):
        return Transaction.objects.get(
            token=self.request.session.get('completed_transaction_token')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.get_object()
        context['tickets'] = transaction.tickets.all()
        return context
    

# views.py
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Ticket
from django.utils import timezone

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@login_required
def verify_ticket(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f'Received data: {data}')  # Log the received data
            ticket_code = data.get("ticket_code")
            print(f'Received ticket code: {ticket_code}')  # Log the ticket code
            logger.info(f"Received ticket code: {ticket_code}")  # Log the ticket code

            if not ticket_code:
                return JsonResponse({"status": "error", "message": "No ticket code provided."})

            ticket = get_object_or_404(Ticket, unique_ticket_code=ticket_code)

            if ticket.status == "used":
                return JsonResponse({"status": "error", "message": "This ticket has already been used."})

            # Update the ticket status to "used"
            ticket.status = "used"
            ticket.used_at = timezone.now()
            ticket.save()

            return JsonResponse({"status": "success", "message": "Ticket is valid and has been marked as used."})
        except Exception as e:
            logger.error(f"Error verifying ticket: {e}")
            return JsonResponse({"status": "error", "message": "An unexpected error occurred."}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)
