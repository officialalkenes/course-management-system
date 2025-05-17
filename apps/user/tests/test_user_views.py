# tests/test_user_views.py

import importlib
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from apps.user.tasks import send_otp_email_task


User = get_user_model()


@pytest.mark.django_db
def test_register_creates_user_and_dispatches_otp(api_client, monkeypatch):
    url = reverse("user-list")
    payload = {
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User",
        "phone_number": "08012345678",
        "password": "StrongPass1!",
        "password_confirm": "StrongPass1!",
    }

    calls = []
    monkeypatch.setattr(
        send_otp_email_task,
        "delay",
        lambda uid, otp, purpose: calls.append((uid, otp, purpose)),
    )

    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data["email"] == "new@example.com"
    assert len(calls) == 1
    uid, otp, purpose = calls[0]
    assert purpose == "email verification"
    assert User.objects.filter(pk=uid).exists()


@pytest.mark.django_db
def test_login_returns_tokens_and_user(api_client, user):
    url = reverse("login")
    resp = api_client.post(
        url,
        {
            "email": user.email,
            "password": "Password123!",
        },
        format="json",
    )

    assert resp.status_code == status.HTTP_200_OK
    assert "tokens" in resp.data
    assert "user" in resp.data
    assert resp.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_me_endpoint(auth_client, user):
    url = reverse("user-me")
    resp = auth_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["email"] == user.email


@pytest.mark.django_db
def test_change_status_forbidden_for_non_admin(auth_client, user):
    """
    Authenticated non-admin users should get 400 (bad request)
    when calling change_status (because change_user_status raises).
    """
    url = reverse("user-change-status", args=[user.id])
    resp = auth_client.post(url, {"status": "SUSPENDED"}, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_change_status_succeeds_for_admin(admin_client, user, monkeypatch):
    user_views = importlib.import_module("apps.user.views")

    """
    Authenticated admin users can change another user's status.
    We patch out change_user_status so it always "works" and returns the user.
    """
    # patch the function as imported by the view
    monkeypatch.setattr(
        user_views,
        "change_user_status",
        lambda obj, new_status: setattr(obj, "status", new_status) or obj,
    )

    url = reverse("user-change-status", args=[user.id])
    resp = admin_client.post(url, {"status": "SUSPENDED"}, format="json")

    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["status"] == "SUSPENDED"


@pytest.mark.django_db
def test_logout_blacklists_refresh(auth_client, user, monkeypatch):
    """
    POST /logout/ should blacklist the provided refresh token.
    """
    url = reverse("logout")
    refresh_token = str(RefreshToken.for_user(user))

    called = []
    # add blacklist if missing, capture calls
    monkeypatch.setattr(
        RefreshToken, "blacklist", lambda self: called.append(self), raising=False
    )

    resp = auth_client.post(url, {"refresh": refresh_token}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["detail"] == "Successfully logged out."
    assert called, "Expected RefreshToken.blacklist() to be called"


@pytest.mark.django_db
def test_change_password_view(auth_client, user):
    """
    POST /change-password/ should update the user's password.
    """
    user.set_password("OldPass1!")
    user.save(update_fields=["password"])

    url = reverse("change-password")
    payload = {
        "current_password": "OldPass1!",
        "new_password": "NewPass2!",
        "new_password_confirm": "NewPass2!",
    }
    resp = auth_client.post(url, payload, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["detail"] == "Password changed successfully."

    user.refresh_from_db()
    assert user.check_password("NewPass2!"), "Password was not updated"


@pytest.mark.django_db
def test_password_reset_request_view(api_client, monkeypatch):
    """
    POST /password-reset-request/ should call initiate_password_reset()
    and return a message.
    """
    url = reverse("password-reset-request")
    called = []
    monkeypatch.setattr(
        "apps.user.serializers.initiate_password_reset",
        lambda email: called.append(email),
    )

    resp = api_client.post(url, {"email": "test@example.com"}, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert "message" in resp.data
    assert called == ["test@example.com"]


@pytest.mark.django_db
def test_password_reset_complete_view_success(api_client, user, monkeypatch):
    """
    POST /password-reset-complete/ with valid OTP succeeds.
    """
    url = reverse("password-reset-complete")
    new_pw = "ResetPass1!"
    data = {
        "email": user.email,
        "otp": "123456",
        "new_password": new_pw,
        "new_password_confirm": new_pw,
    }

    monkeypatch.setattr(
        "apps.user.serializers.complete_password_reset", lambda email, otp, pwd: True
    )

    resp = api_client.post(url, data, format="json")
    assert resp.status_code == status.HTTP_200_OK
    assert "message" in resp.data


@pytest.mark.django_db
def test_password_reset_complete_view_failure(api_client, user, monkeypatch):
    """
    POST /password-reset-complete/ with invalid OTP returns 400.
    """
    url = reverse("password-reset-complete")
    new_pw = "ResetPass1!"
    data = {
        "email": user.email,
        "otp": "000000",
        "new_password": new_pw,
        "new_password_confirm": new_pw,
    }

    monkeypatch.setattr(
        "apps.user.serializers.complete_password_reset", lambda email, otp, pwd: False
    )

    resp = api_client.post(url, data, format="json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in resp.data
