from datetime import datetime


ASSESSMENTS = [
    {
        "id": "sim-2026-001",
        "titulo": "Simulado teste - Operações primárias",
        "disciplina": "Matemática",
        "assunto": "Operações primárias",
        "modalidade": "Remoto",
        "publico": "9º ano",
        "duracao": 40,
        "data": "15/10/2026",
        "status": "Publicado",
        "question_ids": ["que-001", "que-003", "que-005", "que-007", "que-009", "que-011", "que-013", "que-015"],
        "instituicao_ids": ["inst-001", "inst-002", "inst-003", "inst-004"],
        "descricao": "Avaliação demonstrativa com duas questões de cada operação primária.",
        "tentativa_unica": True,
    }
]

ASSESSMENT_REQUESTS = []


def find_assessment(assessment_id):
    return next((assessment for assessment in ASSESSMENTS if assessment["id"] == assessment_id), None)


def add_assessment(values):
    sequence = max([int(item["id"].split("-")[-1]) for item in ASSESSMENTS] or [0]) + 1
    assessment = {"id": f"sim-2026-{sequence:03d}", "disciplina": "Matemática", "assunto": "Operações primárias", "status": "Rascunho", "tentativa_unica": True, **values}
    ASSESSMENTS.append(assessment)
    return assessment


def update_assessment(assessment_id, values):
    assessment = find_assessment(assessment_id)
    if assessment:
        assessment.update(values)
    return assessment


def add_assessment_request(values):
    sequence = max([int(item["id"].split("-")[-1]) for item in ASSESSMENT_REQUESTS] or [0]) + 1
    assessment_request = {
        "id": f"sol-2026-{sequence:03d}",
        "status": "Aguardando questões",
        "solicitado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        **values,
    }
    ASSESSMENT_REQUESTS.insert(0, assessment_request)
    return assessment_request


def find_assessment_request(request_id):
    return next((item for item in ASSESSMENT_REQUESTS if item["id"] == request_id), None)


def find_request_assignment(assessment_request, teacher_id, subject_id=None):
    return next((assignment for assignment in assessment_request.get("atribuicoes", [])
                 if assignment["professor_id"] == teacher_id
                 and (subject_id is None or assignment["materia_id"] == subject_id)), None)


def find_request_submission(assessment_request, question_id):
    for assignment in assessment_request.get("atribuicoes", []):
        for submission in assignment.get("entregas", []):
            if submission["question_id"] == question_id:
                return assignment, submission
    return None, None


def refresh_request_status(assessment_request):
    if assessment_request.get("status") == "Agendado":
        return assessment_request["status"]
    assignments = assessment_request.get("atribuicoes", [])
    submissions = [submission for item in assignments for submission in item.get("entregas", [])]
    ready = bool(assignments) and all(
        item.get("entregas") and all(submission["status"] == "Aprovada" for submission in item["entregas"])
        for item in assignments
    )
    if ready:
        assessment_request["status"] = "Pronto para agendar"
    elif submissions:
        assessment_request["status"] = "Em avaliação"
    else:
        assessment_request["status"] = "Aguardando questões"
    return assessment_request["status"]


def submit_request_question(assessment_request, teacher_id, subject_id, question_id, source):
    assignment = find_request_assignment(assessment_request, teacher_id, subject_id)
    if not assignment:
        return None
    assignment.setdefault("entregas", [])
    existing = next((item for item in assignment["entregas"] if item["question_id"] == question_id), None)
    if existing:
        existing.update({"origem": source, "status": "Reenviada", "enviado_em": datetime.now().strftime("%d/%m/%Y às %H:%M")})
        existing.pop("revisao_observacao", None)
    else:
        existing = {
            "question_id": question_id,
            "origem": source,
            "status": "Enviada",
            "enviado_em": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        }
        assignment["entregas"].append(existing)
    refresh_request_status(assessment_request)
    return existing


def update_submissions_after_question_edit(question_id):
    updated = False
    for assessment_request in ASSESSMENT_REQUESTS:
        _, submission = find_request_submission(assessment_request, question_id)
        if submission and submission["status"] == "Revisão solicitada":
            submission["status"] = "Reenviada"
            submission["enviado_em"] = datetime.now().strftime("%d/%m/%Y às %H:%M")
            refresh_request_status(assessment_request)
            updated = True
    return updated


def teacher_request_history(teacher_id, subject_id=None, exclude_request_id=None):
    history = []
    seen = set()
    for assessment_request in ASSESSMENT_REQUESTS:
        if assessment_request["id"] == exclude_request_id:
            continue
        for assignment in assessment_request.get("atribuicoes", []):
            if assignment["professor_id"] != teacher_id or (subject_id and assignment["materia_id"] != subject_id):
                continue
            for submission in assignment.get("entregas", []):
                if submission["question_id"] not in seen:
                    seen.add(submission["question_id"])
                    history.append(submission["question_id"])
    return history
