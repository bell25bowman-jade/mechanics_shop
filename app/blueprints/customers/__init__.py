from flask import Blueprint

customers_bp = Blueprint('customers', __name__)

from . import routes as routes  # pyright: ignore[reportUnusedImport]