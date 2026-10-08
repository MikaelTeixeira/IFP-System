from flask import abort, redirect, render_template, request, url_for

from . import reports_bp
from ..auth.security import current_profile, roles_required
from ..data.academic import DATA
from ..data.reports import (
    bar_chart,
    class_report,
    institute_report,
    line_chart,
    school_history,
    school_report,
    series_report,
    student_attendance_roster,
)


REPORT_ROLES = ("school_coordinator", "institute_coordinator")


def _find_or_404(entity, item_id):
    record = next((item for item in DATA[entity] if item["id"] == item_id), None)
    if record is None:
        abort(404)
    return record


def _ensure_school_scope(institution_id):
    profile = current_profile()
    if profile["key"] == "school_coordinator" and profile.get("institution_id") != institution_id:
        abort(403)


@reports_bp.get("/")
@roles_required(*REPORT_ROLES)
def index():
    profile = current_profile()
    if profile["key"] == "school_coordinator":
        return redirect(url_for("reports.school", institution_id=profile["institution_id"]))
    report = institute_report()
    school_names = [item["nome"] for item in report["schools"]]
    colors = ["#2D3B57", "#B86122", "#277454", "#536381"]
    network_trend_chart = {
        "labels": ["Fev", "Mar", "Abr", "Mai", "Jun", "Ago", "Set"],
        "datasets": [
            {"label": school["nome"], "values": school["trend"], "color": colors[index % len(colors)]}
            for index, school in enumerate(report["schools"])
        ],
        "max": 10,
    }
    return render_template(
        "reports/index.html", page_title="Relatórios das escolas", report=report,
        performance_chart=bar_chart(school_names, [item["average"] for item in report["schools"]], "Média", 10),
        absence_chart=bar_chart(school_names, [item["absences"] for item in report["schools"]], "Faltas"),
        network_trend_chart=network_trend_chart,
        active_navigation="relatorios",
    )


@reports_bp.get("/escolas/<institution_id>")
@roles_required(*REPORT_ROLES)
def school(institution_id):
    _ensure_school_scope(institution_id)
    institution = _find_or_404("instituicoes", institution_id)
    report = school_report(institution)
    return render_template(
        "reports/school.html", page_title=f"Desempenho · {institution['nome']}", report=report,
        performance_chart=line_chart(report["trend"]),
        absence_chart=bar_chart(["Fev", "Mar", "Abr", "Mai", "Jun", "Ago", "Set"], report["absence_trend"], "Faltas"),
        can_view_all=current_profile()["key"] == "institute_coordinator", active_navigation="relatorios",
    )


@reports_bp.get("/escolas/<institution_id>/historico")
@roles_required(*REPORT_ROLES)
def history(institution_id):
    _ensure_school_scope(institution_id)
    institution = _find_or_404("instituicoes", institution_id)
    return render_template(
        "reports/history.html",
        page_title=f"Histórico · {institution['nome']}",
        institution=institution,
        periods=school_history(institution),
        active_navigation="relatorios",
    )


@reports_bp.get("/escolas/<institution_id>/estudantes/<view>")
@roles_required(*REPORT_ROLES)
def students(institution_id, view):
    views = {
        "frequencia": {
            "title": "Estudantes que compareceram",
            "description": "Relação de estudantes marcados como presentes no último registro do período.",
            "status": "Presente",
        },
        "faltas": {
            "title": "Estudantes que faltaram",
            "description": "Relação de estudantes marcados como ausentes no último registro do período.",
            "status": "Ausente",
        },
        "todos": {
            "title": "Relação total de estudantes",
            "description": "Todos os estudantes vinculados ao recorte acadêmico selecionado.",
            "status": None,
        },
    }
    if view not in views:
        abort(404)
    _ensure_school_scope(institution_id)
    institution = _find_or_404("instituicoes", institution_id)
    series_id = request.args.get("series_id") or None
    class_id = request.args.get("class_id") or None
    series_record = _find_or_404("series", series_id) if series_id else None
    class_record = _find_or_404("turmas", class_id) if class_id else None
    if series_record and series_record.get("instituicao_id") != institution_id:
        abort(404)
    if class_record and (
        class_record.get("instituicao_id") != institution_id
        or (series_id and class_record.get("serie_id") != series_id)
    ):
        abort(404)
    if class_record and not series_record:
        series_record = _find_or_404("series", class_record["serie_id"])
        series_id = series_record["id"]

    all_students = student_attendance_roster(institution_id, series_id=series_id, class_id=class_id)
    selected_view = views[view]
    records = [
        item for item in all_students
        if selected_view["status"] is None or item["latest_status"] == selected_view["status"]
    ]
    return render_template(
        "reports/students.html",
        page_title=f"{selected_view['title']} · {institution['nome']}",
        institution=institution,
        series=series_record,
        school_class=class_record,
        records=records,
        total_students=len(all_students),
        selected_view=view,
        view_config=selected_view,
        active_navigation="relatorios",
    )


@reports_bp.get("/escolas/<institution_id>/series/<series_id>")
@roles_required(*REPORT_ROLES)
def series(institution_id, series_id):
    _ensure_school_scope(institution_id)
    institution = _find_or_404("instituicoes", institution_id)
    series_record = _find_or_404("series", series_id)
    if series_record.get("instituicao_id") != institution_id:
        abort(404)
    report = series_report(institution, series_record)
    return render_template(
        "reports/series.html", page_title=f"{series_record['nome']} · {institution['nome']}", institution=institution, report=report,
        performance_chart=line_chart(report["trend"]),
        absence_chart=bar_chart([item["nome"] for item in report["classes_data"]], [item["absences"] for item in report["classes_data"]], "Faltas"),
        active_navigation="relatorios",
    )


@reports_bp.get("/escolas/<institution_id>/series/<series_id>/turmas/<class_id>")
@roles_required(*REPORT_ROLES)
def school_class(institution_id, series_id, class_id):
    _ensure_school_scope(institution_id)
    institution = _find_or_404("instituicoes", institution_id)
    series_record = _find_or_404("series", series_id)
    school_class_record = _find_or_404("turmas", class_id)
    if series_record.get("instituicao_id") != institution_id or school_class_record.get("serie_id") != series_id or school_class_record.get("instituicao_id") != institution_id:
        abort(404)
    report = class_report(institution, series_record, school_class_record)
    return render_template(
        "reports/class.html", page_title=f"{school_class_record['nome']} · {series_record['nome']}", institution=institution, series=series_record, report=report,
        performance_chart=line_chart(report["trend"]),
        absence_chart=bar_chart(["Fev", "Mar", "Abr", "Mai", "Jun", "Ago", "Set"], report["absence_trend"], "Faltas"),
        active_navigation="relatorios",
    )
