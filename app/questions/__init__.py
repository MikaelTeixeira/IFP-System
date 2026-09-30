from flask import Blueprint


questions_bp = Blueprint("questions", __name__)

from . import routes  # noqa: E402, F401

