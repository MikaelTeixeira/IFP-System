from flask import Blueprint


student_bp = Blueprint("student_area", __name__)

from . import routes  # noqa: E402, F401
