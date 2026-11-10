from app.core.security import verify_password, hash_password


def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@nuviogrowth.com", "password": "NuvioGrowth2026!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@nuviogrowth.com", "password": "IncorrectPassword"},
    )
    assert response.status_code == 401


def test_register_new_tenant(client):
    unique_email = "newowner@brandboost.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "BrandBoost Global",
            "full_name": "Elena Rostova",
            "email": unique_email,
            "password": "StrongPassword2026!",
            "industry": "E-Commerce",
            "language": "es",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_get_current_user_profile(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@nuviogrowth.com"
    assert data["role"] == "agency_admin"

