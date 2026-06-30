from typing import Any, cast
from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy import select
from app.auth import token_required
from app.extensions import cache
from app.models import Inventory, db
from typing import cast
from . import inventory_bp
from .schemas import InventorySchema
from typing import Any, cast


cache_cached = cast(Any, cache.cached)  # pyright: ignore[reportUnknownMemberType]


def _session_get(model: type[Any], object_id: int) -> Any:
    session = db.session
    return session.execute(select(model).where(model.id == object_id)).scalar_one_or_none()


def _inventory_cache_key(*args: Any, **kwargs: Any) -> str:
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
    item = _session_get(Inventory, id)
    if item is None:
        return jsonify({"message": "Inventory item not found."}), 404

    inventory_schema = InventorySchema()
    return jsonify(inventory_schema.dump(item)), 200


@inventory_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_inventory_item(customer_id: int, id: int):
    item = _session_get(Inventory, id)
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
    item = _session_get(Inventory, id)
    if item is None:
        return jsonify({"message": "Inventory item not found."}), 404

    db.session.delete(item)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Inventory item deleted successfully."}), 200

@inventory_bp.route("/delete", methods=["DELETE"])
@token_required
def delete_items(customer_id: int):
    data = request.get_json()
    if not data or "ids" not in data:
        return jsonify({"message": "Request body must contain 'ids' field."}), 400

    ids = data["ids"]
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return jsonify({"message": "'ids' field must be a list of integers."}), 400

    items = db.session.execute(select(Inventory).where(Inventory.id.in_(ids))).scalars().all()
    if not items:
        return jsonify({"message": "No inventory items found for the provided IDs."}), 404

    for item in items:
        db.session.delete(item)
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"{len(items)} inventory items deleted successfully."}), 200