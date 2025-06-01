import pytest  # type: ignore
from rest_framework.test import APIClient  # type: ignore
from rest_framework import status  # type: ignore
from django.contrib.auth import get_user_model


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user():
    User = get_user_model()

    def _create_user(**kwargs):
        defaults = {
            "full_name": "Test User",
            "email": "test@example.com",
            "student_id": "ST0000",
            "phone_number": "0123456789",
            "password": "TestPass123",
            "role": "student"
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    return _create_user


@pytest.mark.django_db
def test_register_success(api_client):
    payload = {
        "full_name": "Alice Student",
        "email": "alice@example.com",
        "student_id": "ST1234",
        "phone_number": "0123456789",
        "password": "StrongPass123",
        "role": "student"
    }
    response = api_client.post("/api/users/register/", payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == 'User registered successfully.'


@pytest.mark.django_db
def test_register_user_invalid_data(api_client):
    invalid_cases = [
        (
            {
                "full_name": "Test Student",
                "email": "test@student.com",
                "phone_number": "0123456789",
                "password": "StudentPass123",
                "role": "student"
            },
            "Student ID is required for student accounts."
        ),
        (
            {
                "full_name": "Admin User",
                "student_id": "ADMIN01",
                "phone_number": "0987654321",
                "password": "AdminPass123",
                "role": "admin"
            },
            "Email is required for admin accounts."
        ),
        (
            {
                "full_name": "No Password",
                "email": "nopass@example.com",
                "student_id": "NP001",
                "phone_number": "0123012301",
                "role": "student"
            },
            "password"  # field-level key
        ),
    ]

    for payload, expected_error in invalid_cases:
        response = api_client.post("/api/users/register/", payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        if expected_error == "password":
            assert "password" in response.data
        else:
            assert "non_field_errors" in response.data
            assert expected_error in response.data["non_field_errors"]


@pytest.mark.django_db
def test_login_student_success(api_client, create_user):
    create_user(
        full_name="Alice Student",
        email="alice@example.com",
        student_id="ST1234",
        password="StrongPass123",
        role="student"
    )

    payload = {
        "username": "ST1234",
        "password": "StrongPass123",
        "role": "student"
    }

    response = api_client.post("/api/users/login/", payload)
    assert response.status_code == 200
    assert "access" in response.data["tokens"]


@pytest.mark.django_db
def test_login_admin_success(api_client, create_user):
    create_user(
        full_name="Admin User",
        email="admin@example.com",
        student_id="ADM001",
        password="AdminStrong123",
        role="admin"
    )

    payload = {
        "username": "admin@example.com",
        "password": "AdminStrong123",
        "role": "admin"
    }

    response = api_client.post("/api/users/login/", payload)
    assert response.status_code == 200
    assert "access" in response.data["tokens"]
    assert response.data["user"]["email"] == "admin@example.com"


@pytest.mark.django_db
def test_user_profile_authenticated(api_client, create_user):
    user = create_user(
        full_name="Student User",
        email="student@example.com",
        student_id="ST4321",
        password="MyPass123",
        role="student"
    )

    login_payload = {
        "username": "ST4321",
        "password": "MyPass123",
        "role": "student"
    }

    login_response = api_client.post("/api/users/login/", login_payload)
    assert login_response.status_code == 200
    access_token = login_response.data["tokens"]["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    profile_response = api_client.get("/api/users/profile/")
    assert profile_response.status_code == 200
    assert profile_response.data["full_name"] == "Student User"
    assert profile_response.data["student_id"] == "ST4321"
