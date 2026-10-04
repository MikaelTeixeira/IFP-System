from flask import Blueprint


scanner_bp = Blueprint("scanner", __name__)

from . import routes  # noqa: E402, F401
