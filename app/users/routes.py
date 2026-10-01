from flask import abort, flash, redirect, render_template, request, url_for

from . import users_bp
from ..auth.security import current_profile, roles_required
from ..data.academic import DATA, enrich, find, find_identity_conflict, normalize_cpf, normalize_email
from ..data.users import ROLE_LABELS, add_user, delete_user, enrich_user, find_user, list_users, toggle_user, update_user, user_identity_conflict


@users_bp.get("")
@roles_required("it_admin")
def index():
    users = [enrich_user(item) for item in list_users()]
    municipality_id = request.args.get("municipio_id", "")
    institution_id = request.args.get("instituicao_id", "")
    role = request.args.get("cargo", "")
    order = request.args.get("ordem", "az")

    if municipality_id:
        users = [item for item in users if item["municipio_id"] == municipality_id]
    if institution_id:
        users = [item for item in users if item["instituicao_id"] == institution_id]
    if role:
        users = [item for item in users if item["cargo"] == role]
    users.sort(key=lambda item: item["nome"].casefold(), reverse=order == "za")

    return render_template(
        "users/index.html",
        page_title="Usuários",
        users=users,
        municipalities=DATA["municipios"],
        institutions=[enrich("instituicoes", item) for item in DATA["instituicoes"]],
        roles=ROLE_LABELS,
        filters={"municipio_id": municipality_id, "instituicao_id": institution_id, "cargo": role, "ordem": order},
        active_navigation="usuarios",
    )


@users_bp.route("/novo", methods=["GET", "POST"])
@roles_required("it_admin")
def create():
    values = request.form
    error = None
    if request.method == "POST":
        name = request.form.get("nome", "").strip()
        cpf = normalize_cpf(request.form.get("cpf", ""))
        email = normalize_email(request.form.get("email", ""))
        role = request.form.get("cargo", "")
        institution_id = request.form.get("instituicao_id", "")
        institution = find("instituicoes", institution_id) if institution_id else None
        municipality_id = institution["municipio_id"] if institution else request.form.get("municipio_id", "")

        if not name or not cpf or not email or role not in ROLE_LABELS:
            error = "Preencha nome, CPF, e-mail e cargo."
        elif role in {"student", "teacher", "school_coordinator"} and not institution:
            error = "Selecione a instituição deste usuário."
        else:
            academic_field, academic_record = find_identity_conflict(cpf, email)
            account_record = user_identity_conflict(cpf, email)
            conflict = account_record or academic_record
            if conflict:
                error = f"CPF ou e-mail já cadastrado para {conflict['nome']}."

        if not error:
            add_user({
                "nome": name,
                "cpf": cpf,
                "email": email,
                "cargo": role,
                "municipio_id": municipality_id,
                "instituicao_id": institution_id,
            })
            flash("Usuário adicionado no banco de dados.", "success")
            return redirect(url_for("users.index"))

    return render_template(
        "users/form.html",
        page_title="Adicionar usuário",
        values=values,
        error=error,
        municipalities=DATA["municipios"],
        institutions=DATA["instituicoes"],
        roles=ROLE_LABELS,
        active_navigation="usuarios",
    ), 400 if error else 200


@users_bp.route("/<user_id>/editar", methods=["GET", "POST"])
@roles_required("it_admin")
def edit(user_id):
    user = find_user(user_id)
    if not user:
        abort(404)
    values = request.form if request.method == "POST" else user
    error = None
    if request.method == "POST":
        name = request.form.get("nome", "").strip()
        cpf = normalize_cpf(request.form.get("cpf", ""))
        email = normalize_email(request.form.get("email", ""))
        institution_id = request.form.get("instituicao_id", "")
        institution = find("instituicoes", institution_id) if institution_id else None
        municipality_id = institution["municipio_id"] if institution else request.form.get("municipio_id", "")
        role = user["cargo"]
        if not name or not cpf or not email:
            error = "Preencha nome, CPF e e-mail."
        elif role in {"student", "teacher", "school_coordinator"} and not institution:
            error = "Selecione a instituição deste usuário."
        else:
            academic_field, academic_record = find_identity_conflict(cpf, email)
            linked_account_id = (academic_record.get("_user_account_id") or academic_record.get("id")) if academic_record else None
            if academic_record and linked_account_id != user_id:
                error = f"CPF ou e-mail já cadastrado para {academic_record['nome']}."
            account_record = user_identity_conflict(cpf, email, exclude_id=user_id)
            if account_record:
                error = f"CPF ou e-mail já cadastrado para {account_record['nome']}."
        if not error:
            update_user(user_id, {"nome": name, "cpf": cpf, "email": email, "municipio_id": municipality_id, "instituicao_id": institution_id})
            flash("Usuário atualizado no banco de dados.", "success")
            return redirect(url_for("users.index"))
    return render_template("users/form.html", page_title="Editar usuário", values=values, user=user, error=error, municipalities=DATA["municipios"], institutions=DATA["instituicoes"], roles=ROLE_LABELS, active_navigation="usuarios"), 400 if error else 200


@users_bp.post("/<user_id>/excluir")
@roles_required("it_admin")
def delete(user_id):
    user = find_user(user_id)
    if not user:
        abort(404)
    if current_profile().get("account_id") == user_id:
        flash("O usuário de T.I. em uso não pode excluir o próprio acesso.", "danger")
        return redirect(url_for("users.index"))
    if user["cargo"] == "it_admin" and sum(item["cargo"] == "it_admin" for item in list_users()) <= 1:
        flash("O último usuário de T.I. não pode ser excluído.", "danger")
        return redirect(url_for("users.index"))
    delete_user(user_id)
    flash(f"Usuário {user['nome']} excluído. O cadastro acadêmico relacionado foi mantido inativo.", "success")
    return redirect(url_for("users.index"))


@users_bp.post("/<user_id>/status")
@roles_required("it_admin")
def status(user_id):
    user = find_user(user_id)
    if not user:
        abort(404)
    user = toggle_user(user_id)
    flash(f"{user['nome']} agora está {user['status'].lower()}.", "success")
    return redirect(request.referrer or url_for("users.index"))
