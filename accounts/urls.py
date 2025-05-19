from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs - using Django's built-in auth views
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('register/', views.register, name='register'),
    
    # Department URLs - using correct view function names
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Patient portal URLs
    path('patient/profile/update/', views.patient_profile_update, name='patient_profile_update'),
    path('patient/medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/doctors/', views.patient_doctors, name='patient_doctors'),
    path('patient/video-call/<int:doctor_id>/', views.request_video_call, name='request_video_call'),
    path('patient/video-consultation/', views.patient_video_consultation, name='patient_video_consultation'),
    path('patient/health-tracker/', views.patient_health_tracker, name='patient_health_tracker'),
    path('patient/document-upload/', views.patient_document_upload, name='patient_document_upload'),
    
    # Settings URLs
    path('settings/', views.settings_home, name='settings'),
    path('settings/general/', views.settings_general, name='settings_general'),
    path('settings/appearance/', views.settings_appearance, name='settings_appearance'),
    path('settings/notifications/', views.settings_notifications, name='settings_notifications'),
    path('settings/security/', views.settings_security, name='settings_security'),
    path('settings/system-status/', views.settings_system_status, name='settings_system_status'),
    path('settings/backups/', views.settings_backups, name='settings_backups'),
    
    # Doctor creation
    path('doctors/create/', views.doctor_create, name='doctor_create'),
    
    # API endpoints
    path('api/system-metrics/', views.system_metrics_api, name='system_metrics_api'),
    path('api/debug-settings/', views.debug_settings_api, name='debug_settings_api'),
    
    # Backup management
    path('backups/create/', views.create_backup, name='create_backup'),
    path('backups/<str:filename>/download/', views.download_backup, name='download_backup'),
    path('backups/<str:filename>/restore/', views.restore_backup, name='restore_backup'),
    path('backups/<str:filename>/delete/', views.delete_backup, name='delete_backup'),
]
