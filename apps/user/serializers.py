from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _


from apps.abstract.choices import UserType
from apps.user.utils import (
    validate_email,
    validate_phone_number,
    create_user,
    get_tokens_for_user,
    check_password_strength,
    set_user_otp,
    verify_user_otp,
    send_otp_sms,
    find_user,
    initiate_password_reset,
    complete_password_reset,
)
from apps.user.tasks import send_otp_email_task

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - used for general user data representation.
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "user_type",
            "status",
            "created_at",
            "updated_at",
            "is_active",
            "phone_verified",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "email",
            "user_type",
            "is_active",
            "phone_verified",
        ]


class UserDetailSerializer(UserSerializer):
    """
    Extended user serializer with additional fields for detailed view.
    """

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["meta"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        ]
        extra_kwargs = {"user_type": {"default": UserType.USER}}

    def validate_email(self, value):
        if not validate_email(value):
            raise serializers.ValidationError(_("Invalid email format."))
        if User.objects.filter(email=value, status="DELETED").exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()

    def validate_phone_number(self, value):
        if value and not validate_phone_number(value):
            raise serializers.ValidationError(_("Invalid phone number format."))
        return value

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
        is_strong, message = check_password_strength(data["password"])
        if not is_strong:
            raise serializers.ValidationError({"password": message})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        user, created = create_user(
            email=validated_data.pop("email"),
            password=validated_data.pop("password"),
            **validated_data,
        )
        if created:
            otp = set_user_otp(user)
            # Dispatch OTP email via Celery
            send_otp_email_task.delay(user.id, otp, "email verification")
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number"]

    def validate_phone_number(self, value):
        """
        Validate phone number format if provided.
        """
        if value and not validate_phone_number(value):
            raise serializers.ValidationError(_("Invalid phone number format."))

        # If phone number changed, set phone_verified to False
        if self.instance and self.instance.phone_number != value:
            self.instance.phone_verified = False
            self.instance.save(update_fields=["phone_verified"])

        return value

    def update(self, instance, validated_data):
        """
        Update and return user instance.
        """
        instance = super().update(instance, validated_data)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """

    current_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate_current_password(self, value):
        """
        Validate current password is correct.
        """
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Current password is incorrect."))
        return value

    def validate(self, data):
        """
        Validate new passwords match and meet strength requirements.
        """
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("New passwords do not match.")}
            )

        # Check password strength
        is_strong, message = check_password_strength(data["new_password"])
        if not is_strong:
            raise serializers.ValidationError({"new_password": message})

        # Ensure new password is different from current password
        if data["current_password"] == data["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": _(
                        "New password must be different from current password."
                    )
                }
            )

        return data

    def save(self):
        """
        Save the new password.
        """
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        """
        Validate credentials and return user with tokens.
        """
        email = data.get("email", "")
        password = data.get("password", "")

        # Normalize email
        email = email.lower().strip()

        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )

        if not user:
            # Try to find the user to provide more specific error messages
            try:
                user_obj = User.objects.get(email=email)
                if not user_obj.is_active:
                    raise serializers.ValidationError(
                        {"detail": _("Account is disabled. Please contact support.")}
                    )
                # If user exists but authentication failed, it's a password issue
                raise serializers.ValidationError({"detail": _("Invalid password.")})
            except User.DoesNotExist:
                # User doesn't exist
                raise serializers.ValidationError(
                    {"detail": _("No account found with this email.")}
                )

        # Check if user is active and not deleted
        if user.status == "DELETED":
            raise serializers.ValidationError(
                {"detail": _("This account has been deleted.")}
            )

        if user.status == "SUSPENDED" or user.status == "BLOCKED":
            raise serializers.ValidationError(
                {
                    "detail": _(
                        "This account has been suspended. Please contact support."
                    )
                }
            )

        # Generate tokens
        tokens = get_tokens_for_user(user)

        return {"user": user, "tokens": tokens}


class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    """

    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data):
        """
        Validate OTP.
        """
        user = self.context.get("user")
        otp = data.get("otp")

        if not user:
            raise serializers.ValidationError({"detail": _("User not found.")})

        is_valid = verify_user_otp(user, otp)
        if not is_valid:
            raise serializers.ValidationError({"otp": _("Invalid or expired OTP.")})

        return data


class PhoneVerificationSerializer(serializers.Serializer):
    """
    Serializer for phone number verification.
    """

    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        """
        Validate phone number format.
        """
        if not validate_phone_number(value):
            raise serializers.ValidationError(_("Invalid phone number format."))

        user = self.context.get("request").user
        if user.phone_number != value:
            raise serializers.ValidationError(
                _("This phone number doesn't match your account.")
            )

        return value

    def save(self):
        """
        Generate and send OTP for phone verification.
        """
        user = self.context.get("request").user
        otp = set_user_otp(user)
        send_otp_sms(user, otp, purpose="phone verification")
        return {"message": _("OTP sent to your phone number.")}


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Normalize and validate the email.
        We call find_user() for its side‐effects (e.g. logging), but don’t keep the result.
        """
        email = value.lower().strip()
        _ = find_user(email)  # prefix with `_` to avoid “assigned but unused”
        return email

    def save(self):
        """
        Initiate password reset via OTP.
        We call initiate_password_reset() for its side‐effects, not the return value.
        """
        email = self.validated_data["email"]
        initiate_password_reset(email)  # no assignment to `otp`
        return {
            "message": _("If an account exists with this email, an OTP has been sent.")
        }


class PasswordResetCompleteSerializer(serializers.Serializer):
    """
    Serializer for completing password reset.
    """

    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, data):
        """
        Validate passwords match and meet strength requirements.
        """
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("Passwords do not match.")}
            )

        # Check password strength
        is_strong, message = check_password_strength(data["new_password"])
        if not is_strong:
            raise serializers.ValidationError({"new_password": message})

        return data

    def save(self):
        """
        Complete password reset.
        """
        email = self.validated_data["email"]
        otp = self.validated_data["otp"]
        new_password = self.validated_data["new_password"]

        success = complete_password_reset(email, otp, new_password)
        if not success:
            raise serializers.ValidationError(
                {"detail": _("Failed to reset password. Invalid or expired OTP.")}
            )

        return {
            "message": _(
                "Password reset successful. You can now login with your new password."
            )
        }
