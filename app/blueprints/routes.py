from flask import request, jsonify
from marshmallow import ValidationError
from typing import Any, cast
from .usersSchemas import MechanicSchema, CustomerSchema
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from . import customers_bp, mechanics_bp, services_bp

from app.models import db, Customer, Mechanic, Service
@customers_bp.route("/", methods=["GET"])
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
@customers_bp.route("/customers", methods=["POST"])
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
@customers_bp.route("/customers", methods=["GET"])
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    customer_schema = CustomerSchema(many=True)
    return jsonify(customer_schema.dump(customers, many=True)), 200

#=====get customer by id========
@customers_bp.route("/customers/<int:id>", methods=["GET"])
def get_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    customer_schema = CustomerSchema()
    return jsonify(customer_schema.dump(customer)), 200

#=====update customer by id========
@customers_bp.route("/customers/<int:id>", methods=["PUT"])
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
@customers_bp.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully."}), 200

#======create routs for mechanics======
#======creates new mechanic========
@mechanics_bp.route("/mechanic", methods=["POST"])
@mechanics_bp.route("/mechanics", methods=["POST"])
def create_mechanic():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    query = select(Mechanic).where(Mechanic.name == data.get("name"))
    existing_mechanic = db.session.execute(query).scalar_one_or_none()
    if existing_mechanic:
        return jsonify({"message": "Mechanic with this name already exists."}), 400

    mechanic_schema = MechanicSchema()
    try:
        new_mechanic = cast(Mechanic, mechanic_schema.load(data))  # pyright: ignore[reportUnknownMemberType]
    except ValidationError as err:
        return jsonify(cast(Any, err.messages)), 400  # pyright: ignore[reportUnknownMemberType]

    db.session.add(new_mechanic)
    db.session.commit()
    return jsonify(mechanic_schema.dump(new_mechanic)), 201

#=====get all mechanics========
@mechanics_bp.route("/mechanics", methods=["GET"])
def get_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()
    mechanic_schema = MechanicSchema(many=True)
    return jsonify(mechanic_schema.dump(mechanics, many=True)), 200

#=====update mechanic by id========
@mechanics_bp.route("/mechanics/<int:id>", methods=["PUT"])
def update_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    data = request.get_json()
    mechanic_schema = MechanicSchema()
    updated_mechanic = cast(Mechanic, mechanic_schema.load(data, instance=mechanic, partial=True))  # pyright: ignore[reportUnknownMemberType]
    db.session.commit()
    return jsonify(mechanic_schema.dump(updated_mechanic)), 200

#====delete mechanic by id========
@mechanics_bp.route("/mechanics/<int:id>", methods=["DELETE"])
def delete_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": "Mechanic deleted successfully."}), 200

#=====service routs========
#====create service ticket=====
@services_bp.route("/services", methods=["POST"])
def create_service():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    mechanic_id = data.get("mechanic_id")
    customer_id = data.get("customer_id")

    mechanic = db.session.get(Mechanic, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    new_service = Service(mechanic=mechanic, customer=customer)
    db.session.add(new_service)
    db.session.commit()
    
    return jsonify({"message": "Service ticket created successfully."}), 201

#====update service ticket========
@services_bp.route("/services/<int:id>", methods=["PUT"])
def update_service(id: int):
    service = db.session.get(Service, id)
    if service is None:
        return jsonify({"message": "Service ticket not found."}), 404

    data = request.get_json()
    mechanic_id = data.get("mechanic_id")
    customer_id = data.get("customer_id")

    if mechanic_id is not None:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic is None:
            return jsonify({"message": "Mechanic not found."}), 404
        service.mechanic = mechanic

    if customer_id is not None:
        customer = db.session.get(Customer, customer_id)
        if customer is None:
            return jsonify({"message": "Customer not found."}), 404
        service.customer = customer

    db.session.commit()
    return jsonify({"message": "Service ticket updated successfully."}), 200


#====remove mechanic from service ticket========
@services_bp.route("/services/<int:id>/remove-mechanic", methods=["PUT"])
def remove_mechanic_from_service(id: int):
    service = db.session.get(Service, id)
    if service is None:
        return jsonify({"message": "Service ticket not found."}), 404

    if service.mechanic is None:
        return jsonify({"message": "Service ticket already has no mechanic."}), 200

    service.mechanic = None
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Unable to remove mechanic. Ensure services.mechanic_id is nullable in the database schema."
        }), 400

    return jsonify({"message": "Mechanic removed from service ticket successfully."}), 200

#====retrieve all service tickets========
@services_bp.route("/services", methods=["GET"])
def get_services(): 
    query = select(Service)
    services = db.session.execute(query).scalars().all()
    service_list: list[dict[str, Any]] = []
    for service in services:
        service_data: dict[str, Any] = {
            "id": service.id,
            "mechanic": {
                "id": service.mechanic.id,
                "name": service.mechanic.name
            } if service.mechanic else None,
            "customer": {
                "id": service.customer.id,
                "name": service.customer.name
            }
        }
        service_list.append(service_data)
    return jsonify(service_list), 200

