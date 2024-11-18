# Django imports
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.views import View

# Django REST framework imports
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

# Simple JWT imports
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Logging
import logging

# Local imports
from .utils.otp import OTPManager
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    RequestOTPSerializer,
    VerifyOTPSerializer,
    UserProfileUpdateSerializer,
    UserProfileSerializer,
    TripSerializer,
    RouteSerializer
)
from .models import UserProfile, Route, Trip

User = get_user_model()

class HomePageView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Welcome to the API Home Page!")

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        user.is_verified = False
        user.save()
        
        return Response({
            'user': serializer.data,
            'message': 'User registered successfully. Please verify your OTP.'
        }, status=status.HTTP_201_CREATED)
class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        
        if not user.is_verified:
            return Response(
                {"error": "Account not verified. Please verify OTP."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().post(request, *args, **kwargs)

logger = logging.getLogger(__name__)
class RequestOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RequestOTPSerializer

    @swagger_auto_schema(request_body=RequestOTPSerializer)
    def post(self, request):
        try:
            logger.debug("Received request data: %s", request.data)
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data.get('email')
            phone_number = serializer.validated_data.get('phone_number')

            identifier = str(email or phone_number)
            cache_key = f'otp_request_{identifier}'

            if cache.get(cache_key):
                logger.debug(f"Cache hit for {cache_key}, waiting 60 seconds")
                return Response({
                    "error": "Please wait before requesting another OTP.",
                    "wait_time": "60 seconds"
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            logger.debug(f"User lookup for email: {email} or phone_number: {phone_number}")
            user = None
            if email:
                user = User.objects.filter(email=email).first()
            elif phone_number:
                user = User.objects.filter(phone_number=phone_number).first()

            if not user:
                logger.debug("User not found")
                return Response({"error": "User not found. Please register."}, status=status.HTTP_404_NOT_FOUND)

            otp = OTPManager.create_otp(user)
            if not otp:
                logger.debug("Failed to create OTP")
                return Response({"error": "Failed to send OTP. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            cache.set(cache_key, True, 60)

            return Response({
                "message": "OTP sent successfully",
                "expires_in": "10 minutes",
                "contact": email or str(phone_number),
                "delivery_method": "email" if email else "sms"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in RequestOTPView: {str(e)}")
            return Response({
                "error": "An unexpected error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer
    max_attempts = 3
    
    @swagger_auto_schema(request_body=VerifyOTPSerializer)
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            email = serializer.validated_data.get('email')
            phone_number = serializer.validated_data.get('phone_number')
            code = serializer.validated_data['code']
            
            identifier = str(email or phone_number)
            attempt_key = f'otp_attempts_{identifier}'
            attempts = cache.get(attempt_key, 0)
            
            if attempts >= self.max_attempts:
                return Response({
                    "error": "Too many failed attempts. Please request a new OTP.",
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            user = None
            if email:
                user = User.objects.filter(email=email).first()
            elif phone_number:
                user = User.objects.filter(phone_number=phone_number).first()

            if not user:
                return Response({
                    "error": "User not found."
                }, status=status.HTTP_404_NOT_FOUND)

            if OTPManager.verify_otp(user, code):
                user.is_verified = True
                user.save()
                
                cache.delete(attempt_key)
                
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    "message": "OTP verified successfully",
                    "is_verified": True,
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh)
                    }
                }, status=status.HTTP_200_OK)
            
            cache.set(attempt_key, attempts + 1, 300)
            
            return Response({
                "error": "Invalid or expired OTP.",
                "attempts_left": self.max_attempts - (attempts + 1)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error in VerifyOTPView: {str(e)}")
            return Response({
                "error": "An unexpected error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpt for retrieving & updating user profiles.
    Requires authentication & sends OTP for verification on updates.
    """
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'first_name': '',
                'last_name': '',
                'phone_number': ''
            }
        )
        return profile

    def get_serializer_class(self):
        """
        Return serializer class based on the HTTP method.
        """
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserProfileUpdateSerializer

    def update(self, request, *args, **kwargs):
        """
        Handle profile updates & trigger OTP verification
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        has_changes = False
        for field in ['first_name', 'last_name', 'phone_number']:
            if field in serializer.validated_data:
                if getattr(instance, field) != serializer.validated_data[field]:
                    has_changes = True
                    break

        if has_changes:
            cache_key = f"profile_update_{request.user.id}"
            cache.set(cache_key, serializer.validated_data, timeout=300)

            try:
                otp = OTPManager.create_otp(request.user)
                contact = serializer.validated_data.get('phone_number', instance.phone_number)
                return Response({
                    'message': 'Please verify OTP to update profile',
                    'verification_required': True
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': 'Failed to send OTP',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.perform_update(serializer)
        return Response(serializer.data)

class VerifyProfileUpdateOTPView(generics.GenericAPIView):
    """
    Verify OTP & complete profile update
    """
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cache_key = f"profile_update_{request.user.id}"
        profile_data = cache.get(cache_key)

        if not profile_data:
            return Response({
                'error': 'Profile update session expired'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not OTPManager.verify_otp(request.user, serializer.validated_data['code']):
            return Response({
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)

        profile = request.user.profile
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.is_verified = True
        profile.save()

        cache.delete(cache_key)

        return Response({
            'message': 'Profile updated successfully',
            'profile': UserProfileUpdateSerializer(profile).data
        })

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.is_active = False
        user.save()
        return Response({"message": "Account successfully deleted."}, status=status.HTTP_204_NO_CONTENT)

class TripListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing & creating trips
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Override this method to associate the user with the trip when it is created.
        """
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Create a new trip",
        responses={201: TripSerializer()}
    )
    def post(self, request, *args, **kwargs):
        try:
            logger.debug("Creating new trip with data: %s", request.data)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'trip': serializer.data,
                'message': 'Trip created successfully.'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error in TripListCreateView: {str(e)}")
            return Response({
                "error": "An unexpected error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UpcomingTripsView(generics.ListAPIView):
    """
    API endpt for listing upcoming trips
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(
            user=self.request.user,
            status=Trip.TripStatus.SCHEDULED,
            scheduled_time__gte=timezone.now()
        ).order_by('scheduled_time')

class PastTripsView(generics.ListAPIView):
    """
    API endpt for listing past trips
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        return Trip.objects.filter(
            user=self.request.user,
            status=Trip.TripStatus.COMPLETED
        ).order_by('-scheduled_time')

class OngoingTripView(APIView):
    """
    API endpt for getting ongoing trip details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer

    @swagger_auto_schema(
        operation_description="Get ongoing trip details",
        responses={200: TripSerializer()}
    )
    def get(self, request):
        try:
            trip = Trip.objects.filter(
                user=request.user,
                status=Trip.TripStatus.ONGOING
            ).first()

            if not trip:
                return Response({
                    "error": "No ongoing trip found."
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = self.serializer_class(trip)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in OngoingTripView: {str(e)}")
            return Response({
                "error": "An unexpected error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TripDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpt for retrieving, updating & deleting trips
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TripSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Trip.objects.none()
        return Trip.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.status = Trip.TripStatus.CANCELLED
            instance.save()
            
            return Response({
                "message": "Trip cancelled successfully."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in TripDetailView: {str(e)}")
            return Response({
                "error": "An unexpected error occurred."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RouteListCreateView(generics.ListCreateAPIView):
    """
    API endpt for listing and creating routes
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RouteSerializer

    def get_queryset(self):
        return Route.objects.filter(created_by=self.request.user)

class SavedRoutesView(generics.ListAPIView):
    """
    API endpt for listing saved routes
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RouteSerializer

    def get_queryset(self):
        return Route.objects.filter(
            created_by=self.request.user,
            is_saved=True
        )
