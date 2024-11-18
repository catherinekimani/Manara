from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    HomePageView,
    UserRegistrationView,
    UserLoginView,
    RequestOTPView,
    VerifyOTPView,
    UserProfileView,
    VerifyProfileUpdateOTPView,
    DeleteAccountView,
    TripListCreateView,
    TripDetailView,
    UpcomingTripsView,
    PastTripsView,
    OngoingTripView,
    RouteListCreateView,
    SavedRoutesView,
)

app_name = 'authentication'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/verify-otp/', VerifyProfileUpdateOTPView.as_view(), name='verify-profile-update'),
    
    path('delete_account/', DeleteAccountView.as_view(), name='delete_account'),
    
    # Trip endpts
    path('trips/', TripListCreateView.as_view(), name='trip-list-create'),
    path('trips/upcoming/', UpcomingTripsView.as_view(), name='upcoming-trips'),
    path('trips/past/', PastTripsView.as_view(), name='past-trips'),
    path('trips/ongoing/', OngoingTripView.as_view(), name='ongoing-trip'),
    path('trips/<int:pk>/', TripDetailView.as_view(), name='trip-detail'),
    
    # Route endpts
    path('routes/', RouteListCreateView.as_view(), name='route-list-create'),
    path('routes/saved/', SavedRoutesView.as_view(), name='saved-routes'),
]