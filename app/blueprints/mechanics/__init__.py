from flask import Blueprint


mechanics_bp = Blueprint("mechanics", __name__)


from . import routes as routes  # pyright: ignore[reportUnusedImport]