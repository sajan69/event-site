from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
import time
from django.db import transaction as db_transaction  # Renamed import
class TicketType(models.Model):
    """
    Defines different ticket types for an event
    """
    TICKET_CATEGORIES = [
        ('standard', 'Standard'),
        ('vip', 'VIP'),
        ('premium', 'Premium'),
        ('early_bird', 'Early Bird')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationship with Event
    event = models.ForeignKey(
        'events.Event', 
        on_delete=models.CASCADE, 
        related_name='ticket_types'
    )
    
    # Ticket Type Details
    name = models.CharField(
        max_length=50, 
        choices=TICKET_CATEGORIES, 
        default='standard'
    )
    description = models.TextField(blank=True, null=True)
    
    # Pricing and Quantity
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    
    # Additional Perks for Different Ticket Types
    additional_perks = models.TextField(blank=True, null=True)
    
    # Sold-out Status
    is_sold_out = models.BooleanField(default=False)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """
        Handle ticket type creation and updates
        """
        is_new = self.pk is None
        
        # Calculate total existing quantity
        total_existing_quantity = 0
        if self.pk:
            total_existing_quantity = sum(
                ticket.total_quantity 
                for ticket in self.event.ticket_types.exclude(pk=self.pk)
            )
        else:
            total_existing_quantity = sum(
                ticket.total_quantity 
                for ticket in self.event.ticket_types.all()
            )

        # Validate total capacity
        if total_existing_quantity + self.total_quantity > self.event.total_capacity:
            raise ValueError(
                f"Total quantity of all ticket types ({total_existing_quantity + self.total_quantity}) "
                f"cannot exceed the event's total capacity ({self.event.total_capacity})."
            )

        # Set initial available quantity
        if self.pk is None:
            self.available_quantity = self.total_quantity
        
        # Update sold-out status
        self.is_sold_out = self.available_quantity <= 0
        
        super().save(*args, **kwargs)
        
        # Send email notification for new ticket types in featured events
        if is_new and self.event.is_featured:
            from .utils import send_new_tickets_email
            send_new_tickets_email(self.event, [self])


    def __str__(self):
        return f"{self.event.title} - {self.get_name_display()} Ticket"

    class Meta:
        unique_together = ['event', 'name']
        ordering = ['price']

class Ticket(models.Model):
    """
    Individual ticket purchased by a user
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='tickets'
    )
    ticket_type = models.ForeignKey(
        TicketType, 
        on_delete=models.CASCADE, 
        related_name='tickets'
    )
    
    # Ticket Identification
    unique_ticket_code = models.CharField(
        max_length=50, 
        unique=True
    )
    qr_code = models.ImageField(
        upload_to='ticket_qr_codes/', 
        null=True, 
        blank=True
    )
    
    # Ticket Status and Timestamps
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name='tickets')

    purchased_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    
    def generate_unique_ticket_code(self):
        """
        Generate a unique ticket code with retries and timestamp
        """
        max_attempts = 10
        for attempt in range(max_attempts):
            timestamp = int(time.time() * 1000)
            code = f"{self.ticket_type.event.id.hex[:4]}-{timestamp}-{uuid.uuid4().hex[:6].upper()}"
            
            if not Ticket.objects.filter(unique_ticket_code=code).exists():
                return code
            time.sleep(0.1)
        raise ValueError("Unable to generate unique ticket code after maximum attempts")

    def generate_qr_code(self):
        """Generate QR code for the ticket"""
        try:
            if not self.unique_ticket_code:
                raise ValueError("Cannot generate QR code without a unique ticket code")

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5
            )
            qr.add_data(self.unique_ticket_code)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)  # Reset buffer position
            
            filename = f'ticket_qr_{self.unique_ticket_code}.png'
            
            # Delete existing QR code if it exists
            if self.qr_code:
                try:
                    self.qr_code.delete(save=False)
                except Exception:
                    pass
            
            # Save new QR code
            self.qr_code.save(filename, File(buffer), save=True)  # Changed to save=True
            buffer.close()
            
        except Exception as e:
            print(f"QR Code generation error: {str(e)}")  # Add logging
            raise ValueError(f"Failed to generate QR code: {str(e)}")

    @db_transaction.atomic  # Using renamed import
    def save(self, *args, **kwargs):
        """
        Custom save method to generate ticket code and QR, and update quantity only on creation.
        """
        is_new = self.pk is None
        
        if is_new:
            # Lock the ticket type for update
            ticket_type = TicketType.objects.select_for_update().get(pk=self.ticket_type.pk)
            
            if ticket_type.available_quantity <= 0:
                raise ValueError("Cannot create ticket: No available quantity.")
            
            # Generate unique code
            if not self.unique_ticket_code:
                self.unique_ticket_code = self.generate_unique_ticket_code()
            
            # Save first to get the ID
            super().save(*args, **kwargs)
            
            # Generate QR code
            try:
                self.generate_qr_code()
                # Update only the QR code field
                super().save(update_fields=['qr_code'])
            except Exception as e:
                raise ValueError(f"Failed to generate QR code: {str(e)}")
            
            # Update ticket type quantity
            ticket_type.available_quantity -= 1
            ticket_type.is_sold_out = ticket_type.available_quantity <= 0
            ticket_type.save()
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_type} - {self.unique_ticket_code}"

    class Meta:
        ordering = ['-purchased_at']
        indexes = [
            models.Index(fields=['unique_ticket_code', 'status'])
        ]

class Transaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
   
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    token = models.CharField(max_length=255)
    idx = models.CharField(max_length=255)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.payment_status})"
