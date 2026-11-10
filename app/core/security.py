import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from app.config import settings


def _get_fernet_cipher() -> Fernet:
    """Generate a reliable 32-byte Fernet key based on SECRET_KEY or ENCRYPTION_KEY."""
    raw_key = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    # Hash to 32 bytes and urlsafe base64 encode
    key_32 = hashlib.sha256(raw_key.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(key_32)
    return Fernet(b64_key)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    # Truncate to 72 bytes if needed (bcrypt standard limit)
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(
    subject: Union[str, Any],
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    if claims:
        to_encode.update(claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """Create JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_token(raw_token: str) -> str:
    """Encrypt sensitive OAuth tokens before storing them in the database."""
    if not raw_token:
        return ""
    cipher = _get_fernet_cipher()
    encrypted = cipher.encrypt(raw_token.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt stored OAuth tokens."""
    if not encrypted_token:
        return ""
    try:
        cipher = _get_fernet_cipher()
        decrypted = cipher.decrypt(encrypted_token.encode("utf-8"))
        return decrypted.decode("utf-8")
    except (InvalidToken, Exception):
        return ""

