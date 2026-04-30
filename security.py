import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt

from fastapi import HTTPException, status

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-long-random-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    # bcrypt only uses first 72 bytes; keep a hard stop too.
    pw_bytes = (password or "").encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=422, detail="Password is too long (max 72 bytes).")
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw((plain or "").encode("utf-8"), (hashed or "").encode("utf-8"))
    except Exception:
        return False


def create_access_token(*, user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
