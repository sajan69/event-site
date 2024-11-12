from django.contrib import admin
from .models import Event, EventCategory, EventTag,EventOrganizer

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'events_count')
    search_fields = ('name', 'email')
    list_filter = ('name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'start_datetime', 'end_datetime', 'status', 
        'organizer', 'total_capacity', 'category', 'get_tags'
    )
    search_fields = ('title', 'organizer__email')
    list_filter = ('status', 'category')  
    prepopulated_fields = {'slug': ('title',)}

    def total_capacity(self, obj):
        return obj.total_capacity
    total_capacity.short_description = 'Total Capacity'

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Tags'