from pathlib import Path

import click
from flask import current_app
from sqlalchemy import inspect, text

from .data.academic import DATA, INITIAL_DATA
from .data.assessments import ASSESSMENTS, ASSESSMENT_REQUESTS, INITIAL_ASSESSMENTS
from .data.curriculum import INITIAL_SUBJECTS, INITIAL_TOPICS, SUBJECTS, TOPICS
from .data.materials import INITIAL_MATERIAL_POSTS, MATERIAL_POSTS
from .data.questions import INITIAL_QUESTIONS, QUESTIONS
from .data.reports import SCHOOL_BASELINES
from .data.users import INITIAL_USER_ACCOUNTS, USER_ACCOUNTS
from .extensions import db
from .models import (
    Assessment, AssessmentRequest, GradeSeries, Institution, MaterialPost, Municipality, Question,
    ReportSnapshot, SchoolClass, StoredFile, Student, StudentAttendanceSummary, Subject, Teacher, Topic, UserAccount,
)


def _next_user_id():
    numbers = [int(item.id.rsplit("-", 1)[-1]) for item in UserAccount.query.all()]
    return f"usr-{max(numbers or [0]) + 1:03d}"


def _municipality_for_institution(institution_id):
    institution = db.session.get(Institution, institution_id)
    return institution.municipality_id if institution else None


def _account_for_person(item, role):
    account = UserAccount.query.filter_by(cpf=item["cpf"]).first()
    if not account:
        account = UserAccount(
            id=_next_user_id(), name=item["nome"], cpf=item["cpf"], email=item["email"], role=role,
            municipality_id=_municipality_for_institution(item["instituicao_id"]),
            institution_id=item["instituicao_id"], status=item.get("status", "Ativo"),
        )
        db.session.add(account)
        db.session.flush()
    return account.id


