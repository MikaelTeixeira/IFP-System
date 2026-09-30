from functools import wraps

from flask import abort, redirect, session, url_for

from .profiles import get_profile


def current_profile():
    return get_profile(session.get("profile"))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_profile() is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_profile()["key"] not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator

