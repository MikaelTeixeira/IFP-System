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
