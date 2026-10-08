from functools import wraps

from flask import abort, current_app, g, has_app_context, redirect, session, url_for

from .profiles import get_profile


def current_profile():
    """Return the signed-in profile, validated against its account once per request.

    The decorators, the view and the template context all ask for it; without the
    cache each call costs a database round trip.
    """
    key = session.get("profile")
    cached = g.get("_current_profile")
    if cached is None or cached[0] != key:
        cached = (key, _load_profile(key))
        g._current_profile = cached
    profile = cached[1]
    return dict(profile) if profile else None


def _load_profile(key):
    profile = get_profile(key)
    if not profile or not has_app_context() or not current_app.config.get("DATABASE_ENABLED", False):
        return profile
    from ..extensions import db
    from ..models import UserAccount

    account = db.session.get(UserAccount, profile.get("account_id"))
    if not account or account.status.lower() not in {"ativo", "ativa"}:
        return None
    profile["name"] = account.name
    profile["initials"] = "".join(part[0].upper() for part in account.name.split()[:2])
    if account.institution_id:
        profile["institution_id"] = account.institution_id
    if profile["key"] == "teacher":
        from ..data.academic import find

        teacher = find("professores", profile["teacher_id"])
        if teacher:
            profile["institution_id"] = teacher["instituicao_id"]
            profile["class_ids"] = list(teacher.get("turma_ids", []))
    return profile


def profile_is_active(profile_key):
    profile = get_profile(profile_key)
    if not profile or not has_app_context() or not current_app.config.get("DATABASE_ENABLED", False):
        return bool(profile)
    from ..extensions import db
    from ..models import UserAccount

    account = db.session.get(UserAccount, profile.get("account_id"))
    return bool(account and account.status.lower() in {"ativo", "ativa"})


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
