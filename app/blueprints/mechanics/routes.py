from typing import Any, cast

from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Mechanic, db

from . import mechanics_bp
from .schemas import MechanicSchema


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
    return jsonify(mechanic_schema.dump(new_mechanic)), 201


@mechanics_bp.route("/", methods=["GET"])
def get_mechanics():
    mechanics = db.session.execute(select(Mechanic)).scalars().all()
    mechanic_schema = MechanicSchema(many=True)
    return jsonify(mechanic_schema.dump(mechanics, many=True)), 200


@mechanics_bp.route("/<int:id>", methods=["GET"])
def get_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    mechanic_schema = MechanicSchema()
    return jsonify(mechanic_schema.dump(mechanic)), 200


@mechanics_bp.route("/<int:id>", methods=["PUT"])
def update_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    mechanic_schema = MechanicSchema()
    updated_mechanic = cast(Mechanic, mechanic_schema.load(data, instance=mechanic, partial=True))  # pyright: ignore[reportUnknownMemberType]
    db.session.commit()
    return jsonify(mechanic_schema.dump(updated_mechanic)), 200


@mechanics_bp.route("/<int:id>", methods=["DELETE"])
def delete_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    for service in mechanic.services:
        service.mechanic = None

    try:
        db.session.delete(mechanic)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Unable to delete mechanic. Ensure services.mechanic_id is nullable in the database schema."
        }), 400

    return jsonify({"message": "Mechanic deleted successfully."}), 200