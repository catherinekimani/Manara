from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, OTPCode

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
  list_display = ('email', 'phone_number', 'full_name', 'user_type', 'is_active', 'is_verified')
  list_filter = ('is_active', 'is_verified', 'user_type', 'is_staff')
  search_fields = ('email', 'phone_number', 'full_name')
  ordering = ('email',)
  
  fieldsets = (
    (None, {'fields': ('email', 'password')}),
    (_('Personal info'), {'fields': ('full_name', 'phone_number', 'user_type')}),
    (_('Permissions'), {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
  add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('email', 'phone_number', 'full_name', 'user_type', 'password1', 'password2'),
    }),
  )

@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__phone_number')