from flask import Blueprint


materials_bp = Blueprint("materials", __name__)

from . import routes  # noqa: E402, F401
