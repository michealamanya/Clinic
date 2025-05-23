# Generated by Django 5.1.5 on 2025-05-16 06:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clinic_name', models.CharField(default='Smart Clinic', max_length=100)),
                ('clinic_tagline', models.CharField(blank=True, max_length=200)),
                ('clinic_logo', models.ImageField(blank=True, null=True, upload_to='clinic_images/')),
                ('contact_email', models.EmailField(default='info@smartclinic.com', max_length=254)),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('clinic_address', models.TextField(blank=True)),
                ('primary_color', models.CharField(default='#3498db', help_text='Primary color in hex format (e.g. #3498db)', max_length=7)),
                ('secondary_color', models.CharField(default='#2ecc71', help_text='Secondary color in hex format', max_length=7)),
                ('accent_color', models.CharField(default='#9b59b6', help_text='Accent color in hex format', max_length=7)),
                ('enable_dark_mode', models.BooleanField(default=False)),
                ('custom_css', models.TextField(blank=True, help_text='Custom CSS to be applied to the entire site')),
                ('appointment_buffer_minutes', models.IntegerField(default=15, help_text='Buffer time between appointments in minutes')),
                ('max_appointments_per_day', models.IntegerField(default=20, help_text='Maximum appointments allowed per doctor per day')),
                ('patient_registration_open', models.BooleanField(default=True, help_text='Allow new patients to register themselves')),
                ('enable_patient_portal', models.BooleanField(default=True, help_text='Enable the patient portal features')),
                ('enable_online_booking', models.BooleanField(default=True, help_text='Allow online appointment booking')),
                ('require_appointment_approval', models.BooleanField(default=True, help_text='Require staff approval for online appointments')),
                ('send_appointment_reminders', models.BooleanField(default=True)),
                ('reminder_hours_before', models.IntegerField(default=24, help_text='Hours before appointment to send reminder')),
                ('notify_staff_on_new_appointment', models.BooleanField(default=True)),
                ('notify_patients_on_schedule_change', models.BooleanField(default=True)),
                ('meta_description', models.TextField(blank=True, help_text='Site meta description for SEO')),
                ('google_analytics_id', models.CharField(blank=True, help_text='Google Analytics Tracking ID', max_length=20)),
                ('maintenance_mode', models.BooleanField(default=False, help_text='Put the site in maintenance mode')),
                ('maintenance_message', models.TextField(default="We're currently updating our system. Please check back later.")),
                ('working_days', models.CharField(default='0,1,2,3,4', help_text='Comma-separated day numbers (0=Monday, 6=Sunday)', max_length=20)),
                ('working_hours_start', models.TimeField(default='09:00')),
                ('working_hours_end', models.TimeField(default='17:00')),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='settings_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'System Settings',
                'verbose_name_plural': 'System Settings',
            },
        ),
    ]
