from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Patient, MedicalRecord, Prescription
from .forms import PatientForm, MedicalRecordForm, PrescriptionForm

@login_required
def patient_list(request):
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    else:
        patients = Patient.objects.all().order_by('last_name', 'first_name')
    
    # Paginate the results
    paginator = Paginator(patients, 10)
    page_number = request.GET.get('page', 1)
    patients_page = paginator.get_page(page_number)
    
    context = {
        'patients': patients_page,
        'search_query': search_query,
        'title': 'Patients'
    }
    return render(request, 'patients/patient_list.html', context)

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    medical_records = patient.medical_records.all().order_by('-date')
    prescriptions = patient.prescriptions.all().order_by('-start_date')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'prescriptions': prescriptions,
        'title': f'Patient: {patient}'
    }
    return render(request, 'patients/patient_detail.html', context)

@login_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, 'Patient created successfully.')
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientForm()
    
    context = {
        'form': form,
        'title': 'Register New Patient'
    }
    return render(request, 'patients/patient_form.html', context)

@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully.')
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    context = {
        'form': form,
        'patient': patient,
        'title': 'Edit Patient'
    }
    return render(request, 'patients/patient_form.html', context)

@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        patient.delete()
        messages.success(request, 'Patient record deleted successfully.')
        return redirect('patients:list')
    
    context = {
        'patient': patient,
        'title': 'Delete Patient'
    }
    return render(request, 'patients/patient_confirm_delete.html', context)

# Medical Record views
@login_required
def medical_record_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.profile.role == 'doctor'):
        messages.error(request, 'You do not have permission to create medical records.')
        return redirect('patients:detail', pk=patient_id)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = patient
            medical_record.doctor = request.user.profile
            medical_record.save()
            messages.success(request, 'Medical record created successfully.')
            return redirect('patients:detail', pk=patient_id)  # Fixed URL name
    else:
        form = MedicalRecordForm()
    
    return render(request, 'patients/medical_record_form.html', {
        'form': form,
        'patient': patient,
        'title': f'Create Medical Record for {patient}'
    })

@login_required
def medical_record_edit(request, pk):
    medical_record = get_object_or_404(MedicalRecord, pk=pk)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=medical_record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medical record updated successfully.')
            return redirect('patients:detail', pk=medical_record.patient.pk)
    else:
        form = MedicalRecordForm(instance=medical_record)
    
    context = {
        'form': form,
        'medical_record': medical_record,
        'patient': medical_record.patient,
        'title': 'Edit Medical Record'
    }
    return render(request, 'patients/medical_record_form.html', context)

@login_required
def medical_record_delete(request, pk):
    medical_record = get_object_or_404(MedicalRecord, pk=pk)
    patient_id = medical_record.patient.pk
    
    if request.method == 'POST':
        medical_record.delete()
        messages.success(request, 'Medical record deleted successfully.')
        return redirect('patients:detail', pk=patient_id)
    
    context = {
        'medical_record': medical_record,
        'patient': medical_record.patient,
        'title': 'Delete Medical Record'
    }
    return render(request, 'patients/medical_record_confirm_delete.html', context)

# Prescription views
@login_required
def prescription_create(request, patient_id=None, medical_record_id=None):
    patient = None
    medical_record = None
    
    if patient_id:
        patient = get_object_or_404(Patient, pk=patient_id)
    
    if medical_record_id:
        medical_record = get_object_or_404(MedicalRecord, pk=medical_record_id)
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, patient_id=patient_id, medical_record_id=medical_record_id)
        if form.is_valid():
            prescription = form.save()
            messages.success(request, 'Prescription created successfully.')
            return redirect('patients:detail', pk=prescription.patient.pk)
    else:
        form = PrescriptionForm(patient_id=patient_id, medical_record_id=medical_record_id)
    
    context = {
        'form': form,
        'patient': patient,
        'medical_record': medical_record,
        'title': 'Add Prescription'
    }
    return render(request, 'patients/prescription_form.html', context)

@login_required
def prescription_edit(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription updated successfully.')
            return redirect('patients:detail', pk=prescription.patient.pk)
    else:
        form = PrescriptionForm(instance=prescription)
    
    context = {
        'form': form,
        'prescription': prescription,
        'patient': prescription.patient,
        'title': 'Edit Prescription'
    }
    return render(request, 'patients/prescription_form.html', context)

@login_required
def prescription_delete(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    patient_id = prescription.patient.pk
    
    if request.method == 'POST':
        prescription.delete()
        messages.success(request, 'Prescription deleted successfully.')
        return redirect('patients:detail', pk=patient_id)
    
    context = {
        'prescription': prescription,
        'patient': prescription.patient,
        'title': 'Delete Prescription'
    }
    return render(request, 'patients/prescription_confirm_delete.html', context)
