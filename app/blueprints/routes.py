from flask import request, jsonify
from marshmallow import ValidationError
from typing import Any, cast
from .usersSchemas import CustomerSchema
from sqlalchemy import select
from . import customers_bp

from app.models import db, Customer
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
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    query = select(Customer).where(Customer.name == data.get("name"))
    existing_customer = db.session.execute(query).scalar_one_or_none()
    if existing_customer:
        return jsonify({"message": "Customer with this name already exists."}), 400

    customer_schema = CustomerSchema()
    try:
        new_customer = cast(Customer, customer_schema.load(data))  # pyright: ignore[reportUnknownMemberType]
    except ValidationError as err:
        return jsonify(cast(Any, err.messages)), 400  # pyright: ignore[reportUnknownMemberType]

    db.session.add(new_customer)
    db.session.commit()
    return jsonify(customer_schema.dump(new_customer)), 201

#======Get all customers========
@customers_bp.route("/", methods=["GET"])
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    customer_schema = CustomerSchema(many=True)
    return jsonify(customer_schema.dump(customers, many=True)), 200

#=====get customer by id========
@customers_bp.route("/<int:id>", methods=["GET"])
def get_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    customer_schema = CustomerSchema()
    return jsonify(customer_schema.dump(customer)), 200

#=====update customer by id========
@customers_bp.route("/<int:id>", methods=["PUT"])
def update_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    data = request.get_json()
    customer_schema = CustomerSchema()
    updated_customer = cast(Customer, customer_schema.load(data, instance=customer, partial=True))  # pyright: ignore[reportUnknownMemberType]
    db.session.commit()
    return jsonify(customer_schema.dump(updated_customer)), 200

#====delete customer by id========
@customers_bp.route("/<int:id>", methods=["DELETE"])
def delete_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully."}), 200

