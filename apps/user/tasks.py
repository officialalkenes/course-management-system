import logging
from celery import shared_task
from django.contrib.auth import get_user_model

from apps.abstract.utils.accounts_utils import (
    initiate_password_reset,
    send_otp_email,
    send_otp_sms,
)


User = get_user_model()

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_otp_email_task(self, user_id: int, otp: str, purpose: str) -> None:
    """
    Celery task to send an OTP email asynchronously.

    Args:
        user_id: Primary key of the User to email.
        otp: The One-Time Password code.
        purpose: Context for the OTP (e.g., 'email verification', 'password reset').
    """
    try:
        # It's safer to directly pass the user_id and let send_otp_email handle the lookup
        send_otp_email(user_id, otp, purpose)
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found - abandoning task")
        # No need to retry if the user doesn't exist
        return
    except Exception as exc:
        logger.error(f"Failed to send OTP email, retrying: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(bind=True)
def send_otp_sms_task(self, user_id: int, otp: str, purpose: str) -> None:
    """
    Celery task to send an OTP SMS asynchronously.

    Args:
        user_id: Primary key of the User to message.
        otp: The One-Time Password code.
        purpose: Context for the OTP (e.g., 'phone verification').
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    send_otp_sms(user, otp, purpose)


@shared_task(bind=True)
def send_password_reset_task(self, email: str) -> None:
    """
    Celery task to initiate a password reset by generating and emailing an OTP.

    Args:
        email: Email address of the user requesting password reset.
    """
    # This will generate the OTP and send the email if the user exists
    initiate_password_reset(email)
