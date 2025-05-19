from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Appointment, AppointmentType
from .forms import AppointmentForm, AppointmentTypeForm, AppointmentCompleteForm, AppointmentRescheduleForm

@login_required
def appointment_list(request):
    appointments = Appointment.objects.all().order_by('date', 'start_time')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Paginate the results
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page', 1)
    appointments_page = paginator.get_page(page_number)
    
    context = {
        'appointments': appointments_page,
        'status_choices': Appointment.STATUS_CHOICES,
        'selected_status': status_filter,
        'title': 'Appointments'
    }
    return render(request, 'appointments/appointment_list.html', context)

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    context = {
        'appointment': appointment,
        'title': f'Appointment: {appointment}'
    }
    return render(request, 'appointments/appointment_detail.html', context)

@login_required
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, 'Appointment created successfully.')
            return redirect('appointments:detail', pk=appointment.pk)
    else:
        # Pre-fill with patient_id if provided
        patient_id = request.GET.get('patient_id')
        initial_data = {}
        if patient_id:
            initial_data['patient'] = patient_id
        
        form = AppointmentForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Create Appointment'
    }
    return render(request, 'appointments/appointment_form.html', context)

@login_required
def appointment_edit(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or request.user.profile.role == 'doctor' or 
            (hasattr(appointment.patient, 'user') and appointment.patient.user == request.user)):
        messages.error(request, 'You do not have permission to edit this appointment.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully.')
            return redirect('appointments:detail', pk=appointment.pk)
    else:
        form = AppointmentForm(instance=appointment)
    
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'appointment': appointment,
        'title': 'Edit Appointment'
    })

@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or request.user.profile.role == 'doctor'):
        messages.error(request, 'You do not have permission to delete this appointment.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        # Store info for message
        appointment_info = f"Appointment for {appointment.patient} on {appointment.date}"
        
        # Delete appointment
        appointment.delete()
        
        messages.success(request, f'{appointment_info} has been deleted.')
        return redirect('appointments:list')
    
    return render(request, 'appointments/appointment_confirm_delete.html', {
        'appointment': appointment,
        'title': 'Delete Appointment'
    })

@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or 
            request.user.profile.role == 'doctor' or 
            (hasattr(appointment.patient, 'user') and appointment.patient.user == request.user)):
        messages.error(request, 'You do not have permission to cancel this appointment.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointments:list')
    
    return render(request, 'appointments/appointment_cancel.html', {
        'appointment': appointment,
        'title': 'Cancel Appointment'
    })

@login_required
def appointment_complete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Only staff and doctors can mark appointments as completed
    if not (request.user.is_staff or request.user.profile.role == 'doctor'):
        messages.error(request, 'You do not have permission to complete this appointment.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = AppointmentCompleteForm(request.POST)
        if form.is_valid():
            appointment.status = 'completed'
            appointment.notes = form.cleaned_data.get('notes', '')
            appointment.save()
            
            messages.success(request, 'Appointment marked as completed.')
            return redirect('appointments:detail', pk=appointment.pk)
    else:
        form = AppointmentCompleteForm()
    
    return render(request, 'appointments/appointment_complete.html', {
        'form': form,
        'appointment': appointment,
        'title': 'Complete Appointment'
    })

@login_required
def appointment_reschedule(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user.is_staff or request.user.profile.role == 'doctor'):
        messages.error(request, 'You do not have permission to reschedule this appointment.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = AppointmentRescheduleForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.save()
            
            messages.success(request, 'Appointment rescheduled successfully.')
            return redirect('appointments:detail', pk=appointment.pk)
    else:
        form = AppointmentRescheduleForm(instance=appointment)
    
    return render(request, 'appointments/appointment_reschedule.html', {
        'form': form,
        'appointment': appointment,
        'title': 'Reschedule Appointment'
    })

# Views for AppointmentType
@login_required
def appointment_type_list(request):
    appointment_types = AppointmentType.objects.all().order_by('name')
    context = {
        'appointment_types': appointment_types,
        'title': 'Appointment Types'
    }
    return render(request, 'appointments/appointment_type_list.html', context)

@login_required
def appointment_type_create(request):
    if request.method == 'POST':
        form = AppointmentTypeForm(request.POST)
        if form.is_valid():
            appointment_type = form.save()
            messages.success(request, 'Appointment Type created successfully.')
            return redirect('appointments:type_list')
    else:
        form = AppointmentTypeForm()
    
    context = {
        'form': form,
        'title': 'Create Appointment Type'
    }
    return render(request, 'appointments/appointment_type_form.html', context)

@login_required
def appointment_type_edit(request, pk):
    appointment_type = get_object_or_404(AppointmentType, pk=pk)
    
    if request.method == 'POST':
        form = AppointmentTypeForm(request.POST, instance=appointment_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment Type updated successfully.')
            return redirect('appointments:type_list')
    else:
        form = AppointmentTypeForm(instance=appointment_type)
    
    context = {
        'form': form,
        'appointment_type': appointment_type,
        'title': 'Edit Appointment Type'
    }
    return render(request, 'appointments/appointment_type_form.html', context)

@login_required
def appointment_type_delete(request, pk):
    appointment_type = get_object_or_404(AppointmentType, pk=pk)
    
    if request.method == 'POST':
        if appointment_type.appointments.exists():
            messages.error(request, 'Cannot delete - this appointment type is in use.')
            return redirect('appointments:type_list')
        
        appointment_type.delete()
        messages.success(request, 'Appointment Type deleted successfully.')
        return redirect('appointments:type_list')
    
    context = {
        'appointment_type': appointment_type,
        'title': 'Delete Appointment Type'
    }
    return render(request, 'appointments/appointment_type_confirm_delete.html', context)
