from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Count, Q
from patients.models import Patient, MedicalRecord, Prescription  # Updated imports
from .forms import (
    UserRegistrationForm, UserProfileForm, DepartmentForm, ScheduleForm, 
    PatientProfileForm, ContactForm, DoctorProfileForm, DoctorCreationForm
)
from .models import Department, UserProfile, Schedule
import psutil
import os
import platform
import time
import json
from django.http import JsonResponse
from django.db import connection
from django.apps import apps
import os
import datetime  # Make sure this import is available
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Auto-login after registration
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to the Smart Clinic.')
            return redirect('dashboard:index')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Register New Account'
    }
    return render(request, 'accounts/register.html', context)

@login_required
def profile(request):
    user_profile = request.user.profile
    schedules = user_profile.schedules.all().order_by('day_of_week')
    
    # Calculate missing days
    existing_days = set(schedule.day_of_week for schedule in schedules)
    all_days = set(range(7))  # 0-6 for Monday to Sunday
    missing_days = sorted(all_days - existing_days)
    
    context = {
        'user_profile': user_profile,
        'schedules': schedules,
        'missing_days': missing_days,
        'title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit(request):
    user_profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'form': form,
        'title': 'Edit Profile'
    }
    return render(request, 'accounts/profile_form.html', context)

