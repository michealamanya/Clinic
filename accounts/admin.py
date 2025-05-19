from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Department, Schedule

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'department', 'specialization', 'phone', 'address', 'bio', 'profile_picture', 'is_active')

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'profile__role')
    
    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '-'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 0
    fields = ('day_of_week', 'start_time', 'end_time', 'is_working')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_extension', 'is_active')
    search_fields = ('name', 'description', 'phone_extension')
    list_filter = ('is_active',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'specialization', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    inlines = [ScheduleInline]
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Role Information', {
            'fields': ('role', 'department', 'specialization')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Additional Information', {
            'fields': ('bio', 'profile_picture', 'is_active')
        }),
    )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
