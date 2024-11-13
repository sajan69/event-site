from django.contrib import admin
from .models import Event, EventCategory, EventTag,EventOrganizer, GlobalSettings, NewsletterSubscriber
from tickets.models import TicketType
from django import forms

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'events_count')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('name',)
    readonly_fields = ('events_count',)

class TicketTypeInlineForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

    def clean_total_quantity(self):
        total_quantity = self.cleaned_data.get('total_quantity')
        if self.event and total_quantity > self.event.total_capacity:
            raise forms.ValidationError("Total quantity cannot exceed the event's total capacity.")
        return total_quantity

class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1
    form = TicketTypeInlineForm

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.event = obj  # Pass the event instance to the form
        return formset
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'start_datetime', 'end_datetime', 'status', 
        'organizer', 'total_capacity', 'category', 'get_tags'
    )
    search_fields = ('title', 'organizer__email', 'category__name', 'tags__name')  # Updated to search by tag name
    list_filter = ('status', 'category', 'organizer', 'tags')  # Updated to filter by tags
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TicketTypeInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'organizer', 'category', 'tags')  # Updated to include tags
        }),
        ('Event Timing', {
            'fields': ('start_datetime', 'end_datetime', 'venue_name', 'address', 'city', 'country')
        }),
        ('Pricing and Capacity', {
            'fields': ('is_free', 'total_capacity', 'poster', 'status', 'is_featured')
        }),
    )

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Tags'

    actions = ['mark_as_published']

    def mark_as_published(self, request, queryset):
        queryset.update(status='published')
        self.message_user(request, "Selected events have been marked as published.")
    mark_as_published.short_description = "Mark selected events as published"




@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not GlobalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at', 'last_sent_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at', 'last_sent_at']