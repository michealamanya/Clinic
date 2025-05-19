from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Department, Schedule
from patients.models import Patient

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'department', 'specialization', 'phone', 'address', 'bio', 'profile_picture']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'phone_extension', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })
            
        self.fields['is_active'].widget.attrs.update({
            'class': 'form-check-input',
            'style': 'margin-right: 10px;'
        })

class ScheduleForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    class Meta:
        model = Schedule
        fields = ['staff', 'day_of_week', 'start_time', 'end_time', 'is_working']
        
    def __init__(self, *args, **kwargs):
        staff_id = kwargs.pop('staff_id', None)
        super().__init__(*args, **kwargs)
        
        if staff_id:
            self.fields['staff'].initial = staff_id
            self.fields['staff'].widget = forms.HiddenInput()
        
        # Apply custom styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'style': 'border-radius: 8px; border: 1px solid #ddd;'
            })
            
        self.fields['is_working'].widget.attrs.update({
            'class': 'form-check-input',
            'style': 'margin-right: 10px;'
        })

class PatientProfileForm(forms.ModelForm):
    """Form for patients to update their profile information"""
    
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

class ContactForm(forms.Form):
    """Form for contact page messages"""
    
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'style': 'border-radius: 8px; border: 1px solid #ddd;',
        'placeholder': 'Your Name'
    }))
    
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'style': 'border-radius: 8px; border: 1px solid #ddd;',
        'placeholder': 'Your Email'
    }))
    
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'style': 'border-radius: 8px; border: 1px solid #ddd;',
        'placeholder': 'Subject'
    }))
    
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'style': 'border-radius: 8px; border: 1px solid #ddd;',
        'placeholder': 'Your Message',
        'rows': 5
    }))

class DoctorCreationForm(UserCreationForm):
    """Extended user creation form that includes first_name, last_name and email"""
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=254, 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class DoctorProfileForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = ['department', 'specialization', 'phone', 'address', 'bio', 'profile_picture']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
