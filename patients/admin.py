from django.contrib import admin
from .models import Patient, MedicalRecord, Prescription

class MedicalRecordInline(admin.TabularInline):
    model = MedicalRecord
    extra = 0
    fields = ('date', 'diagnosis', 'treatment', 'follow_up_required', 'follow_up_date')
    
class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0
    fields = ('medication_name', 'dosage', 'frequency', 'start_date', 'end_date')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'date_of_birth', 'gender', 'phone', 'get_age')
    list_filter = ('gender', 'blood_type')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'address')
    date_hierarchy = 'date_of_birth'
    inlines = [MedicalRecordInline, PrescriptionInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'blood_type')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Insurance Details', {
            'fields': ('insurance_provider', 'insurance_policy_number'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date', 'diagnosis', 'follow_up_required', 'follow_up_date')
    list_filter = ('follow_up_required', 'date')
    search_fields = ('patient__first_name', 'patient__last_name', 'diagnosis', 'treatment', 'notes')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Medical Details', {
            'fields': ('date', 'diagnosis', 'treatment', 'notes')
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_date')
        }),
    )

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medication_name', 'dosage', 'frequency', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'medication_name', 'instructions')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Patient', {
            'fields': ('patient', 'medical_record')
        }),
        ('Medication', {
            'fields': ('medication_name', 'dosage', 'frequency', 'instructions')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
    )
