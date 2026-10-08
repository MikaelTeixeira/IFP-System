from datetime import UTC, datetime

from .extensions import db


class Municipality(db.Model):
    __tablename__ = "municipios"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(120), nullable=False, index=True)
    state = db.Column("uf", db.String(2), nullable=False)
    code = db.Column("codigo", db.String(20), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "uf": self.state, "codigo": self.code, "status": self.status}


class Institution(db.Model):
    __tablename__ = "instituicoes"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(160), nullable=False, index=True)
    municipality_id = db.Column("municipio_id", db.String(16), db.ForeignKey("municipios.id"), nullable=False, index=True)
    code = db.Column("codigo", db.String(30), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="Ativa")
    municipality = db.relationship("Municipality", lazy="joined")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "municipio_id": self.municipality_id, "codigo": self.code, "status": self.status}


class UserAccount(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(160), nullable=False, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    role = db.Column("cargo", db.String(40), nullable=False, index=True)
    municipality_id = db.Column("municipio_id", db.String(16), db.ForeignKey("municipios.id"), nullable=True, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo", index=True)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))
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
    __tablename__ = "series"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(120), nullable=False, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    shift = db.Column("turno", db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa", index=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "instituicao_id": self.institution_id, "turno": self.shift, "status": self.status}


class SchoolClass(db.Model):
    __tablename__ = "turmas"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(120), nullable=False, index=True)
    series_id = db.Column("serie_id", db.String(16), db.ForeignKey("series.id"), nullable=False, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    school_year = db.Column("ano_letivo", db.String(8), nullable=False)
    shift = db.Column("turno", db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa", index=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "serie_id": self.series_id, "instituicao_id": self.institution_id, "ano_letivo": self.school_year, "turno": self.shift, "status": self.status}


class Student(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(160), nullable=False, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    enrollment = db.Column("matricula", db.String(40), nullable=False, unique=True)
    class_id = db.Column("turma_id", db.String(16), db.ForeignKey("turmas.id"), nullable=True, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    admission = db.Column("ingresso", db.String(20), nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="Ativa", index=True)
    user_account_id = db.Column("usuario_id", db.String(16), db.ForeignKey("usuarios.id"), nullable=True, unique=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "cpf": self.cpf, "email": self.email, "matricula": self.enrollment, "turma_id": self.class_id or "", "instituicao_id": self.institution_id, "ingresso": self.admission, "status": self.status, "_user_account_id": self.user_account_id or ""}


class Teacher(db.Model):
    __tablename__ = "professores"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(160), nullable=False, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    subject_ids = db.Column("disciplina_ids", db.JSON, nullable=False, default=list)
    class_ids = db.Column("turma_ids", db.JSON, nullable=False, default=list)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo", index=True)
    user_account_id = db.Column("usuario_id", db.String(16), db.ForeignKey("usuarios.id"), nullable=True, unique=True)

    def to_record(self):
        return {"id": self.id, "nome": self.name, "cpf": self.cpf, "email": self.email, "disciplina_ids": list(self.subject_ids or []), "turma_ids": list(self.class_ids or []), "instituicao_id": self.institution_id, "status": self.status, "_user_account_id": self.user_account_id or ""}


class Subject(db.Model):
    __tablename__ = "materias"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(140), nullable=False, index=True)
    scope = db.Column("escopo", db.String(20), nullable=False, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativa")
    created_by = db.Column("criado_por", db.String(160), nullable=False, default="")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "escopo": self.scope, "instituicao_id": self.institution_id or "", "status": self.status, "criado_por": self.created_by}


class Topic(db.Model):
    __tablename__ = "assuntos"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column("nome", db.String(160), nullable=False, index=True)
    subject_id = db.Column("materia_id", db.String(16), db.ForeignKey("materias.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Ativo")
    created_by = db.Column("criado_por", db.String(160), nullable=False, default="")

    def to_record(self):
        return {"id": self.id, "nome": self.name, "materia_id": self.subject_id, "status": self.status, "criado_por": self.created_by}


class Question(db.Model):
    __tablename__ = "questoes"

    id = db.Column(db.String(16), primary_key=True)
    subject_id = db.Column("materia_id", db.String(16), db.ForeignKey("materias.id"), nullable=False, index=True)
    topic_id = db.Column("assunto_id", db.String(16), db.ForeignKey("assuntos.id"), nullable=False, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    author_id = db.Column("autor_id", db.String(16), db.ForeignKey("professores.id"), nullable=False, index=True)
    subject_name = db.Column("disciplina", db.String(140), nullable=False)
    topic_name = db.Column("assunto", db.String(160), nullable=False)
    operation = db.Column("operacao", db.String(60), nullable=False)
    difficulty = db.Column("dificuldade", db.String(30), nullable=False)
    statement = db.Column("enunciado", db.Text, nullable=False)
    question_type = db.Column("tipo", db.String(20), nullable=False, default="objetiva")
    alternatives = db.Column("alternativas", db.JSON, nullable=False, default=dict)
    answer_key = db.Column("gabarito", db.String(8), nullable=False, default="")
    expected_answer = db.Column("resposta_esperada", db.Text, nullable=False, default="")
    explanation = db.Column("explicacao", db.Text, nullable=False, default="")
    author_name = db.Column("autor", db.String(160), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Ativa")
    image = db.Column("imagem", db.JSON, nullable=True)
    review_status = db.Column("revisao_status", db.String(30), nullable=False, default="", index=True)
    review_note = db.Column("revisao_observacao", db.Text, nullable=False, default="")
    review_requested_by = db.Column("revisao_solicitada_por", db.String(160), nullable=False, default="")
    review_requested_at = db.Column("revisao_solicitada_em", db.String(40), nullable=False, default="")
    review_requester_role = db.Column("revisao_solicitante_perfil", db.String(40), nullable=False, default="")
    review_requester_id = db.Column("revisao_solicitante_id", db.String(36), nullable=False, default="")
    review_answered_at = db.Column("revisao_respondida_em", db.String(40), nullable=False, default="")

    def to_record(self):
        return {"id": self.id, "materia_id": self.subject_id, "assunto_id": self.topic_id, "instituicao_id": self.institution_id, "autor_id": self.author_id, "disciplina": self.subject_name, "assunto": self.topic_name, "operacao": self.operation, "dificuldade": self.difficulty, "enunciado": self.statement, "tipo": self.question_type, "alternativas": dict(self.alternatives or {}), "gabarito": self.answer_key, "resposta_esperada": self.expected_answer, "explicacao": self.explanation, "autor": self.author_name, "status": self.status, "imagem": self.image, "revisao_status": self.review_status, "revisao_observacao": self.review_note, "revisao_solicitada_por": self.review_requested_by, "revisao_solicitada_em": self.review_requested_at, "revisao_solicitante_role": self.review_requester_role, "revisao_solicitante_id": self.review_requester_id, "revisao_respondida_em": self.review_answered_at}


class Assessment(db.Model):
    __tablename__ = "simulados"

    id = db.Column(db.String(24), primary_key=True)
    title = db.Column("titulo", db.String(200), nullable=False, index=True)
    subject = db.Column("disciplina", db.String(200), nullable=False)
    topic = db.Column("assunto", db.String(200), nullable=False)
    modality = db.Column("modalidade", db.String(40), nullable=False)
    audience = db.Column("publico", db.String(160), nullable=False)
    duration = db.Column("duracao", db.Integer, nullable=False)
    scheduled_date = db.Column("data_agendada", db.String(20), nullable=False, default="")
    status = db.Column(db.String(30), nullable=False, index=True)
    question_ids = db.Column("questao_ids", db.JSON, nullable=False, default=list)
    institution_ids = db.Column("instituicao_ids", db.JSON, nullable=False, default=list)
    series_ids = db.Column("serie_ids", db.JSON, nullable=False, default=list)
    description = db.Column("descricao", db.Text, nullable=False, default="")
    single_attempt = db.Column("tentativa_unica", db.Boolean, nullable=False, default=True)

    def to_record(self):
        return {"id": self.id, "titulo": self.title, "disciplina": self.subject, "assunto": self.topic, "modalidade": self.modality, "publico": self.audience, "duracao": self.duration, "data": self.scheduled_date, "status": self.status, "question_ids": list(self.question_ids or []), "instituicao_ids": list(self.institution_ids or []), "serie_ids": list(self.series_ids or []), "descricao": self.description, "tentativa_unica": self.single_attempt}


class AssessmentRequest(db.Model):
    __tablename__ = "solicitacoes_simulado"

    id = db.Column(db.String(24), primary_key=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    payload = db.Column("dados", db.JSON, nullable=False)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    def to_record(self):
        return dict(self.payload or {})


class MaterialPost(db.Model):
    __tablename__ = "materiais"

    id = db.Column(db.String(16), primary_key=True)
    title = db.Column("titulo", db.String(200), nullable=False, index=True)
    description = db.Column("descricao", db.Text, nullable=False)
    text = db.Column("texto", db.Text, nullable=False, default="")
    teacher_id = db.Column("professor_id", db.String(16), db.ForeignKey("professores.id"), nullable=False, index=True)
    subject_id = db.Column("materia_id", db.String(16), db.ForeignKey("materias.id"), nullable=False, index=True)
    topic_id = db.Column("assunto_id", db.String(16), db.ForeignKey("assuntos.id"), nullable=False, index=True)
    class_ids = db.Column("turma_ids", db.JSON, nullable=False, default=list)
    published_at = db.Column("publicado_em", db.String(40), nullable=False)
    attachment = db.Column("anexo", db.JSON, nullable=True)

    def to_record(self):
        return {"id": self.id, "titulo": self.title, "descricao": self.description, "texto": self.text, "professor_id": self.teacher_id, "materia_id": self.subject_id, "assunto_id": self.topic_id, "turma_ids": list(self.class_ids or []), "publicado_em": self.published_at, "anexo": self.attachment}


class ReportSnapshot(db.Model):
    __tablename__ = "indicadores_relatorio"

    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), primary_key=True)
    average = db.Column("media", db.Float, nullable=False)
    attendance = db.Column("frequencia", db.Float, nullable=False)
    absences = db.Column("faltas", db.Integer, nullable=False)
    performance_trend = db.Column("evolucao_desempenho", db.JSON, nullable=False)
    absence_trend = db.Column("evolucao_faltas", db.JSON, nullable=False)


class StudentAttendanceSummary(db.Model):
    __tablename__ = "frequencias_alunos"
    __table_args__ = (db.UniqueConstraint("aluno_id", "ano_letivo", name="uq_frequencia_aluno_ano"),)

    id = db.Column(db.String(36), primary_key=True)
    student_id = db.Column("aluno_id", db.String(16), db.ForeignKey("alunos.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = db.Column("instituicao_id", db.String(16), db.ForeignKey("instituicoes.id"), nullable=False, index=True)
    school_year = db.Column("ano_letivo", db.String(8), nullable=False, index=True)
    attendance = db.Column("frequencia", db.Float, nullable=False)
    absences = db.Column("faltas", db.Integer, nullable=False, default=0)
    latest_status = db.Column("ultima_situacao", db.String(20), nullable=False, default="Presente", index=True)


class StoredFile(db.Model):
    __tablename__ = "arquivos"

    id = db.Column(db.String(36), primary_key=True)
    owner_type = db.Column("tipo_dono", db.String(40), nullable=False, index=True)
    owner_id = db.Column("dono_id", db.String(36), nullable=False, index=True)
    path = db.Column("caminho", db.String(500), nullable=False, unique=True)
    original_name = db.Column("nome_original", db.String(255), nullable=False)
    mime_type = db.Column("tipo_mime", db.String(120), nullable=False)
    extension = db.Column("extensao", db.String(16), nullable=False)
    size = db.Column("tamanho", db.Integer, nullable=False)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class Notification(db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(db.String(36), primary_key=True)
    recipient_role = db.Column("perfil_destinatario", db.String(40), nullable=False, index=True)
    recipient_id = db.Column("destinatario_id", db.String(36), nullable=False, index=True)
    kind = db.Column("tipo", db.String(50), nullable=False, index=True)
    title = db.Column("titulo", db.String(180), nullable=False)
    message = db.Column("mensagem", db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    is_read = db.Column("lida", db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)


class QuestionReviewEvent(db.Model):
    __tablename__ = "historico_revisoes"

    id = db.Column(db.String(36), primary_key=True)
    question_id = db.Column("questao_id", db.String(36), nullable=False, index=True)
    request_id = db.Column("solicitacao_id", db.String(36), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    note = db.Column("observacao", db.Text, nullable=True)
    actor_role = db.Column("perfil_autor", db.String(40), nullable=False)
    actor_id = db.Column("autor_id", db.String(36), nullable=False)
    actor_name = db.Column("autor_nome", db.String(160), nullable=False)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)


class AssessmentAttempt(db.Model):
    __tablename__ = "tentativas"

    id = db.Column(db.String(36), primary_key=True)
    assessment_id = db.Column("simulado_id", db.String(36), nullable=False, index=True)
    student_id = db.Column("aluno_id", db.String(36), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default="Em andamento", index=True)
    started_at = db.Column("iniciada_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    submitted_at = db.Column("entregue_em", db.DateTime, nullable=True)
    duration_seconds = db.Column("duracao_segundos", db.Integer, nullable=False)
    remaining_seconds = db.Column("segundos_restantes", db.Integer, nullable=False)
    objective_score = db.Column("nota_objetiva", db.Float, nullable=False, default=0)
    final_score = db.Column("nota_final", db.Float, nullable=True)
    answers = db.relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan", lazy="selectin")


class AttemptAnswer(db.Model):
    __tablename__ = "respostas"
    __table_args__ = (db.UniqueConstraint("tentativa_id", "questao_id", name="uq_resposta_tentativa_questao"),)

    id = db.Column(db.String(36), primary_key=True)
    attempt_id = db.Column("tentativa_id", db.String(36), db.ForeignKey("tentativas.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column("questao_id", db.String(36), nullable=False, index=True)
    answer_text = db.Column("resposta", db.Text, nullable=False, default="")
    is_open = db.Column("aberta", db.Boolean, nullable=False, default=False)
    is_correct = db.Column("correta", db.Boolean, nullable=True)
    grade = db.Column("nota", db.Float, nullable=True)
    concept = db.Column("conceito", db.String(60), nullable=True)
    feedback = db.Column("comentario", db.Text, nullable=True)
    graded_at = db.Column("corrigida_em", db.DateTime, nullable=True)
    grader_id = db.Column("corretor_id", db.String(36), nullable=True)
    attempt = db.relationship("AssessmentAttempt", back_populates="answers")
<<<<<<< Updated upstream
=======


class AnswerSheet(db.Model):
    __tablename__ = "cartoes_resposta"

    id = db.Column(db.String(36), primary_key=True)
    assessment_id = db.Column("simulado_id", db.String(36), nullable=False, index=True)
    student_id = db.Column("aluno_id", db.String(36), nullable=False, index=True)
    template_version = db.Column("versao_modelo", db.String(40), nullable=False, default="A4-20-v2")
    snapshot = db.Column("dados_emissao", db.JSON, nullable=True)
    token_digest = db.Column("hash_token", db.String(64), nullable=False, unique=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="Emitido", index=True)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class AnswerScanBatch(db.Model):
    __tablename__ = "lotes_leitura"

    id = db.Column(db.String(36), primary_key=True)
    assessment_id = db.Column("simulado_id", db.String(36), nullable=False, index=True)
    original_name = db.Column("nome_original", db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Processando", index=True)
    page_count = db.Column("total_paginas", db.Integer, nullable=False, default=0)
    processed_count = db.Column("total_processadas", db.Integer, nullable=False, default=0)
    review_count = db.Column("total_revisao", db.Integer, nullable=False, default=0)
    failed_count = db.Column("total_falhas", db.Integer, nullable=False, default=0)
    created_by_role = db.Column("criado_por_perfil", db.String(40), nullable=False)
    created_by_id = db.Column("criado_por_id", db.String(36), nullable=False)
    scope = db.Column("escopo", db.JSON, nullable=True)
    error_message = db.Column("mensagem_erro", db.String(300), nullable=True)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)
    pages = db.relationship("AnswerScanPage", back_populates="batch", cascade="all, delete-orphan", lazy="selectin")


class AnswerScanPage(db.Model):
    __tablename__ = "paginas_leitura"
    __table_args__ = (db.UniqueConstraint("lote_id", "numero_pagina", name="uq_pagina_lote"),)

    id = db.Column(db.String(36), primary_key=True)
    batch_id = db.Column("lote_id", db.String(36), db.ForeignKey("lotes_leitura.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = db.Column("numero_pagina", db.Integer, nullable=False)
    answer_sheet_id = db.Column("cartao_id", db.String(36), nullable=True, index=True)
    student_id = db.Column("aluno_id", db.String(36), nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    image_path = db.Column("caminho_imagem", db.String(500), nullable=False)
    detected_answers = db.Column("respostas_detectadas", db.JSON, nullable=False, default=dict)
    confidence = db.Column("confianca", db.Float, nullable=False, default=0)
    issue = db.Column("problema", db.String(300), nullable=False, default="")
    analysis = db.Column("analise", db.JSON, nullable=True)
    created_at = db.Column("criado_em", db.DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    batch = db.relationship("AnswerScanBatch", back_populates="pages")
>>>>>>> Stashed changes
