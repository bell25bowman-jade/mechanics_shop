from flask import Blueprint

customers_bp = Blueprint('customers', __name__)
mechanics_bp = Blueprint('mechanics', __name__)
services_bp = Blueprint('services', __name__)

from . import routes as routes  # pyright: ignore[reportUnusedImport]