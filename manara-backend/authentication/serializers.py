# Django imports
from django.contrib.auth import get_user_model
from django.utils import timezone

# Django REST framework imports
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Third-party imports
from phonenumber_field.serializerfields import PhoneNumberField

from .models import OTPCode, UserProfile, Location, Route, Trip, RouteStop

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    phone_number = PhoneNumberField()
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'full_name', 'user_type', 'password', 'confirm_password']
        read_only_fields = ['id']

    def validate(self, attrs):
        confirm_password = attrs.pop('confirm_password', None)
        
        if attrs['password'] != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match"})
            
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserLoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = get_user_model().objects.filter(email=attrs['email']).first()
        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        return data

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    
    def validate(self, attrs):
        email = attrs.get('email')
        phone_number = attrs.get('phone_number')
        
        if not email and not phone_number:
            raise serializers.ValidationError(
                "Either email or phone number must be provided"
            )
            
        return attrs
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits.")
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ('email', 'first_name', 'last_name', 'phone_number')
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    class Meta:
        model = UserProfile
        fields = ('email', 'first_name', 'last_name', 'phone_number')

    def validate_phone_number(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        return value

    def update(self, instance, validated_data):
        has_changes = any(
            getattr(instance, field) != validated_data.get(field, getattr(instance, field))
            for field in ['first_name', 'last_name', 'phone_number']
        )
        if has_changes:
            instance.is_verified = False
        return super().update(instance, validated_data)
    
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude', 'address']

class RouteStopSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    class Meta:
        model = RouteStop
        fields = ['id', 'location', 'sequence', 'estimated_time']
class RouteSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    start_location = LocationSerializer()
    end_location = LocationSerializer()

    class Meta:
        model = Route
        fields = ['id', 'name', 'start_location', 'end_location', 
                'estimated_duration', 'is_saved', 'stops']

    def create(self, validated_data):
        start_location_data = validated_data.pop('start_location')
        end_location_data = validated_data.pop('end_location')

        created_by = self.context['request'].user

        start_location = Location.objects.create(**start_location_data)
        end_location = Location.objects.create(**end_location_data)

        route = Route.objects.create(
            start_location=start_location,
            end_location=end_location,
            created_by=created_by,
            **validated_data
        )

        stops_data = self.context.get('view').request.data.get('stops', [])
        for stop_data in stops_data:
            stop_data['route'] = route
            RouteStop.objects.create(**stop_data)

        return route

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['route', 'status', 'scheduled_time', 'estimated_arrival_time', 'actual_arrival_time']

    def validate(self, data):
        status = data.get('status')
        scheduled_time = data.get('scheduled_time')
        estimated_time = data.get('estimated_arrival_time')
        actual_time = data.get('actual_arrival_time')
        now = timezone.now()

        if status == 'SCHEDULED':
            if scheduled_time and scheduled_time < now:
                raise serializers.ValidationError("Scheduled time must be in the future")
            if actual_time:
                raise serializers.ValidationError("Actual arrival time should not be set for scheduled trips")
                
        elif status == 'ONGOING':
            if scheduled_time and scheduled_time > now:
                raise serializers.ValidationError("Scheduled time must be in the past for ongoing trips")
            if estimated_time and estimated_time < now:
                raise serializers.ValidationError("Estimated arrival time must be in the future for ongoing trips")
            if actual_time:
                raise serializers.ValidationError("Actual arrival time should not be set for ongoing trips")

        elif status == 'COMPLETED':
            if not actual_time:
                raise serializers.ValidationError("Actual arrival time is required for completed trips")
            if actual_time > now:
                raise serializers.ValidationError("Actual arrival time must be in the past for completed trips")
            if scheduled_time and scheduled_time > actual_time:
                raise serializers.ValidationError("Scheduled time must be before actual arrival time")

        elif status == 'CANCELLED':
            if actual_time:
                raise serializers.ValidationError("Actual arrival time should not be set for cancelled trips")

        return data
