from flask import request, jsonify
from typing import Any, cast
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth import encode_token, token_required
from app.blueprints.service_tickets.schemas import ServiceTicketSchema
from app.models import Customer, Service, db

from .usersSchemas import CustomerSchema, login_schema
from sqlalchemy import select
from . import customers_bp

@customers_bp.route("/info", methods=["GET"])
def index():
    return jsonify({
        "message": "Mechanics Shop API",
        "endpoints": {
            "GET /customers": "List customers",
            "POST /customers": "Create customer",
            "GET /customers/<id>": "Get one customer",
            "PUT /customers/<id>": "Update customer",
            "DELETE /customers/<id>": "Delete customer"
        }
    }), 200

@customers_bp.errorhandler(405)
def method_not_allowed(err: Any):
    return jsonify({
        "error": "Method Not Allowed",
        "message": "Use the correct HTTP method for this URL.",
    }), 405

#=======CREATE CUSTOMER========
@customers_bp.route("/", methods=["POST"])
def create_customer():
    raw_data = request.get_json(silent=True)
    if not isinstance(raw_data, dict):
        return jsonify({
            "message": "Request body must be valid JSON.",
            "hint": "Set Content-Type to application/json and send a JSON object.",
        }), 400

    payload = cast(dict[str, Any], raw_data)

    # Accept common client key styles.
    if "make_model" not in payload:
        make_model_alias = payload.get("makeModel") or payload.get("make-model")
        if make_model_alias is not None:
            payload["make_model"] = make_model_alias

    customer_schema = CustomerSchema()
    try:
        new_customer = cast(Customer, customer_schema.load(payload))  # pyright: ignore[reportUnknownMemberType]
    except ValidationError as err:
        return jsonify({
            "message": "Validation failed.",
            "errors": cast(Any, err.messages),  # pyright: ignore[reportUnknownMemberType]
            "required_fields": ["name", "email", "password", "make_model"],
            "date_format": "YYYY-MM-DD",
        }), 400

    query = select(Customer).where(Customer.email == payload.get("email"))
    existing_customer = db.session.execute(query).scalar_one_or_none()
    if existing_customer:
        return jsonify({"message": "Customer with this email already exists."}), 400

    new_customer.password = generate_password_hash(new_customer.password)

    db.session.add(new_customer)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Invalid or duplicate customer data."}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": "Unable to create customer."}), 500

    return jsonify(customer_schema.dump(new_customer)), 201


@customers_bp.route("/login", methods=["POST"])
def login_customer():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    validation_errors = login_schema.validate(data)  # pyright: ignore[reportUnknownMemberType]
    if validation_errors:
        return jsonify(validation_errors), 400

    query = select(Customer).where(Customer.email == data["email"])
    customer = db.session.execute(query).scalar_one_or_none()
    if customer is None:
        return jsonify({"message": "Invalid email or password."}), 401

    if not check_password_hash(customer.password, cast(str, data["password"])):
        return jsonify({"message": "Invalid email or password."}), 401

    token = encode_token(customer.id)
    return jsonify({"token": token}), 200

#======Get all customers========
@customers_bp.route("/", methods=["GET"])
def get_customers():
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    if page < 1 or per_page < 1:
        return jsonify({"message": "page and per_page must be positive integers."}), 400

    if per_page > 100:
        per_page = 100

    query = select(Customer).offset((page - 1) * per_page).limit(per_page)
    customers = db.session.execute(query).scalars().all()
    total_customers = db.session.execute(select(db.func.count(Customer.id))).scalar_one()

    customer_schema = CustomerSchema(many=True)
    return jsonify({
        "items": customer_schema.dump(customers, many=True),
        "page": page,
        "per_page": per_page,
        "total": total_customers,
        "pages": (total_customers + per_page - 1) // per_page,
    }), 200

#=====get customer by id========
@customers_bp.route("/<int:id>", methods=["GET"])
def get_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    customer_schema = CustomerSchema()
    return jsonify(customer_schema.dump(customer)), 200


@customers_bp.route("/my-tickets", methods=["GET"])
@token_required
def get_my_tickets(customer_id: int):
    service_tickets = db.session.execute(
        select(Service).where(Service.customer_id == customer_id)
    ).scalars().all()
    service_ticket_schema = ServiceTicketSchema(many=True)
    return jsonify(service_ticket_schema.dump(service_tickets)), 200

#=====update customer by id========
@customers_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_customer(customer_id: int, id: int):
    if customer_id != id:
        return jsonify({"message": "Forbidden: you can only update your own profile."}), 403

    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    if "password" in data:
        data["password"] = generate_password_hash(cast(str, data["password"]))

    customer_schema = CustomerSchema()
    updated_customer = cast(Customer, customer_schema.load(data, instance=customer, partial=True))  # pyright: ignore[reportUnknownMemberType]
    db.session.commit()
    return jsonify(customer_schema.dump(updated_customer)), 200

#====delete customer by id========
@customers_bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_customer(customer_id: int, id: int):
    if customer_id != id:
        return jsonify({"message": "Forbidden: you can only delete your own profile."}), 403

    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully."}), 200

