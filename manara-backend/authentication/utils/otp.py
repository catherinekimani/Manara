# Standard lib imports
import logging
import random
from datetime import timedelta

# Django imports
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

# Third-party imports
import pyotp
from twilio.rest import Client

from ..models import OTPCode


logger = logging.getLogger(__name__)

class OTPManager:
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    @staticmethod
    def create_otp(user):
        """Create and save OTP for a user"""
        try:

            OTPCode.objects.filter(
                user=user,
                is_used=False,
                expires_at__gt=timezone.now()
            ).update(expires_at=timezone.now())
            
            otp_code = OTPManager.generate_otp()
            logger.info(f"Generated OTP: {otp_code}")
            expires_at = timezone.now() + timedelta(minutes=10)
            
            otp = OTPCode.objects.create(
                user=user,
                code=otp_code,
                expires_at=expires_at
            )
            
            if OTPManager.send_otp(user, otp_code):
                logger.info(f"OTP created and sent successfully for user {user.email}")
                return otp
            else:
                logger.error(f"OTP created but sending failed for user {user.email}")
                otp.delete()
                return None
                
        except Exception as e:
            logger.error(f"Error creating OTP: {e}")
            return None
    
    @staticmethod
    def verify_otp(user, code):
        """Verify OTP code for user"""
        try:
            otp = OTPCode.objects.filter(
                user=user,
                code=code,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            
            if not otp:
                logger.warning(f"Invalid or expired OTP attempt for user {user.email}")
                return False
                
            otp.is_used = True
            otp.save()
            
            logger.info(f"OTP verified successfully for user {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False
    
    @staticmethod
    def send_otp(user, otp_code):
        """Send OTP via SMS with email fallback"""
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            try:
                message = client.messages.create(
                    body=f"Your verification code is: {otp_code}. Valid for 10 minutes.",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=str(user.phone_number)
                )
                logger.info(f"OTP sent successfully via SMS to {user.phone_number}")
                return True
            except Exception as sms_error:
                logger.warning(f"SMS failed, attempting email: {str(sms_error)}")
                
                if user.email:
                    send_mail(
                        'Your OTP Code',
                        f'Your verification code is: {otp_code}. Valid for 10 minutes.',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    logger.info(f"OTP sent successfully via email to {user.email}")
                    return True
                else:
                    raise Exception("Both SMS and email delivery failed")
                    
        except Exception as e:
            logger.error(f"Failed to send OTP: {str(e)}")
            return False


    @staticmethod
    def cleanup_old_otps():
        """Clean up expired and used OTPs"""
        try:
            deleted, _ = OTPCode.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
            logger.info(f"Cleaned up {deleted} expired OTP codes")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up old OTPs: {e}")
            return 0