def _seed_reference_data():
    if Municipality.query.count() == 0:
        db.session.add_all([
            Municipality(id=item["id"], name=item["nome"], state=item["uf"], code=item["codigo"], status=item["status"])
            for item in INITIAL_DATA["municipios"]
        ])
        db.session.flush()
    if Institution.query.count() == 0:
        db.session.add_all([
            Institution(id=item["id"], name=item["nome"], municipality_id=item["municipio_id"], code=item["codigo"], status=item["status"])
            for item in INITIAL_DATA["instituicoes"]
        ])
        db.session.flush()
    if UserAccount.query.count() == 0:
        db.session.add_all([
            UserAccount(
                id=item["id"], name=item["nome"], cpf=item["cpf"], email=item["email"], role=item["cargo"],
                municipality_id=item["municipio_id"] or None, institution_id=item["instituicao_id"] or None,
                status=item["status"],
            )
            for item in INITIAL_USER_ACCOUNTS
        ])
        db.session.flush()
    if GradeSeries.query.count() == 0:
        db.session.add_all([
            GradeSeries(id=item["id"], name=item["nome"], institution_id=item["instituicao_id"], shift=item["turno"], status=item["status"])
            for item in INITIAL_DATA["series"]
        ])
        db.session.flush()
    if SchoolClass.query.count() == 0:
        db.session.add_all([
            SchoolClass(
                id=item["id"], name=item["nome"], series_id=item["serie_id"], institution_id=item["instituicao_id"],
                school_year=item["ano_letivo"], shift=item["turno"], status=item["status"],
            )
            for item in INITIAL_DATA["turmas"]
        ])
        db.session.flush()
    if Subject.query.count() == 0:
        db.session.add_all([
            Subject(
                id=item["id"], name=item["nome"], scope=item["escopo"], institution_id=item.get("instituicao_id") or None,
                status=item["status"], created_by=item.get("criado_por", ""),
            )
            for item in INITIAL_SUBJECTS
        ])
        db.session.flush()
    if Student.query.count() == 0:
        for item in INITIAL_DATA["alunos"]:
            db.session.add(Student(
                id=item["id"], name=item["nome"], cpf=item["cpf"], email=item["email"], enrollment=item["matricula"],
                class_id=item.get("turma_id") or None, institution_id=item["instituicao_id"], admission=item.get("ingresso", ""),
                status=item["status"], user_account_id=_account_for_person(item, "student"),
            ))
        db.session.flush()
    if Teacher.query.count() == 0:
        for item in INITIAL_DATA["professores"]:
            db.session.add(Teacher(
                id=item["id"], name=item["nome"], cpf=item["cpf"], email=item["email"],
                subject_ids=list(item.get("disciplina_ids", [])), class_ids=list(item.get("turma_ids", [])),
                institution_id=item["instituicao_id"], status=item["status"],
                user_account_id=_account_for_person(item, "teacher"),
            ))
        db.session.flush()
    if Topic.query.count() == 0:
        db.session.add_all([
            Topic(
                id=item["id"], name=item["nome"], subject_id=item["materia_id"], status=item["status"],
                created_by=item.get("criado_por", ""),
            )
            for item in INITIAL_TOPICS
        ])
        db.session.flush()
    if Question.query.count() == 0:
        db.session.add_all([
            Question(
                id=item["id"], subject_id=item["materia_id"], topic_id=item["assunto_id"],
                institution_id=item["instituicao_id"], author_id=item["autor_id"], subject_name=item["disciplina"],
                topic_name=item["assunto"], operation=item.get("operacao", ""), difficulty=item.get("dificuldade", ""),
                statement=item["enunciado"], question_type=item.get("tipo", "objetiva"),
                alternatives=dict(item.get("alternativas") or {}), answer_key=item.get("gabarito", ""),
                expected_answer=item.get("resposta_esperada", ""), explanation=item.get("explicacao", ""),
                author_name=item.get("autor", ""), status=item.get("status", "Ativa"), image=item.get("imagem"),
                review_status=item.get("revisao_status", ""), review_note=item.get("revisao_observacao", ""),
            )
            for item in INITIAL_QUESTIONS
        ])
        db.session.flush()
    if Assessment.query.count() == 0:
        db.session.add_all([
            Assessment(
                id=item["id"], title=item["titulo"], subject=item.get("disciplina", ""), topic=item.get("assunto", ""),
                modality=item.get("modalidade", "Remoto"), audience=item.get("publico", ""), duration=item.get("duracao", 40),
                scheduled_date=item.get("data", ""), status=item.get("status", "Rascunho"),
                question_ids=list(item.get("question_ids", [])), institution_ids=list(item.get("instituicao_ids", [])),
                series_ids=list(item.get("serie_ids", [])), description=item.get("descricao", ""),
                single_attempt=bool(item.get("tentativa_unica", True)),
            )
            for item in INITIAL_ASSESSMENTS
        ])
        db.session.flush()
    if MaterialPost.query.count() == 0:
        db.session.add_all([
            MaterialPost(
                id=item["id"], title=item["titulo"], description=item["descricao"], text=item.get("texto", ""),
                teacher_id=item["professor_id"], subject_id=item["materia_id"], topic_id=item["assunto_id"],
                class_ids=list(item.get("turma_ids", [])), published_at=item["publicado_em"], attachment=item.get("anexo"),
            )
            for item in INITIAL_MATERIAL_POSTS
        ])
    if ReportSnapshot.query.count() == 0:
        db.session.add_all([
            ReportSnapshot(
                institution_id=institution_id, average=values["average"], attendance=values["attendance"],
                absences=values["absences"], performance_trend=list(values["trend"]),
                absence_trend=list(values["absence_trend"]),
            )
            for institution_id, values in SCHOOL_BASELINES.items()
        ])
    for institution in Institution.query.all():
        students = Student.query.filter_by(institution_id=institution.id).order_by(Student.id).all()
        baseline = SCHOOL_BASELINES.get(institution.id, {"attendance": 0, "absences": 0})
        base_absences, remainder = divmod(int(baseline["absences"]), len(students)) if students else (0, 0)
        for index, student in enumerate(students):
            summary_id = f"{student.id}-2026"
            if db.session.get(StudentAttendanceSummary, summary_id):
                continue
            attendance_offset = ((index % 5) - 2) * .35
            db.session.add(StudentAttendanceSummary(
                id=summary_id,
                student_id=student.id,
                institution_id=institution.id,
                school_year="2026",
                attendance=round(max(0, min(100, baseline["attendance"] + attendance_offset)), 1),
                absences=base_absences + (1 if index < remainder else 0),
                latest_status="Ausente" if (index + 1) % 5 == 0 else "Presente",
            ))
    db.session.commit()


