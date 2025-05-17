"""
accounts_utils.py

Utility functions for user account management:
- Email and phone validation
- OTP generation, verification, and clearing
- Sending OTP via email and SMS
- JWT token generation
- User creation, profile updates, status changes, and soft deletion
- Password strength checking and reset via OTP
"""

from __future__ import annotations

import logging
import re
import secrets
import string
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, Dict, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.abstract.choices import UserType

if TYPE_CHECKING:
    # For type checking, import the actual User model
    from apps.user.models import User
else:
    # At runtime, resolve User dynamically
    from django.contrib.auth import get_user_model

    User = get_user_model()

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    Check if the provided string is a valid email address.

    Args:
        email: The email string to validate.

    Returns:
        True if the email matches the standard pattern, False otherwise.
    """
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_regex, email))


def validate_phone_number(phone_number: str) -> bool:
    """
    Check if the provided string is a valid phone number.

    Args:
        phone_number: The phone number string to validate.

    Returns:
        True if the phone number matches the expected international format, False otherwise.
    """
    phone_regex = r"^\+?[0-9]{10,15}$"
    return bool(re.match(phone_regex, phone_number))


def generate_otp(length: int = 6) -> str:
    """
    Generate a random numeric One-Time Password (OTP).

    Args:
        length: Length of the OTP (default is 6 digits).

    Returns:
        A string of random digits of the requested length.
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))  # nosec B311


def set_user_otp(user: User, length: int = 6) -> str:
    """
    Create and assign an OTP to a user, marking it as unverified.

    Args:
        user: The User instance to assign the OTP to.
        length: Number of digits for the OTP (default: 6).

    Returns:
        The generated OTP string.
    """
    otp = generate_otp(length)
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.otp_verified = False
    user.save(update_fields=["otp", "otp_created_at", "otp_verified"])
    return otp


def verify_user_otp(user: User, otp: str, expiry_minutes: int = 15) -> bool:
    """
    Verify a user's OTP against the stored value and expiry.

    Args:
        user: The User instance whose OTP to verify.
        otp: The OTP string provided by the user.
        expiry_minutes: Number of minutes the OTP remains valid (default: 15).

    Returns:
        True if the OTP matches and is not expired, False otherwise.
    """
    if not user.otp or user.otp != otp:
        logger.warning(f"OTP verification failed: Invalid OTP for user {user.id}")
        return False

    if not user.otp_created_at:
        logger.warning(
            f"OTP verification failed: Missing creation timestamp for user {user.id}"
        )
        return False

    expiry_time = user.otp_created_at + timedelta(minutes=expiry_minutes)
    if timezone.now() > expiry_time:
        logger.warning(f"OTP verification failed: Expired OTP for user {user.id}")
        return False

    user.otp_verified = True
    user.save(update_fields=["otp_verified"])
    logger.info(f"OTP verification successful for user {user.id}")
    return True


def clear_user_otp(user: User) -> None:
    """
    Remove OTP and its timestamp from a user's record.

    Args:
        user: The User instance to clear OTP from.
    """
    user.otp = None
    user.otp_created_at = None
    user.save(update_fields=["otp", "otp_created_at"])


def send_otp_email(user_or_id, otp, purpose="verification"):
    """
    Email a One-Time Password to the user's email address.

    Args:
        user_or_id: Either a User object or a user ID.
        otp: The OTP string to send.
        purpose: The context (e.g., 'verification', 'password reset').

    Returns:
        True if email sent successfully.
    """
    try:
        # Handle either a User object or a user ID
        if isinstance(user_or_id, User):
            user = user_or_id
        else:
            user = User.objects.get(id=user_or_id)

        logger.info(f"Sending OTP {otp} to {user.email} for {purpose}")

        subject = f"Your {purpose.title()} OTP"
        context = {"user": user, "otp": otp, "purpose": purpose, "expiry_minutes": 15}
        template_path = (
            "emails/otp_email.html"  # Updated path relative to templates directory
        )

        html_message = render_to_string(template_name=template_path, context=context)

        email_message = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email_message.content_subtype = "html"
        email_message.send()

        logger.info(f"OTP email successfully sent to {user.email} for {purpose}")
        return True
    except User.DoesNotExist:
        logger.error(f"User with ID {user_or_id} not found")
        # Re-raise so the task can handle it
        raise
    except Exception as exc:
        logger.error(f"Failed to send OTP email: {exc}")
        # Don't try to call self.retry here - let the task handle retries
        raise


def send_otp_sms(user: User, otp: str, purpose: str = "verification") -> bool:
    """
    Send a One-Time Password to the user's phone via SMS.

    Args:
        user: The User instance to text.
        otp: The OTP string to send.
        purpose: The context (e.g., 'verification', 'password reset').

    Returns:
        True if SMS logged/sent successfully, False otherwise.
    """
    try:
        if not user.phone_number:
            logger.error(f"No phone number for user {user.email}")
            return False

        message = f"Your OTP for {purpose} is: {otp}. Valid for 15 minutes."
        # Integrate with SMS provider (e.g., Twilio) here
        logger.info(f"SMS sent to {user.phone_number}: {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS: {e}")
        return False


