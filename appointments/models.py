from django.db import models
from django.urls import reverse
from django.utils import timezone
from patients.models import Patient
from accounts.models import UserProfile

class AppointmentType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    color_code = models.CharField(max_length=7, default="#3498db", help_text="HEX color code")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.SET_NULL, null=True, related_name='appointments')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} - {self.date} {self.start_time}"
    
    def get_absolute_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.pk})
    
    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'start_time']),
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
            models.Index(fields=['status']),
        ]

class AppointmentHistory(models.Model):
    """Tracks changes to appointment status"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Appointment Histories"
    
    def __str__(self):
        return f"{self.appointment} - {self.get_status_display()}"