@login_required
def dashboard(request):
    user_profile = request.user.profile
    role = user_profile.role
    
    # Import necessary models at the beginning of the function
    from patients.models import Patient
    from appointments.models import Appointment
    
    # Get counts for dashboard stats
    total_patients = Patient.objects.count()
    total_appointments = Appointment.objects.count()
    
    # Get active departments
    departments = Department.objects.filter(is_active=True)
    
    # Mark new departments (created in the last 7 days)
    from django.utils import timezone
    one_week_ago = timezone.now() - timezone.timedelta(days=7)
    
    # Enrich department data with counts
    for dept in departments:
        dept.staff_count = UserProfile.objects.filter(department=dept).count()
        dept.appointment_count = Appointment.objects.filter(doctor__department=dept).count()
        
        # Fix datetime comparison
        if hasattr(dept, 'date_created'):
            # Convert to datetime if it's a date object
            if isinstance(dept.date_created, datetime.date) and not isinstance(dept.date_created, datetime.datetime):
                dept_created_datetime = datetime.datetime.combine(dept.date_created, datetime.time.min)
                dept_created_datetime = timezone.make_aware(dept_created_datetime)
                dept.is_new = dept_created_datetime > one_week_ago
            else:
                # It's already a datetime
                dept.is_new = dept.date_created > one_week_ago
        else:
            dept.is_new = False
    
    # Today's appointments
    today = timezone.now().date()
    todays_appointments = Appointment.objects.filter(date=today).order_by('start_time')
    
    # Mark new appointments (created in the last 24 hours)
    one_day_ago = timezone.now() - timezone.timedelta(days=1)
    for appt in todays_appointments:
        # Fix datetime comparison for appointments too
        if hasattr(appt, 'created_at'):
            if isinstance(appt.created_at, datetime.date) and not isinstance(appt.created_at, datetime.datetime):
                appt_created_datetime = datetime.datetime.combine(appt.created_at, datetime.time.min)
                appt_created_datetime = timezone.make_aware(appt_created_datetime)
                appt.is_new = appt_created_datetime > one_day_ago
            else:
                appt.is_new = appt.created_at > one_day_ago
        else:
            appt.is_new = False
    
    # Generate recent activities
    recent_activities = []
    
    # Recent appointments
    recent_appts = Appointment.objects.filter(
        created_at__gte=one_week_ago
    ).order_by('-created_at')[:5]
    
    for appt in recent_appts:
        recent_activities.append({
            'icon': 'fas fa-calendar-check',
            'description': f'Appointment scheduled for {appt.patient}',
            'timestamp': appt.created_at,
            'is_new': appt.created_at > one_day_ago
        })
    
    # Recent patients
    recent_patients = Patient.objects.filter(
        created_at__gte=one_week_ago
    ).order_by('-created_at')[:5]
    
    for patient in recent_patients:
        recent_activities.append({
            'icon': 'fas fa-user-plus',
            'description': f'New patient registered: {patient.first_name} {patient.last_name}',
            'timestamp': patient.created_at,
            'is_new': patient.created_at > one_day_ago
        })
    
    # Sort by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Limit to 10 most recent
    
    # Render different dashboard based on user role
    if role == 'doctor':
        # Doctor-specific dashboard
        my_appointments = Appointment.objects.filter(
            doctor=user_profile, 
            date__gte=today
        ).order_by('date', 'start_time')
        
        my_patients = Patient.objects.filter(
            appointments__doctor=user_profile
        ).distinct().order_by('last_name', 'first_name')
        
        return render(request, 'accounts/doctor_dashboard.html', {
            'total_patients': my_patients.count(),
            'total_appointments': my_appointments.count(),
            'todays_appointments': todays_appointments.filter(doctor=user_profile),
            'upcoming_appointments': my_appointments[:10],
            'recent_patients': my_patients[:6],
            'recent_activities': recent_activities,
            'departments': departments,
            'title': 'Doctor Dashboard'
        })
    
    elif role == 'nurse':
        # Nurse-specific dashboard
        if user_profile.department:
            department_doctors = UserProfile.objects.filter(
                department=user_profile.department,
                role='doctor'
            )
            department_appointments = Appointment.objects.filter(
                doctor__in=department_doctors,
                date__gte=today
            ).order_by('date', 'start_time')
        else:
            department_appointments = Appointment.objects.none()
        
        return render(request, 'accounts/nurse_dashboard.html', {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'todays_appointments': todays_appointments,
            'department_appointments': department_appointments[:10],
            'title': 'Nurse Dashboard'
        })
    
    elif role == 'receptionist':
        # Receptionist dashboard with focus on appointments
        return render(request, 'accounts/dashboard.html', {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'todays_appointments': todays_appointments,
            'title': 'Reception Dashboard'
        })
    
    elif role == 'patient':
        # Patient-specific dashboard (portal)
        # Fix the problematic query - patient users might not have associated Patient records
        try:
            # Try to find an existing Patient record for this user
            from patients.models import Patient
            patient = Patient.objects.filter(email=request.user.email).first()
            
            if patient:
                # If patient record exists, use it to query appointments
                my_appointments = Appointment.objects.filter(
                    patient=patient,
                    date__gte=today
                ).order_by('date', 'start_time')
                
                past_appointments = Appointment.objects.filter(
                    patient=patient,
                    date__lt=today
                ).order_by('-date', '-start_time')
            else:
                # If no patient record exists, show empty query sets
                my_appointments = Appointment.objects.none()
                past_appointments = Appointment.objects.none()
                
        except ImportError:
            # Handle case where Patient model might not be accessible
            my_appointments = Appointment.objects.none()
            past_appointments = Appointment.objects.none()
        
        return render(request, 'accounts/patient_dashboard.html', {
            'upcoming_appointments': my_appointments,
            'past_appointments': past_appointments[:5],
            'title': 'Patient Portal'
        })
    
    else:
        # Admin or default dashboard
        doctors_with_counts = None
        if request.user.is_staff:
            doctors_with_counts = UserProfile.objects.filter(role='doctor').annotate(
                appointment_count=Count('doctor_appointments'),
                patient_count=Count('doctor_appointments__patient', distinct=True),
                today_count=Count('doctor_appointments', 
                            filter=Q(doctor_appointments__date=today))
            ).order_by('-appointment_count')[:6]
            
            # Mark new doctors with the same date handling
            for doctor in doctors_with_counts:
                if isinstance(doctor.date_joined, datetime.date) and not isinstance(doctor.date_joined, datetime.datetime):
                    doctor_joined_datetime = datetime.datetime.combine(doctor.date_joined, datetime.time.min)
                    doctor_joined_datetime = timezone.make_aware(doctor_joined_datetime)
                    doctor.is_new = doctor_joined_datetime > one_week_ago
                else:
                    doctor.is_new = doctor.date_joined > one_week_ago
        
        return render(request, 'accounts/dashboard.html', {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'todays_appointments': todays_appointments,
            'doctors_with_counts': doctors_with_counts,
            'departments': departments,
            'recent_activities': recent_activities,
            'title': 'Dashboard'
        })

