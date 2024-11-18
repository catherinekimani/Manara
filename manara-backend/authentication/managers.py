# Imports
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
  def create_user(self, email,phone_number, password, **extra_fields):
    if not email:
      raise ValueError(_('The Email field must be set'))
    if not phone_number:
      raise ValueError(_('The Phone Number field must be set'))
    
    email = self.normalize_email(email)
    user = self.model(email=email, phone_number=phone_number, **extra_fields)
    user.set_password(password)
    user.save()
    return user
  
  def create_superuser(self, email, phone_number, password, **extra_fields):
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)
    extra_fields.setdefault('is_active', True)
    extra_fields.setdefault('is_verified', True)
    
    if extra_fields.get('is_staff') is not True:
        raise ValueError(_('Superuser must have is_staff=True.'))
    if extra_fields.get('is_superuser') is not True:
        raise ValueError(_('Superuser must have is_superuser=True.'))
        
    return self.create_user(email, phone_number, password, **extra_fields)