from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserCafe, Camera, Seat, Report, Customer, SeatDetection, EmailOTP, Floor, ActivityLog, EntryEvent

# If you use a custom User model:
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password', 'phone_number')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )
admin.site.register(User, UserAdmin)
admin.site.register(UserCafe)
admin.site.register(Camera)
admin.site.register(Seat)
admin.site.register(Report)
admin.site.register(Customer)
admin.site.register(SeatDetection)
admin.site.register(EmailOTP)
admin.site.register(Floor)
admin.site.register(ActivityLog)
admin.site.register(EntryEvent)

# Register your models here.