# New views for patient portal features
@login_required
def patient_profile_update(request):
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    user = request.user
    
    # Find or create patient record for this user
    try:
        # Try to find an existing Patient record for this user by email
        patient = Patient.objects.get(email=user.email)
    except Patient.DoesNotExist:
        # Create a new patient record with required fields
        from django.utils import timezone
        import datetime
        
        # Use a default date of birth (this will be updated by the user)
        default_dob = timezone.now() - datetime.timedelta(days=365*30)  # Default to 30 years ago
        
        # Create a new patient with required fields that actually exist in the model
        patient = Patient(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            date_of_birth=default_dob,
            gender="unspecified"
            # Remove phone_number field as it doesn't exist in the model
        )
        
        try:
            patient.save()
            messages.info(request, 'A new patient profile has been created for you. Please update your details, especially your date of birth.')
        except Exception as e:
            messages.error(request, f"Error creating patient profile: {str(e)}")
            return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:dashboard')  # Redirect to patient dashboard
    else:
        form = PatientProfileForm(instance=patient)
    
    return render(request, 'accounts/patient_profile_form.html', {
        'form': form,
        'title': 'Update Profile',
        'patient': patient
    })

@login_required
def patient_medical_history(request):
    # Get the current user's patient profile
    try:
        # The Patient model doesn't have a 'user' field
        # Use email to find the patient associated with this user
        patient = Patient.objects.get(email=request.user.email)
        
        # Now query medical records using the Patient instance
        medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-date')
        
        context = {
            'medical_records': medical_records,
            'patient': patient,
            'title': 'My Medical History'
        }
        return render(request, 'accounts/patient_medical_history.html', context)
    except Patient.DoesNotExist:
        messages.error(request, "No patient profile found for your account. Please complete your profile first.")
        return redirect('accounts:patient_profile_update')
    except Exception as e:
        messages.error(request, f"Error retrieving medical records: {str(e)}")
        # Fix the incorrect URL name - use dashboard:index instead of accounts:dashboard
        return redirect('dashboard:index')

@login_required
def patient_prescriptions(request):
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    # Get the patient record associated with this user
    try:
        patient = Patient.objects.get(email=request.user.email)
        # Query prescriptions using the patient object directly
        prescriptions = Prescription.objects.filter(patient=patient).order_by('-start_date')
        
        return render(request, 'accounts/patient_prescriptions.html', {
            'prescriptions': prescriptions,
            'title': 'My Prescriptions',
            'patient': patient
        })
    except Patient.DoesNotExist:
        messages.warning(request, 'Your patient profile is not complete. Please update your profile first.')
        return redirect('accounts:patient_profile_update')
    except Exception as e:
        messages.error(request, f'Error retrieving prescriptions: {str(e)}')
        return redirect('dashboard:index')

@login_required
def patient_doctors(request):
    """View for patients to find doctors for video consultations"""
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    # Get only active doctors to display to patients
    doctors = UserProfile.objects.filter(role='doctor', is_active=True).order_by('department', 'user__last_name')
    departments = Department.objects.filter(is_active=True)
    
    return render(request, 'accounts/patient_doctors.html', {
        'doctors': doctors,
        'departments': departments,
        'title': 'Find a Doctor'
    })

