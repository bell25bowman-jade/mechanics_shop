from functools import wraps
from typing import Any, Callable, TypeVar, cast
from datetime import datetime, timedelta, timezone

from flask import current_app, jsonify, request
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError


F = TypeVar("F", bound=Callable[..., Any])


def _jwt_secret() -> str:
    secret_key = current_app.config.get("JWT_SECRET_KEY") or current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY or JWT_SECRET_KEY is not configured.")
    return cast(str, secret_key)


def _jwt_algorithm() -> str:
    return cast(str, current_app.config.get("JWT_ALGORITHM", "HS256"))


def encode_token(customer_id: int) -> str:
    expires_in = int(current_app.config.get("TOKEN_MAX_AGE_SECONDS", 3600))
    payload = {
        "customer_id": customer_id,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    return cast(str, jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm()))


def token_required(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header with Bearer token is required."}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"message": "Bearer token is required."}), 401

        try:
            token_data = cast(dict[str, Any], jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()]))
        except ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 401
        except JWTError:
            return jsonify({"message": "Invalid token."}), 401

        customer_id = token_data.get("customer_id")
        if not isinstance(customer_id, int):
            return jsonify({"message": "Invalid token payload."}), 401

        return func(customer_id, *args, **kwargs)

    return cast(F, wrapper)