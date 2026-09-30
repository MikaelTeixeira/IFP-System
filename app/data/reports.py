from statistics import mean

from .academic import DATA


MONTHS = ["Fev", "Mar", "Abr", "Mai", "Jun", "Ago", "Set"]
SCHOOL_BASELINES = {
    "inst-001": {"average": 8.4, "attendance": 95.2, "absences": 84, "trend": [7.6, 7.8, 8.0, 7.9, 8.2, 8.3, 8.4], "absence_trend": [16, 14, 13, 12, 11, 10, 8]},
    "inst-002": {"average": 7.9, "attendance": 93.6, "absences": 102, "trend": [7.2, 7.4, 7.3, 7.6, 7.7, 7.8, 7.9], "absence_trend": [19, 18, 16, 15, 13, 12, 9]},
    "inst-003": {"average": 7.6, "attendance": 92.8, "absences": 116, "trend": [7.0, 7.1, 7.3, 7.2, 7.4, 7.5, 7.6], "absence_trend": [22, 20, 18, 17, 15, 14, 10]},
    "inst-004": {"average": 7.3, "attendance": 91.9, "absences": 129, "trend": [6.8, 6.9, 7.0, 7.0, 7.1, 7.2, 7.3], "absence_trend": [24, 22, 21, 19, 17, 15, 11]},
}


def _numeric_id(value):
    try:
        return int(value.rsplit("-", 1)[-1])
    except (TypeError, ValueError):
        return 1


def _records(key, **filters):
    return [item for item in DATA[key] if all(item.get(field) == value for field, value in filters.items())]


def _actual_scores(student_ids):
    """Return normalized persisted assessment scores when the database is available."""
    try:
        from ..models import AssessmentAttempt
        from .assessments import ASSESSMENTS

        question_counts = {item["id"]: max(1, len(item.get("question_ids", []))) for item in ASSESSMENTS}
        attempts = AssessmentAttempt.query.filter(
            AssessmentAttempt.student_id.in_(student_ids),
            AssessmentAttempt.status == "Resultado disponível",
            AssessmentAttempt.final_score.isnot(None),
        ).all() if student_ids else []
        return [min(10, round(item.final_score / question_counts.get(item.assessment_id, 1) * 10, 1)) for item in attempts]
    except (RuntimeError, AttributeError):
        return []


def _metrics(institution_id, series_id=None, class_id=None):
    baseline = SCHOOL_BASELINES.get(institution_id, SCHOOL_BASELINES["inst-004"])
    scope_id = class_id or series_id or institution_id
    adjustment = ((_numeric_id(scope_id) % 5) - 2) * 0.12 if scope_id != institution_id else 0
    students = _records("alunos", instituicao_id=institution_id)
    classes = _records("turmas", instituicao_id=institution_id)
    if series_id:
        classes = [item for item in classes if item["serie_id"] == series_id]
        class_ids = {item["id"] for item in classes}
        students = [item for item in students if item["turma_id"] in class_ids]
    if class_id:
        classes = [item for item in classes if item["id"] == class_id]
        students = [item for item in students if item["turma_id"] == class_id]

    actual_scores = _actual_scores([item["id"] for item in students])
    average = round(mean(actual_scores), 1) if actual_scores else round(baseline["average"] + adjustment, 1)
    trend = [round(max(0, min(10, value + adjustment)), 1) for value in baseline["trend"]]
    if actual_scores:
        trend[-1] = average
    scale = 1 if not series_id else max(.28, len(students) / max(1, len(_records("alunos", instituicao_id=institution_id))))
    if class_id:
        scale = max(.18, len(students) / max(1, len(_records("alunos", instituicao_id=institution_id))))
    absence_trend = [max(0, round(value * scale)) for value in baseline["absence_trend"]]
    return {
        "average": average,
        "attendance": round(min(99.9, baseline["attendance"] - adjustment), 1),
        "absences": sum(absence_trend),
        "students": len(students),
        "classes": len(classes),
        "trend": trend,
        "absence_trend": absence_trend,
        "has_actual_scores": bool(actual_scores),
    }


def school_report(institution):
    metrics = _metrics(institution["id"])
    series_rows = []
    for series in _records("series", instituicao_id=institution["id"]):
        series_rows.append({**series, **_metrics(institution["id"], series_id=series["id"])})
    series_rows.sort(key=lambda item: item["nome"])
    return {**institution, **metrics, "series": series_rows}


def series_report(institution, series):
    metrics = _metrics(institution["id"], series_id=series["id"])
    class_rows = []
    for school_class in _records("turmas", instituicao_id=institution["id"], serie_id=series["id"]):
        class_rows.append({**school_class, **_metrics(institution["id"], series_id=series["id"], class_id=school_class["id"])})
    class_rows.sort(key=lambda item: item["nome"])
    return {**series, **metrics, "classes_data": class_rows}


def class_report(institution, series, school_class):
    metrics = _metrics(institution["id"], series_id=series["id"], class_id=school_class["id"])
    students = []
    for student in _records("alunos", turma_id=school_class["id"]):
        offset = ((_numeric_id(student["id"]) % 5) - 2) * .25
        students.append({**student, "average": round(max(0, min(10, metrics["average"] + offset)), 1), "attendance": round(max(0, min(100, metrics["attendance"] - offset)), 1)})
    students.sort(key=lambda item: (-item["average"], item["nome"]))
    return {**school_class, **metrics, "students_data": students}


def institute_report():
    schools = [school_report(item) for item in DATA["instituicoes"] if item.get("status") == "Ativa"]
    ranking = sorted(schools, key=lambda item: (-item["average"], item["nome"]))
    return {"schools": schools, "ranking": ranking, "average": round(mean(item["average"] for item in schools), 1) if schools else 0}


def line_chart(values, label="Média", maximum=10):
    return {"labels": MONTHS, "datasets": [{"label": label, "values": values, "color": "#2d3d5f"}], "max": maximum}


def bar_chart(labels, values, label, maximum=None):
    return {"labels": labels, "datasets": [{"label": label, "values": values, "color": "#b96121"}], "max": maximum or max(values + [1])}
