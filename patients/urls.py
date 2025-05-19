from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Existing patient URLs
    path('', views.patient_list, name='list'),
    path('<int:pk>/', views.patient_detail, name='detail'),
    path('create/', views.patient_create, name='create'),
    path('<int:pk>/edit/', views.patient_edit, name='edit'),
    path('<int:pk>/delete/', views.patient_delete, name='delete'),
    
    # Medical record URLs - adding the missing URL pattern
    path('<int:patient_id>/record/create/', views.medical_record_create, name='medical_record_create'),
    path('record/<int:pk>/edit/', views.medical_record_edit, name='medical_record_edit'),
    path('record/<int:pk>/delete/', views.medical_record_delete, name='medical_record_delete'),
    
    # Prescription URLs
    path('<int:patient_id>/prescription/create/', views.prescription_create, name='prescription_create'),
    path('prescription/<int:pk>/edit/', views.prescription_edit, name='prescription_edit'),
    path('prescription/<int:pk>/delete/', views.prescription_delete, name='prescription_delete'),
]
