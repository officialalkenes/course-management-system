import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    """
    A normal active user.
    """
    user = User.objects.create_user(
        email="user@example.com",
        password="Password123!",
        first_name="Normal",
        last_name="User",
        # explicitly ensure active:
        is_active=True,
    )
    return user


@pytest.fixture
def admin_user(db):
    """
    A true superuser (is_staff=True, is_superuser=True).
    """
    return User.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123!",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def auth_client(api_client, user):
    """
    APIClient authenticated as normal user.
    """
    token = RefreshToken.for_user(user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """
    APIClient authenticated as admin/superuser.
    """
    token = RefreshToken.for_user(admin_user).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client
