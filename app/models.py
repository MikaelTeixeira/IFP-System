from datetime import UTC, datetime

from .extensions import db


class Municipality(db.Model):
    __tablename__ = "municipalities"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    state = db.Column(db.String(2), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "uf": self.state, "codigo": self.code, "status": self.status}


class Institution(db.Model):
    __tablename__ = "institutions"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    municipality_id = db.Column(db.String(16), db.ForeignKey("municipalities.id"), nullable=False, index=True)
    code = db.Column(db.String(30), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="Ativa")
    municipality = db.relationship("Municipality", lazy="joined")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "municipio_id": self.municipality_id, "codigo": self.code, "status": self.status}


class UserAccount(db.Model):
    __tablename__ = "user_accounts"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    role = db.Column(db.String(40), nullable=False, index=True)
    municipality_id = db.Column(db.String(16), db.ForeignKey("municipalities.id"), nullable=True, index=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    municipality = db.relationship("Municipality", lazy="joined")
    institution = db.relationship("Institution", lazy="joined")

    def to_record(self):
        return {
            "id": self.id,
            "nome": self.name,
            "cpf": self.cpf,
            "email": self.email,
            "cargo": self.role,
            "municipio_id": self.municipality_id or "",
            "instituicao_id": self.institution_id or "",
            "status": self.status,
        }


class GradeSeries(db.Model):
    __tablename__ = "grade_series"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=False, index=True)
    shift = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa", index=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "instituicao_id": self.institution_id, "turno": self.shift, "status": self.status}


class SchoolClass(db.Model):
    __tablename__ = "school_classes"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    series_id = db.Column(db.String(16), db.ForeignKey("grade_series.id"), nullable=False, index=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=False, index=True)
    school_year = db.Column(db.String(8), nullable=False)
    shift = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa", index=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "serie_id": self.series_id, "instituicao_id": self.institution_id, "ano_letivo": self.school_year, "turno": self.shift, "status": self.status}


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    enrollment = db.Column(db.String(40), nullable=False, unique=True)
    class_id = db.Column(db.String(16), db.ForeignKey("school_classes.id"), nullable=True, index=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=False, index=True)
    admission = db.Column(db.String(20), nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="Ativa", index=True)
    user_account_id = db.Column(db.String(16), db.ForeignKey("user_accounts.id"), nullable=True, unique=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "cpf": self.cpf, "email": self.email, "matricula": self.enrollment, "turma_id": self.class_id or "", "instituicao_id": self.institution_id, "ingresso": self.admission, "status": self.status, "_user_account_id": self.user_account_id or ""}


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    subject_ids = db.Column(db.JSON, nullable=False, default=list)
    class_ids = db.Column(db.JSON, nullable=False, default=list)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo", index=True)
    user_account_id = db.Column(db.String(16), db.ForeignKey("user_accounts.id"), nullable=True, unique=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "cpf": self.cpf, "email": self.email, "disciplina_ids": list(self.subject_ids or []), "turma_ids": list(self.class_ids or []), "instituicao_id": self.institution_id, "status": self.status, "_user_account_id": self.user_account_id or ""}


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(140), nullable=False, index=True)
    scope = db.Column(db.String(20), nullable=False, index=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativa")
    created_by = db.Column(db.String(160), nullable=False, default="")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "escopo": self.scope, "instituicao_id": self.institution_id or "", "status": self.status, "criado_por": self.created_by}


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    subject_id = db.Column(db.String(16), db.ForeignKey("subjects.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo")
    created_by = db.Column(db.String(160), nullable=False, default="")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "materia_id": self.subject_id, "status": self.status, "criado_por": self.created_by}


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.String(16), primary_key=True)
    subject_id = db.Column(db.String(16), db.ForeignKey("subjects.id"), nullable=False, index=True)
    topic_id = db.Column(db.String(16), db.ForeignKey("topics.id"), nullable=False, index=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=False, index=True)
    author_id = db.Column(db.String(16), db.ForeignKey("teachers.id"), nullable=False, index=True)
    subject_name = db.Column(db.String(140), nullable=False)
    topic_name = db.Column(db.String(160), nullable=False)
    operation = db.Column(db.String(60), nullable=False)
    difficulty = db.Column(db.String(30), nullable=False)
    statement = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False, default="objetiva")
    alternatives = db.Column(db.JSON, nullable=False, default=dict)
    answer_key = db.Column(db.String(8), nullable=False, default="")
    expected_answer = db.Column(db.Text, nullable=False, default="")
    explanation = db.Column(db.Text, nullable=False, default="")
    author_name = db.Column(db.String(160), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa")
    image = db.Column(db.JSON, nullable=True)
    review_status = db.Column(db.String(30), nullable=False, default="", index=True)
    review_note = db.Column(db.Text, nullable=False, default="")
    review_requested_by = db.Column(db.String(160), nullable=False, default="")
    review_requested_at = db.Column(db.String(40), nullable=False, default="")
    review_requester_role = db.Column(db.String(40), nullable=False, default="")
    review_requester_id = db.Column(db.String(36), nullable=False, default="")
    review_answered_at = db.Column(db.String(40), nullable=False, default="")

    def to_record(self):
        return {"id": self.id, "materia_id": self.subject_id, "assunto_id": self.topic_id, "instituicao_id": self.institution_id, "autor_id": self.author_id, "disciplina": self.subject_name, "assunto": self.topic_name, "operacao": self.operation, "dificuldade": self.difficulty, "enunciado": self.statement, "tipo": self.question_type, "alternativas": dict(self.alternatives or {}), "gabarito": self.answer_key, "resposta_esperada": self.expected_answer, "explicacao": self.explanation, "autor": self.author_name, "status": self.status, "imagem": self.image, "revisao_status": self.review_status, "revisao_observacao": self.review_note, "revisao_solicitada_por": self.review_requested_by, "revisao_solicitada_em": self.review_requested_at, "revisao_solicitante_role": self.review_requester_role, "revisao_solicitante_id": self.review_requester_id, "revisao_respondida_em": self.review_answered_at}


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.String(24), primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    modality = db.Column(db.String(40), nullable=False)
    audience = db.Column(db.String(160), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    scheduled_date = db.Column(db.String(20), nullable=False, default="")
    status = db.Column(db.String(30), nullable=False, index=True)
    question_ids = db.Column(db.JSON, nullable=False, default=list)
    institution_ids = db.Column(db.JSON, nullable=False, default=list)
    series_ids = db.Column(db.JSON, nullable=False, default=list)
    description = db.Column(db.Text, nullable=False, default="")
    single_attempt = db.Column(db.Boolean, nullable=False, default=True)

    def to_record(self):
        return {"id": self.id, "titulo": self.title, "disciplina": self.subject, "assunto": self.topic, "modalidade": self.modality, "publico": self.audience, "duracao": self.duration, "data": self.scheduled_date, "status": self.status, "question_ids": list(self.question_ids or []), "instituicao_ids": list(self.institution_ids or []), "serie_ids": list(self.series_ids or []), "descricao": self.description, "tentativa_unica": self.single_attempt}


class AssessmentRequest(db.Model):
    __tablename__ = "assessment_requests"

    id = db.Column(db.String(24), primary_key=True)
    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    def to_record(self):
        return dict(self.payload or {})


class MaterialPost(db.Model):
    __tablename__ = "material_posts"

    id = db.Column(db.String(16), primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=False, default="")
    teacher_id = db.Column(db.String(16), db.ForeignKey("teachers.id"), nullable=False, index=True)
    subject_id = db.Column(db.String(16), db.ForeignKey("subjects.id"), nullable=False, index=True)
    topic_id = db.Column(db.String(16), db.ForeignKey("topics.id"), nullable=False, index=True)
    class_ids = db.Column(db.JSON, nullable=False, default=list)
    published_at = db.Column(db.String(40), nullable=False)
    attachment = db.Column(db.JSON, nullable=True)

    def to_record(self):
        return {"id": self.id, "titulo": self.title, "descricao": self.description, "texto": self.text, "professor_id": self.teacher_id, "materia_id": self.subject_id, "assunto_id": self.topic_id, "turma_ids": list(self.class_ids or []), "publicado_em": self.published_at, "anexo": self.attachment}


class ReportSnapshot(db.Model):
    __tablename__ = "report_snapshots"

    institution_id = db.Column(db.String(16), db.ForeignKey("institutions.id"), primary_key=True)
    average = db.Column(db.Float, nullable=False)
    attendance = db.Column(db.Float, nullable=False)
    absences = db.Column(db.Integer, nullable=False)
    performance_trend = db.Column(db.JSON, nullable=False)
    absence_trend = db.Column(db.JSON, nullable=False)


class StoredFile(db.Model):
    __tablename__ = "stored_files"

    id = db.Column(db.String(36), primary_key=True)
    owner_type = db.Column(db.String(40), nullable=False, index=True)
    owner_id = db.Column(db.String(36), nullable=False, index=True)
    path = db.Column(db.String(500), nullable=False, unique=True)
    original_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(120), nullable=False)
    extension = db.Column(db.String(16), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True)
    recipient_role = db.Column(db.String(40), nullable=False, index=True)
    recipient_id = db.Column(db.String(36), nullable=False, index=True)
    kind = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)


