from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._settings_model = None

    def _get_settings(self):
        # Lazy import to avoid circular imports and handle missing model
        if self._settings_model is None:
            try:
                from .models import SystemSettings
                self._settings_model = SystemSettings
            except (ImportError, AttributeError):
                # Model doesn't exist yet, possibly during migration
                return None
        
        try:
            return self._settings_model.get_settings()
        except Exception:
            # Handle database errors or table not created yet
            return None

    def __call__(self, request):
        # Check if maintenance mode is enabled
        try:
            from accounts.models import SystemSettings
            settings = SystemSettings.get_settings()
            
            # Skip maintenance mode for staff users
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)
                
            # Allow access to login page and patient portal paths
            if request.path.startswith('/login/') or request.path.startswith('/register/') or request.path == '/accounts/login/':
                return self.get_response(request)
            
            # Allow authenticated patients to access their dashboard
            if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'patient':
                # Allow access to patient dashboard and related views
                if request.path.startswith('/dashboard/') or request.path.startswith('/accounts/patient/'):
                    return self.get_response(request)
            
            # Show maintenance page for all other cases if maintenance mode is on
            if settings.maintenance_mode:
                return render(request, 'accounts/maintenance.html', {
                    'message': settings.maintenance_message
                })
        except:
            # If there's an error accessing settings, continue with normal flow
            pass
            
        return self.get_response(request)
