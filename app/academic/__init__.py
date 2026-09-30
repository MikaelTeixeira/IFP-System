from flask import Blueprint


academic_bp = Blueprint("academic", __name__)

from . import routes  # noqa: E402, F401