class QuestionReviewEvent(db.Model):
    __tablename__ = "question_review_events"

    id = db.Column(db.String(36), primary_key=True)
    question_id = db.Column(db.String(36), nullable=False, index=True)
    request_id = db.Column(db.String(36), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    note = db.Column(db.Text, nullable=True)
    actor_role = db.Column(db.String(40), nullable=False)
    actor_id = db.Column(db.String(36), nullable=False)
    actor_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)


class AssessmentAttempt(db.Model):
    __tablename__ = "assessment_attempts"

    id = db.Column(db.String(36), primary_key=True)
    assessment_id = db.Column(db.String(36), nullable=False, index=True)
    student_id = db.Column(db.String(36), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="Em andamento", index=True)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    submitted_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=False)
    remaining_seconds = db.Column(db.Integer, nullable=False)
    objective_score = db.Column(db.Float, nullable=False, default=0)
    final_score = db.Column(db.Float, nullable=True)
    answers = db.relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan", lazy="selectin")


class AttemptAnswer(db.Model):
    __tablename__ = "attempt_answers"
    __table_args__ = (db.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),)

    id = db.Column(db.String(36), primary_key=True)
    attempt_id = db.Column(db.String(36), db.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.String(36), nullable=False, index=True)
    answer_text = db.Column(db.Text, nullable=False, default="")
    is_open = db.Column(db.Boolean, nullable=False, default=False)
    is_correct = db.Column(db.Boolean, nullable=True)
    grade = db.Column(db.Float, nullable=True)
    concept = db.Column(db.String(60), nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    grader_id = db.Column(db.String(36), nullable=True)
    attempt = db.relationship("AssessmentAttempt", back_populates="answers")
