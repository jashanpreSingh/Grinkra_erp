from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Get attribute from object dynamically"""
    return getattr(obj, attr, False)
