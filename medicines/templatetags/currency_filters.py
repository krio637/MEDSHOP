from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def rupees(value):
    """Convert value to Indian Rupees format"""
    try:
        # Convert to float if it's a string
        if isinstance(value, str):
            value = float(value)
        
        # Format with Indian numbering system (lakhs, crores)
        if value >= 10000000:  # 1 crore
            crores = value / 10000000
            return f"₹{crores:.1f} Cr"
        elif value >= 100000:  # 1 lakh
            lakhs = value / 100000
            return f"₹{lakhs:.1f} L"
        elif value >= 1000:  # Thousands
            return f"₹{value:,.0f}"
        else:
            return f"₹{value:.2f}"
    except (ValueError, TypeError):
        return f"₹0.00"

@register.filter
def rupees_simple(value):
    """Simple rupee formatting without abbreviations"""
    try:
        if isinstance(value, str):
            value = float(value)
        return f"₹{value:,.2f}"
    except (ValueError, TypeError):
        return f"₹0.00"

@register.filter
def rupees_no_decimal(value):
    """Rupee formatting without decimal places"""
    try:
        if isinstance(value, str):
            value = float(value)
        return f"₹{value:,.0f}"
    except (ValueError, TypeError):
        return f"₹0"


@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def whatsapp_number(value):
    """Clean phone number for WhatsApp URL - remove +, spaces, and special chars"""
    if not value:
        return '919710036499'
    # Remove +, spaces, dashes, and any non-digit characters
    import re
    cleaned = re.sub(r'[^\d]', '', str(value))
    return cleaned if cleaned else '919710036499'
