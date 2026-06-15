from typing import Any, cast

from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select

from app.auth import token_required
from app.extensions import cache
from app.models import Inventory, db

from . import inventory_bp
from .schemas import InventorySchema


cache_cached = cast(Any, cache.cached)  # pyright: ignore[reportUnknownMemberType]


def _inventory_cache_key() -> str:
    view_args = request.view_args or {}
    item_id = view_args.get("id", "unknown")
    return f"inventory_{item_id}"


@inventory_bp.route("/", methods=["POST"])
@token_required
def create_inventory_item(customer_id: int):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    inventory_schema = InventorySchema()
    try:
        new_item = cast(Inventory, inventory_schema.load(data))  # pyright: ignore[reportUnknownMemberType]
    except ValidationError as err:
        return jsonify(cast(Any, err.messages)), 400  # pyright: ignore[reportUnknownMemberType]

    db.session.add(new_item)
    db.session.commit()
    cache.clear()
    return jsonify(inventory_schema.dump(new_item)), 201


@inventory_bp.route("/", methods=["GET"])
@cache_cached(timeout=60, key_prefix="inventory_all")
def get_inventory_items():
    items = db.session.execute(select(Inventory)).scalars().all()
    inventory_schema = InventorySchema(many=True)
    return jsonify(inventory_schema.dump(items)), 200


@inventory_bp.route("/<int:id>", methods=["GET"])
@cache_cached(timeout=60, make_cache_key=_inventory_cache_key)
def get_inventory_item(id: int):
    item = db.session.get(Inventory, id)
    if item is None:
        return jsonify({"message": "Inventory item not found."}), 404

    inventory_schema = InventorySchema()
    return jsonify(inventory_schema.dump(item)), 200


@inventory_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_inventory_item(customer_id: int, id: int):
    item = db.session.get(Inventory, id)
    if item is None:
        return jsonify({"message": "Inventory item not found."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    inventory_schema = InventorySchema()
    updated_item = cast(Inventory, inventory_schema.load(data, instance=item, partial=True))  # pyright: ignore[reportUnknownMemberType]
    db.session.commit()
    cache.clear()
    return jsonify(inventory_schema.dump(updated_item)), 200


@inventory_bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_inventory_item(customer_id: int, id: int):
    item = db.session.get(Inventory, id)
    if item is None:
        return jsonify({"message": "Inventory item not found."}), 404

    db.session.delete(item)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Inventory item deleted successfully."}), 200
