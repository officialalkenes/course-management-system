from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from apps.user.serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    OTPVerificationSerializer,
    PhoneVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetCompleteSerializer,
)
from apps.user.utils import (
    set_user_otp,
    change_user_status,
    verify_phone,
)
from apps.user.permissions import IsOwnerOrAdmin, IsAdminUser
from apps.abstract.choices import StatusCHOICES
from apps.user.tasks import send_otp_email_task

User = get_user_model()


@extend_schema(tags=["Users"])
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model - handles CRUD operations.
    """

    queryset = User.objects.exclude(status="DELETED")
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        elif self.action in ["list", "admin_users"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsOwnerOrAdmin]
        return [perm() for perm in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or self.action == "create":
            return User.objects.none()
        if user.user_type == "ADMIN" or user.is_staff:
            return User.objects.exclude(status="DELETED")
        return User.objects.filter(id=user.id)

    @extend_schema(
        request=UserCreateSerializer,
        responses={201: UserDetailSerializer},
        summary="Register a new user",
        description="Create a new user account",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses={200: UserSerializer(many=True)},
        summary="List users",
        description="Retrieve a list of users (admins only)",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={200: UserDetailSerializer},
        summary="Retrieve a user",
        description="Retrieve details for a specific user",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=UserUpdateSerializer,
        responses={200: UserDetailSerializer},
        summary="Update a user",
        description="Update user fields (self or admin)",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=UserUpdateSerializer,
        responses={200: UserDetailSerializer},
        summary="Partially update a user",
        description="Partially update user fields (self or admin)",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                description="New status for the user",
                required=True,
                type=str,
                enum=[c[0] for c in StatusCHOICES.choices],
            )
        ],
        responses={200: UserDetailSerializer},
        summary="Change user status",
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def change_status(self, request, pk=None):
        user = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"detail": _("Status is required.")}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            updated = change_user_status(user, new_status)
            return Response(UserDetailSerializer(updated).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={200: UserSerializer(many=True)},
        summary="List admin users",
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAdminUser])
    def admin_users(self, request):
        admins = User.objects.filter(user_type="ADMIN", status__ne="DELETED")
        return Response(UserSerializer(admins, many=True).data)

    @extend_schema(
        responses={200: UserDetailSerializer},
        summary="Get current user profile",
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserDetailSerializer(request.user).data)


@extend_schema(tags=["Authentication"])
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: OpenApiResponse(response=UserDetailSerializer)},
        summary="User login",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = serializer.validated_data["tokens"]
        return Response(
            {"user": UserDetailSerializer(user).data, "tokens": tokens},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Authentication"])
class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name="refresh",
                description="Refresh token to blacklist",
                required=True,
                type=str,
            )
        ],
        responses={200: OpenApiResponse(response=None)},
        summary="User logout",
    )
    def post(self, request, *args, **kwargs):
        refresh = request.data.get("refresh")
        if refresh:
            RefreshToken(refresh).blacklist()
        return Response(
            {"detail": _("Successfully logged out.")}, status=status.HTTP_200_OK
        )


@extend_schema(tags=["Authentication"])
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(response=None)},
        summary="Change user password",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": _("Password changed successfully.")}, status=status.HTTP_200_OK
        )


@extend_schema(tags=["Verification"])
class EmailVerificationView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(response=None)},
        summary="Send email OTP",
    )
    def get(self, request, *args, **kwargs):
        otp = set_user_otp(request.user)
        # Use the task for consistency with user creation flow
        send_otp_email_task.delay(request.user.id, otp, purpose="email verification")
        return Response(
            {"detail": _("OTP sent to your email.")}, status=status.HTTP_200_OK
        )

    @extend_schema(
        request=OTPVerificationSerializer,
        responses={200: OpenApiResponse(response=None)},
        summary="Verify email OTP",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"user": request.user},  # Explicitly add user to context
        )
        serializer.is_valid(raise_exception=True)

        # The verify_user_otp function already sets otp_verified=True
        # No need to do it again here

        # Clear the OTP after successful verification for security
        request.user.otp = None
        request.user.otp_created_at = None
        request.user.save(update_fields=["otp", "otp_created_at"])

        return Response(
            {"detail": _("Email verified successfully.")}, status=status.HTTP_200_OK
        )


@extend_schema(tags=["Verification"])
class PhoneVerificationView(generics.GenericAPIView):
    serializer_class = PhoneVerificationSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PhoneVerificationSerializer,
        responses={200: OpenApiResponse(response=None)},
        summary="Send phone OTP",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Verification"])
class PhoneOTPVerificationView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OTPVerificationSerializer,
        responses={200: OpenApiResponse(response=None)},
        summary="Verify phone OTP",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify_phone(request.user, True)
        return Response(
            {"detail": _("Phone number verified successfully.")},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Password Reset"])
class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(response=None)},
        summary="Request password reset OTP",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=["Password Reset"])
class PasswordResetCompleteView(generics.GenericAPIView):
    serializer_class = PasswordResetCompleteSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=PasswordResetCompleteSerializer,
        responses={200: OpenApiResponse(response=None)},
        summary="Complete password reset",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
