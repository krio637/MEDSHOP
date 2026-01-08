from .models import SiteSettings

def site_settings(request):
    """Make site settings available in all templates"""
    try:
        settings = SiteSettings.get_settings()
    except:
        settings = None
    return {'site_settings': settings}
