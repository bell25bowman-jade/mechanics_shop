from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


F = TypeVar("F", bound=Callable[..., Any])


def _serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not configured.")
    return URLSafeTimedSerializer(secret_key=secret_key, salt="customer-auth")


def encode_token(customer_id: int) -> str:
    token_payload = {"customer_id": customer_id}
    return _serializer().dumps(token_payload)


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
            token_data = _serializer().loads(
                token,
                max_age=int(current_app.config.get("TOKEN_MAX_AGE_SECONDS", 3600)),
            )
        except SignatureExpired:
            return jsonify({"message": "Token has expired."}), 401
        except BadSignature:
            return jsonify({"message": "Invalid token."}), 401

        customer_id = token_data.get("customer_id")
        if not isinstance(customer_id, int):
            return jsonify({"message": "Invalid token payload."}), 401

        return func(customer_id, *args, **kwargs)

    return cast(F, wrapper)