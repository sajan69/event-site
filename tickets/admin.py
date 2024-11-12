from django.contrib import admin
from .models import TicketType, Ticket
from django.utils.safestring import mark_safe

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'available_quantity', 'sold_out','created_at')
    search_fields = ('name', 'event__title')
    list_filter = ('event',)

    def sold_out(self, obj):
        return obj.is_sold_out

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('unique_ticket_code', 'ticket_type', 'user', 'status', 'purchased_at', 'qr_code_display')
    search_fields = ('unique_ticket_code', 'user__email')
    list_filter = ('status', 'ticket_type')

    def qr_code_display(self, obj):
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" style="width: 50px; height: 50px;" />')
        return "No QR Code"
    qr_code_display.short_description = 'QR Code'