@login_required
def request_video_call(request, doctor_id):
    """Request a video call with a doctor"""
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    doctor = get_object_or_404(UserProfile, id=doctor_id, role='doctor')
    
    # Get the patient record associated with the current user
    try:
        patient = Patient.objects.get(email=request.user.email)
        
        # Create a video consultation appointment for the current patient only
        from appointments.models import Appointment, AppointmentType
        from django.utils import timezone
        
        # Get or create a Video Consultation appointment type
        video_type, created = AppointmentType.objects.get_or_create(
            name="Video Consultation",
            defaults={"duration": 30, "color": "#4a6bff"}
        )
        
        # Create preliminary appointment with pending status
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_type=video_type,
            date=timezone.now().date() + timezone.timedelta(days=1),  # Default to tomorrow
            start_time=timezone.now().time(),
            end_time=(timezone.datetime.combine(timezone.now().date(), timezone.now().time()) + 
                     timezone.timedelta(minutes=30)).time(),
            status='scheduled',
            notes="Video consultation request - pending scheduling"
        )
        
        messages.success(request, f'Video call request sent to Dr. {doctor.user.get_full_name()}. You will be contacted soon to confirm the time.')
        return redirect('appointments:detail', pk=appointment.pk)
        
    except Patient.DoesNotExist:
        messages.error(request, 'We couldn\'t find your patient record. Please complete your profile first.')
        return redirect('accounts:patient_profile_update')
    except Exception as e:
        messages.error(request, f'Error scheduling video consultation: {str(e)}')
        return redirect('accounts:patient_doctors')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on user role
            if hasattr(user, 'profile'):
                if user.profile.role == 'patient':
                    return redirect('accounts:patient_dashboard')
            return redirect('dashboard:index')
        else:
            error_message = "Invalid username or password."
            return render(request, 'registration/login.html', {'error_message': error_message})
    
    # Check if patient portal access was requested
    is_patient_portal = 'portal' in request.GET and request.GET['portal'] == 'patient'
    
    return render(request, 'registration/login.html', {
        'is_patient_portal': is_patient_portal,
        'title': 'Patient Portal Login' if is_patient_portal else 'Login'
    })

