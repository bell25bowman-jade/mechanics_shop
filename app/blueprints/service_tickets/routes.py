from flask import jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth import token_required
from app.extensions import cache
from app.models import Customer, Mechanic, Service, db

from . import service_tickets_bp
from .schemas import ServiceTicketSchema


@service_tickets_bp.route("/", methods=["POST"])
@token_required
def create_service_ticket(customer_id: int):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    description = data.get("description")
    mechanic_id = data.get("mechanic_id")

    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    mechanic = None
    if mechanic_id is not None:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic is None:
            return jsonify({"message": "Mechanic not found."}), 404

    new_service_ticket = Service(customer=customer, mechanic=mechanic, description=description)
    db.session.add(new_service_ticket)
    db.session.commit()
    cache.clear()

    service_ticket_schema = ServiceTicketSchema()
    return jsonify(service_ticket_schema.dump(new_service_ticket)), 201


@service_tickets_bp.route("/", methods=["GET"])
@cache.cached(timeout=60, key_prefix="service_tickets_all")
def get_service_tickets():
    service_tickets = db.session.execute(select(Service)).scalars().all()
    service_ticket_schema = ServiceTicketSchema(many=True)
    return jsonify(service_ticket_schema.dump(service_tickets, many=True)), 200


@service_tickets_bp.route("/<int:id>", methods=["GET"])
@cache.cached(timeout=60, key_prefix=lambda: f"service_ticket_{request.view_args['id']}")
def get_service_ticket(id: int):
    service_ticket = db.session.get(Service, id)
    if service_ticket is None:
        return jsonify({"message": "Service ticket not found."}), 404

    service_ticket_schema = ServiceTicketSchema()
    return jsonify(service_ticket_schema.dump(service_ticket)), 200


@service_tickets_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_service_ticket(customer_id: int, id: int):
    service_ticket = db.session.get(Service, id)
    if service_ticket is None:
        return jsonify({"message": "Service ticket not found."}), 404

    if service_ticket.customer_id != customer_id:
        return jsonify({"message": "Forbidden: you can only update your own service tickets."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    target_customer_id = data.get("customer_id")
    description = data.get("description")

    if target_customer_id is not None:
        if target_customer_id != customer_id:
            return jsonify({"message": "Forbidden: you cannot reassign ticket ownership."}), 403
        customer = db.session.get(Customer, target_customer_id)
        if customer is None:
            return jsonify({"message": "Customer not found."}), 404
        service_ticket.customer = customer

    if description is not None:
        service_ticket.description = description

    db.session.commit()
    cache.clear()
    service_ticket_schema = ServiceTicketSchema()
    return jsonify(service_ticket_schema.dump(service_ticket)), 200


@service_tickets_bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_service_ticket(customer_id: int, id: int):
    service_ticket = db.session.get(Service, id)
    if service_ticket is None:
        return jsonify({"message": "Service ticket not found."}), 404

    if service_ticket.customer_id != customer_id:
        return jsonify({"message": "Forbidden: you can only delete your own service tickets."}), 403

    db.session.delete(service_ticket)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Service ticket deleted successfully."}), 200


@service_tickets_bp.route("/<int:id>/assign-mechanic", methods=["PUT"])
@token_required
def assign_mechanic(customer_id: int, id: int):
    service_ticket = db.session.get(Service, id)
    if service_ticket is None:
        return jsonify({"message": "Service ticket not found."}), 404

    if service_ticket.customer_id != customer_id:
        return jsonify({"message": "Forbidden: you can only modify your own service tickets."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    mechanic_id = data.get("mechanic_id")
    mechanic = db.session.get(Mechanic, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    service_ticket.mechanic = mechanic
    db.session.commit()
    cache.clear()

    service_ticket_schema = ServiceTicketSchema()
    return jsonify(service_ticket_schema.dump(service_ticket)), 200


@service_tickets_bp.route("/<int:id>/remove-mechanic", methods=["PUT"])
@token_required
def remove_mechanic(customer_id: int, id: int):
    service_ticket = db.session.get(Service, id)
    if service_ticket is None:
        return jsonify({"message": "Service ticket not found."}), 404

    if service_ticket.customer_id != customer_id:
        return jsonify({"message": "Forbidden: you can only modify your own service tickets."}), 403

    if service_ticket.mechanic is None:
        return jsonify({"message": "Service ticket already has no mechanic."}), 200

    service_ticket.mechanic = None
    try:
        db.session.commit()
        cache.clear()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Unable to remove mechanic. Ensure services.mechanic_id is nullable in the database schema."
        }), 400

    service_ticket_schema = ServiceTicketSchema()
    return jsonify(service_ticket_schema.dump(service_ticket)), 200