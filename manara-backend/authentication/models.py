# Django imports
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Third-party imports
from phonenumber_field.modelfields import PhoneNumberField

from .managers import CustomUserManager
class User(AbstractBaseUser, PermissionsMixin):
  class UserType(models.TextChoices):
    COMMUTER = 'COMMUTER', _('Commuter')
    SACCO_OWNER = 'SACCO_OWNER', _('Sacco Owner')
    OPERATOR = 'OPERATOR', _('Operator')
    
  email = models.EmailField(_('email address'), unique=True)
  phone_number = PhoneNumberField(_('phone number'), unique=True)
  full_name = models.CharField(_('full name'), max_length=255)
  user_type = models.CharField(_('user type'), max_length=20, choices=UserType.choices, default=UserType.COMMUTER)
  
  is_staff = models.BooleanField(default=False)
  is_active = models.BooleanField(default=True)
  is_verified = models.BooleanField(default=False)
  date_joined = models.DateTimeField(default=timezone.now)
  
  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['full_name', 'phone_number', 'user_type']
  
  objects = CustomUserManager()
  
  class Meta:
    verbose_name = _('user')
    verbose_name_plural = _('users')
  
  def __str__(self):
    return self.email
  
  def get_full_name(self):
    return self.full_name


class OTPCode(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
  code = models.CharField(max_length=6)
  is_used = models.BooleanField(default=False)
  created_at = models.DateTimeField(auto_now_add=True)
  expires_at = models.DateTimeField()
  
  class Meta:
    verbose_name = _('OTP code')
    verbose_name_plural = _('OTP codes')
  
  def __str__(self):
    return f'OTP code for {self.user.email}'
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"

# Location
class Location(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

# Route
class Route(models.Model):
    name = models.CharField(max_length=255)
    start_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='route_starts')
    end_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='route_ends')
    estimated_duration = models.IntegerField(help_text="Duration in mins")
    is_saved = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.start_location} to {self.end_location}"

# Trip
class Trip(models.Model):
    class TripStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', _('Scheduled')
        ONGOING = 'ONGOING', _('Ongoing')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=TripStatus.choices, default=TripStatus.SCHEDULED)
    scheduled_time = models.DateTimeField()
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)
    actual_arrival_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user}'s trip to {self.route.end_location}"

# stops
class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    sequence = models.IntegerField()
    estimated_time = models.IntegerField(help_text="Time in mins from start")
    
    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"Stop {self.sequence} on {self.route}"
