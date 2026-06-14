from typing import Any, cast

from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.auth import token_required
from app.extensions import cache
from app.models import Mechanic, Service, db

from . import mechanics_bp
from .schemas import MechanicSchema
from ..service_tickets.schemas import ServiceTicketSchema


cache_cached = cast(Any, cache.cached)  # pyright: ignore[reportUnknownMemberType]


def _mechanic_service_tickets_cache_key() -> str:
    view_args = request.view_args or {}
    mechanic_id = view_args.get("mechanic_id", "unknown")
    return f"mechanic_service_tickets_{mechanic_id}"


def _mechanic_cache_key() -> str:
    view_args = request.view_args or {}
    mechanic_id = view_args.get("id", "unknown")
    return f"mechanic_{mechanic_id}"


@mechanics_bp.route("/<int:mechanic_id>/service-tickets", methods=["GET"])
@cache_cached(timeout=60, make_cache_key=_mechanic_service_tickets_cache_key)
def get_mechanic_service_tickets(mechanic_id: int):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    service_tickets = db.session.execute(
        select(Service).where(Service.mechanic_id == mechanic_id)
    ).scalars().all()
    service_ticket_schema = ServiceTicketSchema(many=True)
    return jsonify(service_ticket_schema.dump(service_tickets)), 200

@mechanics_bp.route("/", methods=["POST"])
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
    cache.clear()
    return jsonify(mechanic_schema.dump(new_mechanic)), 201


@mechanics_bp.route("/", methods=["GET"])
@cache_cached(timeout=60, key_prefix="mechanics_all")
def get_mechanics():
    mechanics = db.session.execute(select(Mechanic)).scalars().all()
    mechanic_schema = MechanicSchema(many=True)
    return jsonify(mechanic_schema.dump(mechanics)), 200


@mechanics_bp.route("/most-tickets", methods=["GET"])
@cache_cached(timeout=60, key_prefix="mechanics_most_tickets")
def get_mechanics_by_most_tickets():
    rows = db.session.execute(
        select(Mechanic, func.count(Service.id).label("ticket_count"))
        .outerjoin(Service, Service.mechanic_id == Mechanic.id)
        .group_by(Mechanic.id)
        .order_by(func.count(Service.id).desc(), Mechanic.id.asc())
    ).all()

    results = [
        {
            "id": mechanic.id,
            "name": mechanic.name,
            "email": mechanic.email,
            "ticket_count": int(ticket_count),
        }
        for mechanic, ticket_count in rows
    ]
    return jsonify(results), 200


@mechanics_bp.route("/<int:id>", methods=["GET"])
@cache_cached(timeout=60, make_cache_key=_mechanic_cache_key)
def get_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    mechanic_schema = MechanicSchema()
    return jsonify(mechanic_schema.dump(mechanic)), 200


@mechanics_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_mechanic(customer_id: int, id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    mechanic_schema = MechanicSchema()
    updated_mechanic = cast(Mechanic, mechanic_schema.load(data, instance=mechanic, partial=True))  # pyright: ignore[reportUnknownMemberType]
    db.session.commit()
    cache.clear()
    return jsonify(mechanic_schema.dump(updated_mechanic)), 200


@mechanics_bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_mechanic(customer_id: int, id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    for service in mechanic.services:
        service.mechanic = None

    try:
        db.session.delete(mechanic)
        db.session.commit()
        cache.clear()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Unable to delete mechanic. Ensure services.mechanic_id is nullable in the database schema."
        }), 400

    return jsonify({"message": "Mechanic deleted successfully."}), 200