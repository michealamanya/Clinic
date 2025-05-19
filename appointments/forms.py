from django import forms
from .models import Appointment, AppointmentType
from patients.models import Patient
from accounts.models import UserProfile

class AppointmentForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_type', 'date', 'start_time', 'end_time', 'status', 'notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = UserProfile.objects.filter(role='doctor', is_active=True)
        self.fields['patient'].queryset = Patient.objects.all().order_by('last_name', 'first_name')
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })

class AppointmentTypeForm(forms.ModelForm):
    color_code = forms.CharField(
        widget=forms.TextInput(attrs={'type': 'color'})
    )
    
    class Meta:
        model = AppointmentType
        fields = ['name', 'description', 'duration', 'color_code']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })

class AppointmentCompleteForm(forms.Form):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        required=False
    )

class AppointmentRescheduleForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
