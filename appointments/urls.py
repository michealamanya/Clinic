from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('create/', views.appointment_create, name='create'),
    path('<int:pk>/', views.appointment_detail, name='detail'),
    path('<int:pk>/edit/', views.appointment_edit, name='edit'),
    path('<int:pk>/delete/', views.appointment_delete, name='delete'),
    path('<int:pk>/cancel/', views.appointment_cancel, name='cancel'),
    path('<int:pk>/complete/', views.appointment_complete, name='complete'),
    path('<int:pk>/reschedule/', views.appointment_reschedule, name='reschedule'),
]
