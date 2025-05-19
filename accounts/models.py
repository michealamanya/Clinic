from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    phone_extension = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('patient', 'Patient'),
        ('administrator', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"
    
    def get_absolute_url(self):
        return reverse('accounts:profile')

    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
        ]

class Schedule(models.Model):
    staff = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[(i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working = models.BooleanField(default=True)
    
    def __str__(self):
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][self.day_of_week]
        return f"{self.staff} - {day_name}: {self.start_time} to {self.end_time}"
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['staff', 'day_of_week']

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class SystemSettings(models.Model):
    """Stores system-wide settings that can be configured by administrators"""
    
    # Basic information
    clinic_name = models.CharField(max_length=100, default="Smart Clinic")
    clinic_tagline = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(default="info@smartclinic.com")
    contact_phone = models.CharField(max_length=20, blank=True)
    clinic_address = models.TextField(blank=True)
    
    # Appearance settings
    primary_color = models.CharField(max_length=10, default='#3498db')
    secondary_color = models.CharField(max_length=10, default='#2ecc71')
    accent_color = models.CharField(max_length=10, default='#9b59b6')
    enable_dark_mode = models.BooleanField(default=False)
    custom_css = models.TextField(blank=True, null=True)
    clinic_logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    
    # Security settings
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default="We're currently updating our system. Please check back later.")
    password_min_length = models.IntegerField(default=8)
    password_require_uppercase = models.BooleanField(default=True)
    password_require_special = models.BooleanField(default=True)
    password_expiry_days = models.IntegerField(default=90)
    session_timeout_minutes = models.IntegerField(default=30)
    allow_remember_me = models.BooleanField(default=True)
    
    # Notification settings
    notify_patients_on_schedule_change = models.BooleanField(default=True)
    notify_staff_on_new_appointment = models.BooleanField(default=True)
    send_appointment_reminders = models.BooleanField(default=True)
    
    # Timestamps and user references
    created_at = models.DateTimeField(default=timezone.now)  # Add default backt
    updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)  # For backward compatibility
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Optional: Add working days field if needed
    working_days = models.CharField(max_length=20, blank=True, help_text="Comma-separated list of working days (0-6, Monday to Sunday)")
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"System Settings (Last updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def get_settings(cls):
        """Get current settings or create default if none exists"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def get_working_days_list(self):
        """Convert the comma-separated working days string to a list of integers"""
        if not self.working_days:
            return [0, 1, 2, 3, 4]  # Default to Monday-Friday
        return [int(day) for day in self.working_days.split(',')]
    
    def save(self, *args, **kwargs):
        """Override save to ensure there's only one settings instance"""
        self.pk = 1  # Always use ID 1
        super().save(*args, **kwargs)
        
        # Clear cache to ensure settings take immediate effect
        from django.core.cache import cache
        cache.delete('system_settings')