def get_tokens_for_user(user: User) -> Dict[str, str]:
    """
    Generate JWT refresh and access tokens for a user.

    Args:
        user: The User instance to authenticate.

    Returns:
        A dict with 'refresh' and 'access' token strings.
    """
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    user_type: str = UserType.USER[0],
    phone_number: Optional[str] = None,
    **extra_fields,
) -> Tuple[User, bool]:
    """
    Create a new user or return existing one if email exists.

    Args:
        email: User's email (unique).
        password: Raw password (will be hashed).
        first_name: First name.
        last_name: Last name.
        user_type: One of UserType values (default 'user').
        phone_number: Optional phone number.
        extra_fields: Any additional User fields.

    Returns:
        Tuple of (User instance, created flag).
    """
    try:
        email = email.lower().strip()
        if not validate_email(email):
            raise ValidationError("Invalid email format")
        if phone_number and not validate_phone_number(phone_number):
            raise ValidationError("Invalid phone number format")

        existing = User.objects.exclude(status="DELETED").filter(email=email).first()
        if existing:
            return existing, False

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            phone_number=phone_number,
            **extra_fields,
        )
        return user, True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise


def update_user_profile(
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    **extra_fields,
) -> User:
    """
    Update fields on a user profile.

    Args:
        user: The User instance to update.
        first_name: New first name.
        last_name: New last name.
        phone_number: New phone number.
        extra_fields: Any additional User fields.

    Returns:
        The updated User instance.
    """
    try:
        to_update: list[str] = []
        if first_name is not None:
            user.first_name = first_name
            to_update.append("first_name")
        if last_name is not None:
            user.last_name = last_name
            to_update.append("last_name")
        if phone_number is not None:
            if not validate_phone_number(phone_number):
                raise ValidationError("Invalid phone number format")
            user.phone_number = phone_number
            to_update.append("phone_number")
        for field, value in extra_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
                to_update.append(field)
        if to_update:
            user.save(update_fields=to_update)
        return user
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise


def change_user_status(user: User, new_status: str) -> User:
    """
    Change a user's status field to a new value.

    Args:
        user: The User instance.
        new_status: One of StatusCHOICES values.

    Returns:
        The updated User instance.
    """
    from apps.abstract.choices import StatusCHOICES

    if new_status not in [c[0] for c in StatusCHOICES.choices]:
        raise ValidationError(f"Invalid status: {new_status}")
    user.status = new_status
    user.save(update_fields=["status"])
    return user


def soft_delete_user(user: User) -> User:
    """
    Soft-delete a user by anonymizing and disabling their account.

    Args:
        user: The User instance to delete.

    Returns:
        The soft-deleted User instance.
    """
    metadata = user.meta or {}
    metadata.update(
        {"deleted_at": timezone.now().isoformat(), "deletion_reason": "user_requested"}
    )
    user.meta = metadata
    user.status = "DELETED"
    user.is_active = False
    user.email = f"deleted-{user.id}@example.com"
    user.first_name = "Deleted"
    user.last_name = "User"
    user.phone_number = None
    user.save()
    return user


def find_user(identifier: str) -> Optional[User]:
    """
    Locate a user by email or phone number, ignoring deleted accounts.

    Args:
        identifier: Email or phone to search.

    Returns:
        The User if found, else None. If multiple, returns the most recently created.
    """
    query = Q(email=identifier) | Q(phone_number=identifier)
    try:
        return User.objects.exclude(status="DELETED").get(query)
    except User.DoesNotExist:
        return None
    except User.MultipleObjectsReturned:
        return (
            User.objects.exclude(status="DELETED")
            .filter(query)
            .order_by("-created_at")
            .first()
        )


def verify_phone(user: User, verify: bool = True) -> User:
    """
    Mark a user's phone as verified or unverified.

    Args:
        user: The User instance.
        verify: True to set verified, False to unset.

    Returns:
        The updated User instance.
    """
    user.phone_verified = verify
    user.save(update_fields=["phone_verified"])
    return user


def check_password_strength(password: str) -> Tuple[bool, str]:
    """
    Assert that a password meets complexity requirements.

    Args:
        password: The raw password to check.

    Returns:
        Tuple of (is_valid, message). is_valid is True if meets all checks.
    """
    min_length = 8
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    special_chars = "!@#$%^&*()-_=+[]{}\\|;:'\",.<>/?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password meets strength requirements"


def initiate_password_reset(email: str) -> Optional[str]:
    """
    Kick off a password-reset OTP flow for a user.

    Args:
        email: The user's email address.

    Returns:
        The OTP if email was sent, else None.
    """
    try:
        user = User.objects.exclude(status="DELETED").get(email=email, is_active=True)
        otp = set_user_otp(user)
        if send_otp_email(user, otp, purpose="password reset"):
            return otp
        return None
    except User.DoesNotExist:
        logger.info(f"Password reset requested for non-existent user: {email}")
        return None
    except Exception as e:
        logger.error(f"Error initiating password reset: {e}")
        return None


def complete_password_reset(email: str, otp: str, new_password: str) -> bool:
    """
    Finish the password-reset flow: validate OTP and set new password.

    Args:
        email: The user's email address.
        otp: The OTP provided by the user.
        new_password: The new raw password.

    Returns:
        True if reset succeeded, False otherwise.
    """
    try:
        user = User.objects.exclude(status="DELETED").get(email=email, is_active=True)
        if not verify_user_otp(user, otp):
            return False
        is_strong, _ = check_password_strength(new_password)
        if not is_strong:
            return False
        user.set_password(new_password)
        user.save()
        clear_user_otp(user)
        return True
    except User.DoesNotExist:
        return False
    except Exception as e:
        logger.error(f"Error completing password reset: {e}")
        return False
