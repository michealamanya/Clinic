from django.contrib import admin
from .models import Appointment, AppointmentType

@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'color_code')
    search_fields = ('name', 'description')
    list_filter = ('duration',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__user__first_name', 'doctor__user__last_name', 'notes')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'appointment_type')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If not superuser, filter to see only appointments related to the logged-in doctor
        if request.user.is_superuser:
            return qs
        return qs.filter(doctor__user=request.user)