# Department views
@login_required
def department_list(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
        
    departments = Department.objects.all().order_by('name')
    
    context = {
        'departments': departments,
        'title': 'Departments'
    }
    return render(request, 'accounts/department_list.html', context)

@login_required
def department_detail(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
        
    department = get_object_or_404(Department, pk=pk)
    staff = UserProfile.objects.filter(department=department).order_by('role', 'user__last_name')
    
    context = {
        'department': department,
        'staff': staff,
        'title': f'Department: {department.name}'
    }
    return render(request, 'accounts/department_detail.html', context)

@login_required
def department_create(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, 'Department created successfully.')
            return redirect('accounts:department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'title': 'Create Department'
    }
    return render(request, 'accounts/department_form.html', context)

@login_required
def department_edit(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
        
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('accounts:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'title': 'Edit Department'
    }
    return render(request, 'accounts/department_form.html', context)

@login_required
def department_delete(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:index')
        
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        if department.userprofile_set.exists():
            messages.error(request, 'Cannot delete - this department has assigned staff.')
            return redirect('accounts:department_list')
            
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('accounts:department_list')
    
    context = {
        'department': department,
        'title': 'Delete Department'
    }
    return render(request, 'accounts/department_confirm_delete.html', context)

# Settings views
@login_required
def settings_home(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Get settings from database
    try:
        from .models import SystemSettings
        settings_obj = SystemSettings.get_settings()
    except Exception as e:
        settings_obj = None
    
    # Check database connection
    db_connected = True
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
    except:
        db_connected = False
    
    # Get application version from settings if available
    try:
        version = getattr(settings, 'APPLICATION_VERSION', 'Smart Clinic v1.0.0')
    except:
        version = 'Smart Clinic v1.0.0'
    
    # System information
    system_info = {
        'version': version,
        'db_connected': db_connected,
    }
    
    return render(request, 'accounts/settings/home.html', {
        'title': 'System Settings',
        'settings': settings_obj,
        'system_info': system_info,
    })

@login_required
def settings_general(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Implement settings form handling here
    
    return render(request, 'accounts/settings/general.html', {
        'title': 'General Settings',
    })

@login_required
def settings_appearance(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Get current settings from the database
    try:
        from .models import SystemSettings
        settings_obj = SystemSettings.get_settings()
    except:
        settings_obj = None
    
    if request.method == 'POST':
        # Handle form submission and save settings
        try:
            if settings_obj is None:
                from .models import SystemSettings
                settings_obj = SystemSettings()
            
            # Update settings from form data
            settings_obj.primary_color = request.POST.get('primary_color', '#3498db')
            settings_obj.secondary_color = request.POST.get('secondary_color', '#2ecc71')
            settings_obj.accent_color = request.POST.get('accent_color', '#9b59b6')
            settings_obj.enable_dark_mode = 'enable_dark_mode' in request.POST
            settings_obj.custom_css = request.POST.get('custom_css', '')
            
            # Handle logo upload
            if 'clinic_logo' in request.FILES:
                settings_obj.clinic_logo = request.FILES['clinic_logo']
                
            settings_obj.updated_by = request.user
            settings_obj.save()
            
            # Clear cache to ensure changes take effect immediately
            from django.core.cache import cache
            cache.delete('system_settings')
            
            messages.success(request, 'Appearance settings saved successfully!')
        except Exception as e:
            messages.error(request, f'Error saving settings: {str(e)}')
    
    return render(request, 'accounts/settings/appearance.html', {
        'title': 'Appearance Settings',
        'settings': settings_obj,
    })

@login_required
def settings_notifications(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Implement notification settings here
    
    return render(request, 'accounts/settings/notifications.html', {
        'title': 'Notification Settings',
    })

@login_required
def settings_security(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Get current settings
    try:
        from .models import SystemSettings
        settings_obj = SystemSettings.get_settings()
    except Exception as e:
        settings_obj = None
    
    if request.method == 'POST':
        try:
            if settings_obj is None:
                from .models import SystemSettings
                settings_obj = SystemSettings()
            
            # Update maintenance mode settings
            settings_obj.maintenance_mode = 'maintenance_mode' in request.POST
            settings_obj.maintenance_message = request.POST.get('maintenance_message', 
                "We're currently updating our system. Please check back later.")
            
            # Update password policy settings
            settings_obj.password_min_length = int(request.POST.get('password_min_length', 8))
            settings_obj.password_require_uppercase = 'password_require_uppercase' in request.POST
            settings_obj.password_require_special = 'password_require_special' in request.POST
            settings_obj.password_expiry_days = int(request.POST.get('password_expiry_days', 90))
            
            # Update session settings
            settings_obj.session_timeout_minutes = int(request.POST.get('session_timeout_minutes', 30))
            settings_obj.allow_remember_me = 'allow_remember_me' in request.POST
            
            # Save the settings
            settings_obj.updated_by = request.user
            settings_obj.save()
            
            # Clear cache
            from django.core.cache import cache
            cache.delete('system_settings')
            
            messages.success(request, 'Security settings saved successfully!')
            
        except Exception as e:
            messages.error(request, f'Error saving security settings: {str(e)}')
    
    return render(request, 'accounts/settings/security.html', {
        'title': 'Security Settings',
        'settings': settings_obj,
    })

@login_required
def settings_system_status(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Get system information
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'hostname': platform.node(),
        'processor': platform.processor(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': round(psutil.virtual_memory().total / (1024.0 ** 3), 2),  # GB
    }
    
    # Get database stats
    db_stats = {}
    with connection.cursor() as cursor:
        # Get table counts for main models
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('django.') or app_config.name == 'admin':
                continue
                
            for model in app_config.get_models():
                table_name = model._meta.db_table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row = cursor.fetchone()
                if row:
                    db_stats[model.__name__] = row[0]
    
    # Get recent errors from the Django error log (if available)
    error_log = []
    log_path = os.path.join(os.getcwd(), 'error.log')
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            error_log = [line.strip() for line in f.readlines()[-20:]]
    
    context = {
        'title': 'System Status',
        'system_info': system_info,
        'db_stats': db_stats,
        'error_log': error_log,
    }
    return render(request, 'accounts/settings/system_status.html', context)

@login_required
def settings_backups(request):
    """View for managing database backups"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access settings.')
        return redirect('dashboard:index')
    
    # Create backups directory if it doesn't exist
    backups_dir = os.path.join(settings.BASE_DIR, 'backups')
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
    
    # Get list of existing backups
    backups = []
    if os.path.exists(backups_dir):
        for filename in os.listdir(backups_dir):
            if filename.endswith('.json') or filename.endswith('.sql') or filename.endswith('.sqlite'):
                filepath = os.path.join(backups_dir, filename)
                backup_time = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                size_bytes = os.path.getsize(filepath)
                size_readable = "Unknown"
                
                # Format size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        size_readable = f"{size_bytes:.2f} {unit}"
                        break
                    size_bytes /= 1024.0
                
                backups.append({
                    'filename': filename,
                    'date': backup_time,
                    'size': size_readable
                })
    
    # Sort backups by date (newest first)
    backups.sort(key=lambda x: x['date'], reverse=True)
    
    # Get disk space info
    import shutil
    try:
        total, used, free = shutil.disk_usage(backups_dir)
        space_info = {
            'total': f"{total / (1024**3):.2f} GB",
            'used': f"{used / (1024**3):.2f} GB",
            'free': f"{free / (1024**3):.2f} GB",
            'percent_used': int(used * 100 / total)
        }
    except Exception:
        space_info = {
            'total': "Unknown",
            'used': "Unknown",
            'free': "Unknown",
            'percent_used': 0
        }
    
    return render(request, 'accounts/settings/backups.html', {
        'title': 'Database Backups',
        'backups': backups,
        'space_info': space_info,
        'next_scheduled': datetime.datetime.now() + datetime.timedelta(days=1)
    })

# API endpoints
@login_required
def system_metrics_api(request):
    """API endpoint for getting real-time system metrics"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    # Get CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Get network info
    net_io = psutil.net_io_counters()
    
    # Get process info
    current_process = psutil.Process(os.getpid())
    process_memory = current_process.memory_info().rss / (1024 * 1024)  # MB
    process_cpu = current_process.cpu_percent(interval=0.1)
    
    # Return metrics as JSON
    return JsonResponse({
        'timestamp': time.time(),
        'cpu': {
            'usage_percent': cpu_percent,
        },
        'memory': {
            'total': memory.total / (1024 ** 3),  # GB
            'available': memory.available / (1024 ** 3),  # GB
            'used': memory.used / (1024 ** 3),  # GB
            'percent': memory_percent,
        },
        'disk': {
            'total': disk.total / (1024 ** 3),  # GB
            'used': disk.used / (1024 ** 3),  # GB
            'free': disk.free / (1024 ** 3),  # GB
            'percent': disk_percent,
        },
        'network': {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
        },
        'process': {
            'memory_mb': process_memory,
            'cpu_percent': process_cpu,
        }
    })

@login_required
def debug_settings_api(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    debug_data = {
        'user': str(request.user),
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
    }
    
    try:
        from .models import SystemSettings
        settings_obj = SystemSettings.get_settings()
        
        # Add settings info
        debug_data['settings_found'] = True
        debug_data['settings_id'] = settings_obj.pk
        debug_data['maintenance_mode'] = settings_obj.maintenance_mode
        debug_data['password_min_length'] = settings_obj.password_min_length
        
        # Check middleware status
        debug_data['middleware'] = {
            'maintenance_middleware_active': 'accounts.middleware.MaintenanceModeMiddleware' in settings.MIDDLEWARE
        }
    except Exception as e:
        debug_data['settings_error'] = str(e)
    
    return JsonResponse(debug_data)

# Backup management views
@login_required
def create_backup(request):
    """Create a new database backup"""
    if not request.user.is_staff or request.method != 'POST':
        messages.error(request, 'Permission denied or invalid request method.')
        return redirect('accounts:settings_backups')
    
    try:
        import datetime, subprocess
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Determine backup type
        backup_type = request.POST.get('backup_type', 'json')
        
        # Create backup filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if backup_type == 'json':
            filename = f"backup_{timestamp}.json"
            filepath = os.path.join(backup_dir, filename)
            
            # Use Django's dumpdata management command
            with open(filepath, 'w') as f:
                # Exclude contenttypes to avoid problems on restore
                subprocess.run(
                    [
                        'python', 'manage.py', 'dumpdata',
                        '--exclude', 'contenttypes',
                        '--exclude', 'auth.permission',
                        '--indent', '2'
                    ],
                    stdout=f,
                    check=True
                )
        else:
            # SQL backup (we'll just create a JSON backup for now)
            filename = f"backup_{timestamp}.json"
            filepath = os.path.join(backup_dir, filename)
            
            # Use Django's dumpdata management command
            with open(filepath, 'w') as f:
                subprocess.run(
                    [
                        'python', 'manage.py', 'dumpdata',
                        '--exclude', 'contenttypes',
                        '--exclude', 'auth.permission',
                        '--indent', '2'
                    ],
                    stdout=f,
                    check=True
                )
        
        messages.success(request, f'Backup created successfully: {filename}')
    except Exception as e:
        messages.error(request, f'Error creating backup: {str(e)}')
    
    return redirect('accounts:settings_backups')

@login_required
def download_backup(request, filename):
    """Download a backup file"""
    if not request.user.is_staff:
        messages.error(request, 'Permission denied.')
        return redirect('accounts:settings_backups')
    
    from django.http import FileResponse, Http404
    
    filepath = os.path.join(settings.BASE_DIR, 'backups', filename)
    if not os.path.exists(filepath):
        raise Http404("Backup file not found.")
    
    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filename)

@login_required
def restore_backup(request, filename):
    """Restore a database from backup"""
    if not request.user.is_staff or request.method != 'POST':
        messages.error(request, 'Permission denied or invalid request method.')
        return redirect('accounts:settings_backups')
    
    try:
        import subprocess
        
        filepath = os.path.join(settings.BASE_DIR, 'backups', filename)
        if not os.path.exists(filepath):
            messages.error(request, f'Backup file not found: {filename}')
            return redirect('accounts:settings_backups')
        
        # Use Django's loaddata command
        subprocess.run(['python', 'manage.py', 'loaddata', filepath], check=True)
        
        messages.success(request, f'Backup restored successfully: {filename}')
    except Exception as e:
        messages.error(request, f'Error restoring backup: {str(e)}')
    
    return redirect('accounts:settings_backups')

@login_required
def delete_backup(request, filename):
    """Delete a backup file"""
    if not request.user.is_staff or request.method != 'POST':
        messages.error(request, 'Permission denied or invalid request method.')
        return redirect('accounts:settings_backups')
    
    try:
        filepath = os.path.join(settings.BASE_DIR, 'backups', filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            messages.success(request, f'Backup deleted: {filename}')
        else:
            messages.warning(request, f'Backup file not found: {filename}')
    except Exception as e:
        messages.error(request, f'Error deleting backup: {str(e)}')
    
    return redirect('accounts:settings_backups')

@login_required
def doctor_create(request):
    """View for creating new doctor accounts"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to create doctor accounts.')
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        # Use our custom DoctorCreationForm instead of UserCreationForm
        user_form = DoctorCreationForm(request.POST)
        profile_form = DoctorProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Create the user with first name, last name and email included
            user = user_form.save()
            
            # Update the profile
            profile = user.profile
            profile.role = 'doctor'
            profile.department_id = profile_form.cleaned_data['department'].id
            profile.specialization = profile_form.cleaned_data['specialization']
            profile.phone = profile_form.cleaned_data['phone']
            profile.address = profile_form.cleaned_data['address']
            profile.bio = profile_form.cleaned_data['bio']
            
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
                
            profile.save()
            
            messages.success(request, 'Doctor created successfully.')
            return redirect('accounts:department_list')
    else:
        user_form = DoctorCreationForm()
        profile_form = DoctorProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Add New Doctor'
    }
    return render(request, 'accounts/doctor_form.html', context)

def contact_us(request):
    """View for the contact us page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Process the form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Here you would typically send an email
            # For now, we'll just show a success message
            try:
                # Optional: Save the contact message to the database
                # ContactMessage.objects.create(
                #     name=name,
                #     email=email,
                #     subject=subject,
                #     message=message
                # )
                
                messages.success(request, 'Your message has been sent. We will contact you shortly.')
                return redirect('contact_us')
            except Exception as e:
                messages.error(request, f'There was an error sending your message: {str(e)}')
    else:
        # Pre-fill user information if logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name(),
                'email': request.user.email
            }
        form = ContactForm(initial=initial_data)
    
    return render(request, 'pages/contact_us.html', {
        'form': form,
        'title': 'Contact Us'
    })

def services(request):
    """View for the services page"""
    # Get all active services if you have a Service model
    # services = Service.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'pages/services.html', {
        'title': 'Our Services'
    })

def faq(request):
    """View for the frequently asked questions page"""
    # If you have an FAQ model, you could fetch questions and answers here
    # faqs = FAQ.objects.filter(is_active=True).order_by('order')
    
    return render(request, 'pages/faq.html', {
        'title': 'Frequently Asked Questions'
    })

@login_required
def patient_health_tracker(request):
    """View for patient health tracking dashboard"""
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    # Add any data retrieval logic here
    
    return render(request, 'accounts/patient_health_tracker.html', {
        'title': 'Health Tracker'
    })

@login_required
def patient_document_upload(request):
    """View for patient document upload"""
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    # Add any document handling logic here
    
    return render(request, 'accounts/patient_document_upload.html', {
        'title': 'Document Upload'
    })

@login_required
def patient_video_consultation(request):
    """View for patient video consultations"""
    if request.user.profile.role != 'patient':
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('dashboard:index')
    
    try:
        # Get the patient record
        patient = Patient.objects.get(email=request.user.email)
        
        # Get appointment data with video consultation type
        from appointments.models import Appointment
        from django.utils import timezone
        
        today = timezone.now().date()
        current_time = timezone.now().time()
        
        # Get active consultation (happening now)
        active_consultation = Appointment.objects.filter(
            patient=patient,
            date=today,
            start_time__lte=current_time,
            end_time__gte=current_time,
            appointment_type__name="Video Consultation",
            status='confirmed'
        ).first()
        
        # Get upcoming video consultations
        upcoming_consultations = Appointment.objects.filter(
            patient=patient,
            date__gte=today,
            appointment_type__name="Video Consultation",
            status__in=['scheduled', 'confirmed']
        ).exclude(id=active_consultation.id if active_consultation else 0).order_by('date', 'start_time')
        
        # Get past video consultations
        past_consultations = Appointment.objects.filter(
            patient=patient,
            appointment_type__name="Video Consultation",
            status='completed'
        ).order_by('-date', '-start_time')[:5]
        
        # Check if any upcoming consultation is within 15 minutes of starting
        is_within_15_minutes = False
        if upcoming_consultations:
            next_consultation = upcoming_consultations.first()
            if next_consultation.date == today:
                consultation_start = timezone.datetime.combine(
                    today,
                    next_consultation.start_time
                )
                consultation_start = timezone.make_aware(consultation_start)
                
                time_until_start = (consultation_start - timezone.now()).total_seconds() / 60
                is_within_15_minutes = time_until_start <= 15
        
        return render(request, 'accounts/patient_video_consultation.html', {
            'active_consultation': active_consultation,
            'upcoming_consultations': upcoming_consultations,
            'past_consultations': past_consultations,
            'is_within_15_minutes': is_within_15_minutes,
            'title': 'Video Consultation'
        })
        
    except Patient.DoesNotExist:
        messages.error(request, 'Please complete your patient profile first.')
        return redirect('accounts:patient_profile_update')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('dashboard:index')
