from flask import flash, redirect, render_template, request, session, url_for

from . import auth_bp
from .profiles import PROFILES, get_profile
from .security import profile_is_active


@auth_bp.route("/acesso", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        profile_key = request.form.get("profile") or "student"
        if profile_key not in PROFILES:
            profile_key = "student"
        if not profile_is_active(profile_key):
            flash("Este acesso está desativado. Procure a administração do sistema.", "danger")
            return render_template("auth/login.html", profiles=PROFILES, page_title="Entrar"), 403
        session.clear()
        session["profile"] = profile_key
        flash(f"Acesso iniciado como {get_profile(profile_key)['label']}.", "success")
        return redirect(url_for("core.dashboard"))
    return render_template("auth/login.html", profiles=PROFILES, page_title="Entrar")


@auth_bp.post("/acesso/rapido/<profile_key>")
def quick_access(profile_key):
    if profile_key not in PROFILES:
        flash("Perfil demonstrativo não encontrado.", "danger")
        return redirect(url_for("auth.login"))
    if not profile_is_active(profile_key):
        flash("Este acesso está desativado. Procure a administração do sistema.", "danger")
        return redirect(url_for("auth.login"))
    session.clear()
    session["profile"] = profile_key
    flash(f"Acesso rápido: {get_profile(profile_key)['label']}.", "success")
    return redirect(url_for("core.dashboard"))


@auth_bp.post("/sair")
def logout():
    session.clear()
    flash("Você saiu do ambiente demonstrativo.", "info")
    return redirect(url_for("auth.login"))
