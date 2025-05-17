from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.user.views import (
    UserViewSet,
    LoginView,
    LogoutView,
    ChangePasswordView,
    EmailVerificationView,
    PhoneVerificationView,
    PhoneOTPVerificationView,
    PasswordResetRequestView,
    PasswordResetCompleteView,
)

# Create a router for ViewSets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

# URL patterns for function-based and class-based views
urlpatterns = [
    # Include the router URLs
    path("", include(router.urls)),
    # Authentication endpoints
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    # Verification endpoints
    path("verify/email/", EmailVerificationView.as_view(), name="verify-email"),
    path("verify/phone/", PhoneVerificationView.as_view(), name="verify-phone"),
    path(
        "verify/phone/otp/", PhoneOTPVerificationView.as_view(), name="verify-phone-otp"
    ),
    # Password reset endpoints
    path(
        "password-reset/request/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/complete/",
        PasswordResetCompleteView.as_view(),
        name="password-reset-complete",
    ),
]
