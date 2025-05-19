from django.core.cache import cache

def system_settings(request):
    """Add system settings to template context"""
    # Try to get settings from cache
    system_settings = cache.get('system_settings')
    
    if not system_settings:
        try:
            from .models import SystemSettings
            system_settings = SystemSettings.get_settings()
            # Cache for 1 hour
            cache.set('system_settings', system_settings, 3600)
        except:
            system_settings = None
    
    # Generate dynamic CSS variables
    css_vars = ""
    if system_settings:
        css_vars = f"""
        :root {{
            --primary-color: {system_settings.primary_color};
            --primary-light: {system_settings.primary_color}99;
            --primary-dark: {system_settings.primary_color}dd;
            --secondary-color: {system_settings.secondary_color};
            --accent-color: {system_settings.accent_color};
        }}
        """
    
    return {
        'system_settings': system_settings,
        'dynamic_css_variables': css_vars
    }
