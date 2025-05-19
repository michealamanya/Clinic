from django import forms
from .models import Patient, MedicalRecord, Prescription

class PatientForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'email', 
                 'phone', 'address', 'blood_type', 'emergency_contact_name', 
                 'emergency_contact_phone', 'insurance_provider', 'insurance_policy_number']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })

class MedicalRecordForm(forms.ModelForm):
    follow_up_required = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = MedicalRecord
        # Updating fields to match what's actually in the MedicalRecord model
        # Removed 'symptoms' if it doesn't exist in the model
        fields = ['date', 'diagnosis', 'treatment', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'treatment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Handle the initial value for follow_up_required properly
        # This prevents the KeyError
        instance = kwargs.get('instance')
        if instance:
            # If editing an existing record, get the field value from the instance
            self.initial['follow_up_required'] = getattr(instance, 'follow_up_required', False)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })
            
        self.fields['follow_up_required'].widget.attrs.update({
            'class': 'form-check-input',
            'style': 'margin-right: 10px;'
        })

class PrescriptionForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    class Meta:
        model = Prescription
        fields = ['patient', 'medical_record', 'medication_name', 'dosage', 
                 'frequency', 'start_date', 'end_date', 'instructions']
        
    def __init__(self, *args, **kwargs):
        patient_id = kwargs.pop('patient_id', None)
        medical_record_id = kwargs.pop('medical_record_id', None)
        super().__init__(*args, **kwargs)
        
        if patient_id:
            self.fields['patient'].initial = patient_id
            self.fields['patient'].widget = forms.HiddenInput()
            
            if medical_record_id:
                self.fields['medical_record'].initial = medical_record_id
                self.fields['medical_record'].queryset = MedicalRecord.objects.filter(patient_id=patient_id)
            else:
                self.fields['medical_record'].queryset = MedicalRecord.objects.filter(patient_id=patient_id)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })
