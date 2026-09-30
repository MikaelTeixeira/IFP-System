from flask import Blueprint


curriculum_bp = Blueprint("curriculum", __name__)

from . import routes  # noqa: E402, F401
