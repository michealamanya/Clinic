"""
URL configuration for clinicproject project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # App URLs
    path('appointments/', include('appointments.urls')),
    path('patients/', include('patients.urls')),
    path('accounts/', include('accounts.urls')),
    # Authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
    # Dashboard/Home redirect
    path('', RedirectView.as_view(url='dashboard/', permanent=True)),
    path('dashboard/', include('accounts.dashboard_urls')),
    
    # Static pages
    path('privacy-policy/', TemplateView.as_view(template_name='pages/privacy_policy.html'), name='privacy_policy'),
    path('terms-of-service/', TemplateView.as_view(template_name='pages/terms_of_service.html'), name='terms_of_service'),
    path('contact/', accounts_views.contact_us, name='contact_us'),
    path('about/', TemplateView.as_view(template_name='pages/about_us.html'), name='about_us'),
    path('services/', accounts_views.services, name='services'),
    path('faq/', accounts_views.faq, name='faq'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
