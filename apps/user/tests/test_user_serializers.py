import pytest
from django.contrib.auth import get_user_model


from apps.user.serializers import (
    UserCreateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    OTPVerificationSerializer,
)


from rest_framework.test import APIRequestFactory

from apps.user.utils import set_user_otp

User = get_user_model()
rf = APIRequestFactory()


@pytest.mark.django_db
def test_user_create_serializer_password_mismatch():
    data = {
        "email": "a@test.com",
        "first_name": "A",
        "last_name": "B",
        "phone_number": "",
        "password": "pass1",
        "password_confirm": "pass2",
    }
    ser = UserCreateSerializer(data=data)
    assert not ser.is_valid()
    assert "password_confirm" in ser.errors


@pytest.mark.django_db
def test_change_password_serializer_success(user):
    user.set_password("OldPass1!")
    user.save()
    request = rf.post("/")
    request.user = user
    data = {
        "current_password": "OldPass1!",
        "new_password": "NewPass1!",
        "new_password_confirm": "NewPass1!",
    }
    ser = ChangePasswordSerializer(data=data, context={"request": request})
    assert ser.is_valid(), ser.errors
    ser.save()
    user.refresh_from_db()
    assert user.check_password("NewPass1!")


@pytest.mark.django_db
def test_login_serializer_invalid_credentials():
    request = rf.post("/")
    # no user with this email
    ser = LoginSerializer(
        data={"email": "noone@test.com", "password": "x"}, context={"request": request}
    )
    with pytest.raises(Exception):
        ser.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_otp_verification_serializer(user):
    otp = set_user_otp(user)
    ser = OTPVerificationSerializer(data={"otp": otp}, context={"user": user})
    assert ser.is_valid(), ser.errors
