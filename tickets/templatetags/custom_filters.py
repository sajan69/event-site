from django import template
from events.models import EventCategory

register = template.Library()

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def get_item(category_id):
    try:
        return EventCategory.objects.get(id=category_id).name
    except EventCategory.DoesNotExist:
        return None