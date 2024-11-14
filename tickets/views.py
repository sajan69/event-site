import base64
from django.conf import settings
from django.shortcuts import render, redirect
import requests
from .models import TicketType, Ticket, Transaction
from django.contrib import messages
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
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


def add_to_cart(request, event_id):
    if request.method == 'POST':
        ticket_type_id = request.POST.get('ticket_type_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Initialize cart in session if it doesn't exist
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        
        # Convert list to dictionary if necessary (for backward compatibility)
        if isinstance(cart, list):
            new_cart = {}
            for item in cart:
                new_cart[str(item['ticket_type_id'])] = new_cart.get(str(item['ticket_type_id']), 0) + item['quantity']
            cart = new_cart
        
        # Add or update ticket quantity in cart
        cart[ticket_type_id] = cart.get(ticket_type_id, 0) + quantity
        
        request.session['cart'] = cart
        request.session.modified = True
        
        # Calculate total items in cart
        total_items = sum(cart.values())
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Item added to cart',
                'cart_count': total_items
            })
        
        return redirect('tickets:checkout')
    
    return redirect('events:detail', event_id=event_id)

def checkout(request):
    cart = request.session.get('cart', {})
    cart_tickets = []
    total_price = 0
    
    # Convert list to dictionary if necessary
    if isinstance(cart, list):
        new_cart = {}
        for item in cart:
            ticket_type_id = str(item['ticket_type_id'])
            new_cart[ticket_type_id] = new_cart.get(ticket_type_id, 0) + item['quantity']
        cart = new_cart
        request.session['cart'] = cart
    
    for ticket_type_id, quantity in cart.items():
        ticket_type = TicketType.objects.get(id=ticket_type_id)
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



@require_POST
def update_cart(request):
    action = request.POST.get('action')
    ticket_type_id = request.POST.get('ticket_type_id')
    
    cart = request.session.get('cart', {})
    
    # Convert list to dictionary if necessary
    if isinstance(cart, list):
        new_cart = {}
        for item in cart:
            new_cart[str(item['ticket_type_id'])] = new_cart.get(str(item['ticket_type_id']), 0) + item['quantity']
        cart = new_cart
    
    if action == 'add':
        cart[ticket_type_id] = cart.get(ticket_type_id, 0) + 1
    elif action == 'subtract':
        if cart.get(ticket_type_id, 0) > 1:
            cart[ticket_type_id] -= 1
        else:
            cart.pop(ticket_type_id, None)
    elif action == 'delete':
        cart.pop(ticket_type_id, None)
    
    request.session['cart'] = cart
    request.session.modified = True
    
    return redirect('tickets:checkout')


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
        cart = request.session.get('cart', {})  # Get cart as dictionary
        if not cart:
            return JsonResponse({'status': 'error', 'message': 'Cart is empty'}, status=400)
            
        # Create line items for Stripe
        line_items = []
        for ticket_type_id, quantity in cart.items():
            try:
                ticket_type = TicketType.objects.get(id=ticket_type_id)
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(ticket_type.price * 100),  # Convert to cents
                        'product_data': {
                            'name': f"{ticket_type.event.title} - {ticket_type.name}",
                        },
                    },
                    'quantity': quantity,
                })
            except TicketType.DoesNotExist:
                continue

        if not line_items:
            return JsonResponse({'status': 'error', 'message': 'No valid tickets in cart'}, status=400)

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
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required

@transaction.atomic
def process_order(request, transaction_obj):
    """Process the order after successful payment"""
    cart = request.session.get('cart', {})
    created_tickets = []
    
    try:
        # Lock and validate all ticket types first
        ticket_types = {}
        for ticket_type_id, quantity in cart.items():
            ticket_type = TicketType.objects.select_for_update().get(id=ticket_type_id)
            
            # Verify available quantity
            if ticket_type.available_quantity < quantity:
                raise ValueError(f"Insufficient tickets available for {ticket_type.name}")
                
            ticket_types[ticket_type_id] = ticket_type
        
        # Create tickets for each type
        for ticket_type_id, quantity in cart.items():
            ticket_type = ticket_types[ticket_type_id]
            
            for _ in range(quantity):
                # Create ticket with minimal data first
                ticket = Ticket(
                    ticket_type=ticket_type,
                    user=request.user,
                    transaction=transaction_obj,
                    status='active'
                )
                
                # Generate and verify unique code
                max_attempts = 5
                for attempt in range(max_attempts):
                    unique_code = ticket.generate_unique_ticket_code()
                    if not Ticket.objects.filter(unique_ticket_code=unique_code).exists():
                        ticket.unique_ticket_code = unique_code
                        break
                    if attempt == max_attempts - 1:
                        raise ValueError("Failed to generate unique ticket code")
                
                # Save ticket to generate ID
                ticket.save()
                
                # Generate QR code
                ticket.generate_qr_code()
                ticket.save()
                
                created_tickets.append(ticket)
                
                # Update ticket type quantity
                ticket_type.available_quantity -= 1
                ticket_type.save()
        
        # Verify all tickets were created
        if len(created_tickets) != sum(cart.values()):
            raise ValueError("Not all tickets were created successfully")
        
        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True
        
        return created_tickets
        
    except Exception as e:
        # The atomic transaction will roll back all database changes
        raise Exception(f"Failed to process order: {str(e)}")
    
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
        # Retrieve the Stripe session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status != 'paid':
            messages.error(request, "Payment was not completed successfully")
            return redirect('tickets:checkout')
            
        # Start atomic transaction
        with transaction.atomic():
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                user=request.user,
                amount=Decimal(checkout_session.amount_total) / 100,
                token=session_id,
                idx=checkout_session.payment_intent,
                payment_status='completed'
            )
            
            try:
                created_tickets = process_order(request, transaction_obj)
                
                # Verify tickets and QR codes
                for ticket in created_tickets:
                    success, message = verify_qr_code_data(ticket)
                    if not success:
                        raise ValueError(f"QR code verification failed for ticket {ticket.unique_ticket_code}: {message}")
                
                # Clean up session
                request.session.pop('stripe_session_id', None)
                request.session['completed_transaction_token'] = transaction_obj.token
                
                # Send confirmation email
                send_ticket_email(transaction_obj)
                
                messages.success(request, "Payment successful! Your tickets have been confirmed.")
                return redirect('tickets:order_confirmation', token=transaction_obj.token)
                
            except Exception as process_error:
                # Rollback will happen automatically due to atomic transaction
                transaction_obj.payment_status = 'failed'
                transaction_obj.save()
                messages.error(request, str(process_error))
                return redirect('tickets:checkout')
                
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
    
@staff_member_required
def verify_ticket(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            ticket_code = data.get("ticket_code")
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
            return JsonResponse({"status": "error", "message": "An unexpected error occurred."}, status=500)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)
