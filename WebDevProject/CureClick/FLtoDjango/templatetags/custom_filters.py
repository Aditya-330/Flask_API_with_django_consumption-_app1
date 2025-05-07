from django import template

register = template.Library()

@register.filter(name='absolute')
def absolute(value):
    """Returns the absolute value."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

@register.filter(name='abs')
def abs_filter(value):
    """Alternative name for absolute value filter."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value