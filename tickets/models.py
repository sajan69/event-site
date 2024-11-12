from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid
import qrcode
from io import BytesIO
from django.core.files import File

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
        Ensure available quantity is initialized to total quantity only once
        and update the sold-out status based on available quantity.
        """
        # Only set available_quantity to total_quantity on the first save
        if self.pk is None:  # Only when the instance is first created
            self.available_quantity = self.total_quantity
        
        # Update the sold-out status based on available quantity
        self.is_sold_out = self.available_quantity <= 0
        
        super().save(*args, **kwargs)

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
        Generate a unique ticket code
        """
        return uuid.uuid4().hex[:10].upper()

    def generate_qr_code(self):
        """
        Generate QR code for the ticket
        """
        qr = qrcode.QRCode(
            version=1, 
            box_size=10, 
            border=5
        )
        qr.add_data(self.unique_ticket_code)
        qr.make(fit=True)
        
        img = qr.make_image(
            fill_color="black", 
            back_color="white"
        )
        
        # Save QR code
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'ticket_qr_{self.unique_ticket_code}.png'
        
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        """
        Custom save method to generate ticket code and QR, and update quantity only on creation.
        """
        # Only check and update available quantity when the ticket is first created
        if not self.pk:  # self.pk will be None if the object is new (not yet saved)
            # Check available quantity
            if self.ticket_type.available_quantity <= 0:
                raise ValueError("Cannot create ticket: No available quantity.")

            # Generate unique ticket code if it does not exist
            if not self.unique_ticket_code:
                self.unique_ticket_code = self.generate_unique_ticket_code()

            # Generate QR code if not exists
            if not self.qr_code:
                self.generate_qr_code()

            # Decrement available quantity in TicketType only on creation
            self.ticket_type.available_quantity -= 1
            self.ticket_type.is_sold_out = self.ticket_type.available_quantity <= 0
            self.ticket_type.save()

        super().save(*args, **kwargs)  # Save the ticket without altering quantity on update

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