def _refresh_compatibility_data():
    DATA["municipios"][:] = [item.to_record() for item in Municipality.query.order_by(Municipality.id).all()]
    DATA["instituicoes"][:] = [item.to_record() for item in Institution.query.order_by(Institution.id).all()]
    DATA["series"][:] = [item.to_record() for item in GradeSeries.query.order_by(GradeSeries.id).all()]
    DATA["turmas"][:] = [item.to_record() for item in SchoolClass.query.order_by(SchoolClass.id).all()]
    DATA["alunos"][:] = [item.to_record() for item in Student.query.order_by(Student.id).all()]
    DATA["professores"][:] = [item.to_record() for item in Teacher.query.order_by(Teacher.id).all()]
    USER_ACCOUNTS[:] = [item.to_record() for item in UserAccount.query.order_by(UserAccount.id).all()]
    SUBJECTS[:] = [item.to_record() for item in Subject.query.order_by(Subject.id).all()]
    TOPICS[:] = [item.to_record() for item in Topic.query.order_by(Topic.id).all()]
    QUESTIONS[:] = [item.to_record() for item in Question.query.order_by(Question.id).all()]
    ASSESSMENTS[:] = [item.to_record() for item in Assessment.query.order_by(Assessment.id).all()]
    ASSESSMENT_REQUESTS[:] = [
        item.to_record() for item in AssessmentRequest.query.order_by(AssessmentRequest.created_at.desc()).all()
    ]
    MATERIAL_POSTS[:] = [item.to_record() for item in MaterialPost.query.order_by(MaterialPost.id.desc()).all()]


def _remove_orphan_file_records():
    valid_owners = {"material": {item["id"] for item in MATERIAL_POSTS}, "question": {item["id"] for item in QUESTIONS}}
    upload_root = Path(current_app.config["UPLOAD_ROOT"]).resolve()
    changed = False
    for record in StoredFile.query.all():
        if record.owner_type not in valid_owners or record.owner_id in valid_owners[record.owner_type]:
            continue
        candidate = (upload_root / record.path).resolve()
        if upload_root in candidate.parents and candidate.exists():
            candidate.unlink()
        db.session.delete(record)
        changed = True
    if changed:
        db.session.commit()


# Columns added after their table already existed in some database. create_all() creates
# missing tables but never alters existing ones; each entry must be nullable.
ADDED_COLUMNS = (("respostas", "gabarito"),)


def _add_missing_columns():
    inspector = inspect(db.engine)
    preparer = db.engine.dialect.identifier_preparer
    if_not_exists = "IF NOT EXISTS " if db.engine.dialect.name == "postgresql" else ""
    for table_name, column_name in ADDED_COLUMNS:
        if column_name in {column["name"] for column in inspector.get_columns(table_name)}:
            continue
        column = db.metadata.tables[table_name].c[column_name]
        db.session.execute(text(
            f"ALTER TABLE {preparer.format_table(column.table)} ADD COLUMN {if_not_exists}"
            f"{preparer.format_column(column)} {column.type.compile(dialect=db.engine.dialect)}"
        ))
    db.session.commit()


def create_and_seed_database():
    db.create_all()
    _add_missing_columns()
    if db.engine.dialect.name == "postgresql":
        _close_data_api()
    _seed_reference_data()
    _refresh_compatibility_data()
    _remove_orphan_file_records()


def _close_data_api():
    """Keep the application tables out of the Supabase Data API.

    Supabase publishes the public schema through PostgREST for the anon and
    authenticated roles. RLS with no policies hides every row from them, and
    revoking their table privileges removes what RLS does not cover (TRUNCATE).
    The application connects as the table owner, which neither step restricts.
    """
    preparer = db.engine.dialect.identifier_preparer
    api_roles = list(db.session.execute(text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")).scalars())
    for table in db.metadata.sorted_tables:
        name = preparer.format_table(table)
        db.session.execute(text(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY"))
        if api_roles:
            db.session.execute(text(f"REVOKE ALL ON TABLE {name} FROM {', '.join(api_roles)}"))
    db.session.commit()


def init_database(app):
    db.init_app(app)

    @app.cli.command("init-db")
    def init_db_command():
        """Create the configured database tables and initial records."""
        if not current_app.config["DATABASE_ENABLED"]:
            raise click.ClickException("Configure instance/database.env antes de inicializar o banco.")
        create_and_seed_database()
        click.echo("Tabelas criadas e dados iniciais carregados.")

    @app.cli.command("db-status")
    def db_status_command():
        """Show whether persistent database storage is enabled."""
        if not current_app.config["DATABASE_ENABLED"]:
            click.echo("Banco persistente desativado: configure instance/database.env.")
            return
        try:
            db.session.execute(db.select(Municipality).limit(1))
            click.echo(f"Banco {db.engine.dialect.name} conectado e respondendo ({db.engine.url.host}).")
        except Exception as exc:
            raise click.ClickException(f"Falha na conexão: {exc}") from exc

    if app.config["DATABASE_ENABLED"]:
        with app.app_context():
            create_and_seed_database()
