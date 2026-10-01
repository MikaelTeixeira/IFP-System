const shell = document.querySelector("[data-app-shell]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const menuClose = document.querySelector("[data-menu-close]");
const sidebar = document.querySelector("[data-sidebar]");

function setMenu(open, restoreFocus = false) {
  if (!shell || !menuToggle) return;
  const compact = window.innerWidth < 1024;
  const shouldOpen = compact && open;
  shell.classList.toggle("menu-open", shouldOpen);
  menuToggle.setAttribute("aria-expanded", String(shouldOpen));
  document.body.style.overflow = shouldOpen ? "hidden" : "";
  if (sidebar) {
    sidebar.toggleAttribute("inert", compact && !shouldOpen);
    if (compact && !shouldOpen) sidebar.setAttribute("aria-hidden", "true");
    else sidebar.removeAttribute("aria-hidden");
  }
  if (shouldOpen) window.requestAnimationFrame(() => sidebar?.querySelector(".nav-link")?.focus());
  else if (restoreFocus) menuToggle.focus();
}

menuToggle?.addEventListener("click", () => setMenu(!shell.classList.contains("menu-open")));
menuClose?.addEventListener("click", () => setMenu(false, true));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && shell?.classList.contains("menu-open")) setMenu(false, true);
});
window.addEventListener("resize", () => {
  if (window.innerWidth >= 1024) setMenu(false);
});
setMenu(false);

const subjectSelect = document.querySelector("[data-subject-select]");
const topicSelect = document.querySelector("[data-topic-select]");

function updateTopicOptions(reset = false) {
  if (!subjectSelect || !topicSelect) return;
  const subjectId = subjectSelect.value;
  const emptyOption = topicSelect.querySelector('option[value=""]');
  if (emptyOption) emptyOption.textContent = subjectId ? "Selecione um assunto" : "Selecione a matéria primeiro";
  topicSelect.disabled = !subjectId;
  Array.from(topicSelect.options).forEach((option) => {
    if (!option.value) return;
    option.hidden = option.dataset.subject !== subjectId;
    option.disabled = option.dataset.subject !== subjectId;
  });
  if (reset && topicSelect.selectedOptions[0]?.dataset.subject !== subjectId) {
    topicSelect.value = "";
  }
}

subjectSelect?.addEventListener("change", () => updateTopicOptions(true));
updateTopicOptions();

const materialTeacherSelect = document.querySelector("[data-material-teacher-select]");
materialTeacherSelect?.addEventListener("change", () => {
  const destination = new URL(materialTeacherSelect.dataset.materialTeacherUrl, window.location.origin);
  destination.searchParams.set("professor_id", materialTeacherSelect.value);
  window.location.assign(destination);
});

const municipalityFilter = document.querySelector("[data-municipality-filter]");
const institutionFilter = document.querySelector("#instituicao_id");

function updateInstitutionOptions() {
  if (!municipalityFilter || !institutionFilter) return;
  const municipalityId = municipalityFilter.value;
  Array.from(institutionFilter.options).forEach((option) => {
    if (!option.value) return;
    const visible = !municipalityId || option.dataset.municipality === municipalityId;
    option.hidden = !visible;
    option.disabled = !visible;
  });
  if (institutionFilter.selectedOptions[0]?.disabled) institutionFilter.value = "";
}

municipalityFilter?.addEventListener("change", updateInstitutionOptions);
updateInstitutionOptions();

const scopeSelect = document.querySelector("[data-scope-select]");
const institutionScope = document.querySelector("[data-institution-scope]");

function updateScopeField() {
  if (!scopeSelect || !institutionScope) return;
  institutionScope.hidden = scopeSelect.value !== "instituicao";
}

scopeSelect?.addEventListener("change", updateScopeField);
updateScopeField();

const studentAssessmentForm = document.querySelector("[data-student-assessment-form]");
const answerWarning = document.querySelector("[data-answer-warning]");
const missingQuestionsList = answerWarning?.querySelector("[data-missing-questions]");
const assessmentProgress = document.querySelector("[data-assessment-progress]");

function unansweredQuestions() {
  if (!studentAssessmentForm) return [];
  return Array.from(studentAssessmentForm.querySelectorAll("[data-question-number]")).filter(
    (question) => {
      const openAnswer = question.querySelector("[data-open-answer]");
      if (openAnswer) return !openAnswer.value.trim();
      return !question.querySelector("input[type='radio']:checked");
    }
  );
}

function updateAssessmentProgress() {
  if (!studentAssessmentForm || !assessmentProgress) return;
  const questions = Array.from(studentAssessmentForm.querySelectorAll("[data-question-number]"));
  const unanswered = unansweredQuestions();
  const answered = questions.length - unanswered.length;
  const answeredCount = assessmentProgress.querySelector("[data-answered-count]");
  const progressBar = assessmentProgress.querySelector("[role='progressbar']");
  const progressFill = assessmentProgress.querySelector("[data-progress-fill]");
  if (answeredCount) answeredCount.textContent = String(answered);
  if (progressBar) progressBar.setAttribute("aria-valuenow", String(answered));
  if (progressFill) progressFill.style.width = `${questions.length ? (answered / questions.length) * 100 : 0}%`;
  questions.forEach((question) => {
    const answeredQuestion = !unanswered.includes(question);
    question.classList.toggle("is-answered", answeredQuestion);
    if (answeredQuestion) question.classList.remove("is-unanswered");
  });
}

function showAnswerWarning(questions) {
  if (!answerWarning || !missingQuestionsList) return;
  missingQuestionsList.replaceChildren(...questions.map((question) => {
    const item = document.createElement("li");
    item.textContent = `Questão ${question.dataset.questionNumber}`;
    return item;
  }));
  if (!answerWarning.open) answerWarning.showModal();
}

studentAssessmentForm?.addEventListener("submit", (event) => {
  const unanswered = unansweredQuestions();
  studentAssessmentForm.querySelectorAll("[data-question-number]").forEach((question) => {
    question.classList.toggle("is-unanswered", unanswered.includes(question));
  });
  if (!unanswered.length) return;
  event.preventDefault();
  showAnswerWarning(unanswered);
});

answerWarning?.addEventListener("close", () => {
  unansweredQuestions()[0]?.scrollIntoView({ behavior: "smooth", block: "center" });
});

if (answerWarning?.hasAttribute("data-open-on-load")) answerWarning.showModal();

const assessmentTimer = document.querySelector("[data-assessment-timer]");

if (assessmentTimer) {
  const timerValue = assessmentTimer.querySelector("[data-timer-value]");
  const timerLabel = assessmentTimer.querySelector("span");
  const remainingMs = Number(assessmentTimer.dataset.remainingSeconds) * 1000;
  const deadline = Date.now() + remainingMs;

  const updateTimer = () => {
    const remainingSeconds = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    const hours = Math.floor(remainingSeconds / 3600);
    const minutes = Math.floor((remainingSeconds % 3600) / 60);
    const seconds = remainingSeconds % 60;
    timerValue.textContent = hours
      ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
      : `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    if (!remainingSeconds) {
      assessmentTimer.classList.add("is-ended");
      timerLabel.textContent = "Tempo encerrado";
      studentAssessmentForm?.querySelectorAll("input, textarea, button[type='submit']").forEach((field) => {
        field.disabled = true;
      });
      window.clearInterval(timerInterval);
    }
  };

  const timerInterval = window.setInterval(updateTimer, 1000);
  updateTimer();
}

const timeExpiredDialog = document.querySelector("[data-time-expired-dialog][data-open-on-load]");
if (timeExpiredDialog && !timeExpiredDialog.open) timeExpiredDialog.showModal();

let assessmentSaveTimer;
const saveAssessmentProgress = async () => {
  if (!studentAssessmentForm?.dataset.saveUrl) return;
  try {
    await fetch(studentAssessmentForm.dataset.saveUrl, {
      method: "POST",
      body: new FormData(studentAssessmentForm),
      headers: { "X-Requested-With": "fetch" },
    });
  } catch (_) {
    // A próxima alteração fará uma nova tentativa; a entrega continua disponível.
  }
};

studentAssessmentForm?.addEventListener("input", () => {
  updateAssessmentProgress();
  window.clearTimeout(assessmentSaveTimer);
  assessmentSaveTimer = window.setTimeout(saveAssessmentProgress, 600);
});
studentAssessmentForm?.addEventListener("change", () => {
  updateAssessmentProgress();
  saveAssessmentProgress();
});
updateAssessmentProgress();
window.addEventListener("pagehide", () => {
  if (studentAssessmentForm?.dataset.saveUrl) {
    navigator.sendBeacon(studentAssessmentForm.dataset.saveUrl, new FormData(studentAssessmentForm));
  }
});

const userStatusDialog = document.querySelector("[data-user-status-dialog]");
const userStatusTitle = userStatusDialog?.querySelector("[data-user-status-title]");
const userStatusMessage = userStatusDialog?.querySelector("[data-user-status-message]");
const userStatusConfirm = userStatusDialog?.querySelector("[data-user-status-confirm]");
let userStatusAction = "";

document.querySelectorAll("[data-user-status]").forEach((button) => {
  button.addEventListener("click", () => {
    const deactivating = button.dataset.userState === "Ativo";
    userStatusAction = button.dataset.userAction;
    userStatusTitle.textContent = deactivating ? "Desativar usuário?" : "Ativar usuário?";
    userStatusMessage.textContent = deactivating
      ? `O acesso de ${button.dataset.userName} será interrompido até uma nova ativação.`
      : `O acesso de ${button.dataset.userName} será liberado novamente.`;
    userStatusConfirm.textContent = deactivating ? "Desativar" : "Ativar";
    userStatusConfirm.classList.toggle("button--danger", deactivating);
    userStatusConfirm.classList.toggle("button--primary", !deactivating);
    userStatusDialog.classList.toggle("site-dialog--danger", deactivating);
    userStatusDialog.classList.toggle("site-dialog--info", !deactivating);
    userStatusDialog.showModal();
  });
});

userStatusConfirm?.addEventListener("click", () => {
  if (!userStatusAction) return;
  const form = document.createElement("form");
  form.method = "post";
  form.action = userStatusAction;
  document.body.append(form);
  form.submit();
});

const materialDeleteDialog = document.querySelector("[data-material-delete-dialog]");
const materialDeleteMessage = materialDeleteDialog?.querySelector("[data-material-delete-message]");
const materialDeleteConfirm = materialDeleteDialog?.querySelector("[data-material-delete-confirm]");
let materialDeleteAction = "";

document.querySelectorAll("[data-material-delete]").forEach((button) => {
  button.addEventListener("click", () => {
    materialDeleteAction = button.dataset.materialAction;
    materialDeleteMessage.textContent = `A publicação “${button.dataset.materialName}” deixará de aparecer para as turmas selecionadas.`;
    materialDeleteDialog.showModal();
  });
});

materialDeleteConfirm?.addEventListener("click", () => {
  if (!materialDeleteAction) return;
  const form = document.createElement("form");
  form.method = "post";
  form.action = materialDeleteAction;
  document.body.append(form);
  form.submit();
});

const adminDeleteDialog = document.querySelector("[data-admin-delete-dialog]");
const adminDeleteTitle = adminDeleteDialog?.querySelector("[data-admin-delete-title]");
const adminDeleteMessage = adminDeleteDialog?.querySelector("[data-admin-delete-message]");
const adminDeleteConfirm = adminDeleteDialog?.querySelector("[data-admin-delete-confirm]");
let adminDeleteAction = "";

document.querySelectorAll("[data-admin-delete]").forEach((button) => {
  button.addEventListener("click", () => {
    adminDeleteAction = button.dataset.adminDeleteAction;
    if (adminDeleteTitle) adminDeleteTitle.textContent = `Excluir ${button.dataset.adminDeleteLabel}?`;
    if (adminDeleteMessage) adminDeleteMessage.textContent = button.dataset.adminDeleteMessage || "Esta ação removerá o registro definitivamente.";
    adminDeleteDialog?.showModal();
  });
});

adminDeleteConfirm?.addEventListener("click", () => {
  if (!adminDeleteAction) return;
  const form = document.createElement("form");
  form.method = "post";
  form.action = adminDeleteAction;
  document.body.append(form);
  form.submit();
});

const topicDeleteDialog = document.querySelector("[data-topic-delete-dialog]");
const topicDeleteMessage = topicDeleteDialog?.querySelector("[data-topic-delete-message]");
const topicDeleteConfirm = topicDeleteDialog?.querySelector("[data-topic-delete-confirm]");
let topicDeleteAction = "";

document.querySelectorAll("[data-topic-delete]").forEach((button) => {
  button.addEventListener("click", () => {
    topicDeleteAction = button.dataset.topicAction;
    topicDeleteMessage.textContent = `O assunto “${button.dataset.topicName}” será removido desta matéria.`;
    topicDeleteDialog.showModal();
  });
});

topicDeleteConfirm?.addEventListener("click", () => {
  if (!topicDeleteAction) return;
  const form = document.createElement("form");
  form.method = "post";
  form.action = topicDeleteAction;
  document.body.append(form);
  form.submit();
});

const questionRevisionDialog = document.querySelector("[data-question-revision-dialog]");
const questionRevisionForm = questionRevisionDialog?.querySelector("[data-question-revision-form]");
const questionRevisionMessage = questionRevisionDialog?.querySelector("[data-question-revision-message]");
const questionRevisionNote = questionRevisionForm?.querySelector("textarea");

document.querySelectorAll("[data-request-question-revision]").forEach((button) => {
  button.addEventListener("click", () => {
    questionRevisionForm.action = button.dataset.questionAction;
    questionRevisionMessage.textContent = `Explique ao professor o que precisa ser ajustado na ${button.dataset.questionName.toLowerCase()}.`;
    questionRevisionNote.value = "";
    questionRevisionDialog.showModal();
    questionRevisionNote.focus();
  });
});

questionRevisionDialog?.querySelector("[data-question-revision-close]")?.addEventListener("click", () => {
  questionRevisionDialog.close();
});

const submissionRevisionDialog = document.querySelector("[data-submission-revision-dialog]");
const submissionRevisionForm = submissionRevisionDialog?.querySelector("[data-submission-revision-form]");
const submissionRevisionMessage = submissionRevisionDialog?.querySelector("[data-submission-revision-message]");
const submissionRevisionNote = submissionRevisionForm?.querySelector("textarea");

document.querySelectorAll("[data-request-submission-revision]").forEach((button) => {
  button.addEventListener("click", () => {
    submissionRevisionForm.action = button.dataset.questionAction;
    submissionRevisionMessage.textContent = `Explique o ajuste necessário na ${button.dataset.questionName.toLowerCase()}.`;
    submissionRevisionNote.value = "";
    submissionRevisionDialog.showModal();
    submissionRevisionNote.focus();
  });
});

submissionRevisionDialog?.querySelector("[data-submission-revision-close]")?.addEventListener("click", () => {
  submissionRevisionDialog.close();
});

const assessmentRequestForm = document.querySelector("[data-assessment-request-form]");

function updateTeacherAssignments() {
  if (!assessmentRequestForm) return;
  const selectedSubjects = new Set(
    Array.from(assessmentRequestForm.querySelectorAll("[data-request-subject]:checked"), (input) => input.value)
  );
  assessmentRequestForm.querySelectorAll("[data-assignment-subject]").forEach((row) => {
    const active = selectedSubjects.has(row.dataset.assignmentSubject);
    row.hidden = !active;
    row.querySelectorAll("select, input").forEach((field) => {
      field.disabled = !active;
    });
  });
  const emptyMessage = assessmentRequestForm.querySelector("[data-assignment-empty]");
  if (emptyMessage) emptyMessage.hidden = selectedSubjects.size > 0;
}

assessmentRequestForm?.querySelectorAll("[data-request-subject]").forEach((input) => {
  input.addEventListener("change", updateTeacherAssignments);
});
updateTeacherAssignments();

const requestQuestionPicker = document.querySelector("[data-request-question-picker]");
const questionSelectionDialog = document.querySelector("[data-question-selection-dialog]");
const questionSelectionMessage = questionSelectionDialog?.querySelector("[data-question-selection-message]");
const requestQuestionOptions = requestQuestionPicker
  ? Array.from(requestQuestionPicker.querySelectorAll("[data-request-question-option]"))
  : [];
let requestQuestionSelectionOrder = requestQuestionOptions.filter((option) => option.checked);

function selectedRequestQuestions() {
  return requestQuestionPicker
    ? Array.from(requestQuestionPicker.querySelectorAll("[data-request-question-option]:checked"))
    : [];
}

function showQuestionSelectionDialog(message) {
  if (!questionSelectionDialog) return;
  questionSelectionMessage.textContent = message;
  if (!questionSelectionDialog.open) questionSelectionDialog.showModal();
}

function updateQuestionSelectionCounter() {
  if (!requestQuestionPicker) return;
  const required = Number(requestQuestionPicker.dataset.requiredCount);
  const selected = selectedRequestQuestions().length;
  const counter = requestQuestionPicker.querySelector("[data-question-selection-counter]");
  if (counter) counter.textContent = `${selected} de ${required} selecionada${selected === 1 ? "" : "s"}`;
}

function questionCountLabel(count) {
  return count === 1 ? "questão" : "questões";
}

requestQuestionOptions.forEach((option) => {
  option.addEventListener("change", () => {
    const required = Number(requestQuestionPicker.dataset.requiredCount);
    requestQuestionSelectionOrder = requestQuestionSelectionOrder.filter((item) => item !== option);
    if (option.checked) {
      requestQuestionSelectionOrder.push(option);
      if (selectedRequestQuestions().length > required) {
        const replacedOption = [...requestQuestionSelectionOrder]
          .reverse()
          .find((item) => item !== option && item.checked);
        if (replacedOption) {
          replacedOption.checked = false;
          requestQuestionSelectionOrder = requestQuestionSelectionOrder.filter((item) => item !== replacedOption);
        }
      }
    }
    updateQuestionSelectionCounter();
  });
});

requestQuestionPicker?.addEventListener("submit", (event) => {
  const required = Number(requestQuestionPicker.dataset.requiredCount);
  const selected = selectedRequestQuestions().length;
  if (selected === required) return;
  event.preventDefault();
  const missing = required - selected;
  showQuestionSelectionDialog(
    missing > 0
      ? `Selecione mais ${missing} ${questionCountLabel(missing)}. A coordenação solicitou exatamente ${required}.`
      : `Mantenha somente ${required} ${questionCountLabel(required)} ${required === 1 ? "selecionada" : "selecionadas"}.`
  );
});

if (questionSelectionDialog?.hasAttribute("data-open-on-load") && !questionSelectionDialog.open) {
  questionSelectionDialog.showModal();
}
updateQuestionSelectionCounter();

document.querySelectorAll("[data-bold-target]").forEach((button) => {
  button.addEventListener("click", () => {
    const field = document.getElementById(button.dataset.boldTarget);
    if (!field) return;
    const start = field.selectionStart ?? field.value.length;
    const end = field.selectionEnd ?? start;
    const selected = field.value.slice(start, end) || "texto em negrito";
    field.setRangeText(`**${selected}**`, start, end, "select");
    field.focus();
  });
});

const questionType = document.querySelector("[data-question-type]");
const objectiveFields = document.querySelector("[data-objective-fields]");
const openFields = document.querySelector("[data-open-fields]");

function updateQuestionTypeFields() {
  if (!questionType || !objectiveFields || !openFields) return;
  const isOpen = questionType.value === "aberta";
  objectiveFields.hidden = isOpen;
  openFields.hidden = !isOpen;
}

questionType?.addEventListener("change", updateQuestionTypeFields);
updateQuestionTypeFields();

const protectedAssessment = document.querySelector("[data-protected-assessment]");
const protectionDialog = document.querySelector("[data-assessment-protection-dialog]");
const privacyScreen = document.querySelector("[data-assessment-privacy-screen]");

function showProtectionWarning() {
  if (protectionDialog && !protectionDialog.open) protectionDialog.showModal();
}

if (protectedAssessment) {
  ["copy", "cut", "paste", "contextmenu", "dragstart"].forEach((eventName) => {
    protectedAssessment.addEventListener(eventName, (event) => {
      event.preventDefault();
      showProtectionWarning();
    });
  });
  document.addEventListener("keydown", (event) => {
    const blockedShortcut = (event.ctrlKey || event.metaKey) && ["c", "x", "v", "p"].includes(event.key.toLowerCase());
    if (blockedShortcut || event.key === "PrintScreen") {
      event.preventDefault();
      showProtectionWarning();
    }
  });
  window.addEventListener("blur", () => {
    privacyScreen.hidden = false;
  });
  window.addEventListener("focus", () => {
    privacyScreen.hidden = true;
  });
}

function initializeCorrectionCarousel(section) {
  const track = section.querySelector("[data-carousel-track]");
  const items = Array.from(section.querySelectorAll("[data-carousel-item]"));
  const previous = section.querySelector("[data-carousel-previous]");
  const next = section.querySelector("[data-carousel-next]");
  const position = section.querySelector("[data-carousel-position]");
  if (!track || !items.length || !previous || !next || !position) return;

  const itemStep = () => items[1]?.offsetLeft - items[0].offsetLeft || track.clientWidth;
  const visibleItems = () => Math.max(1, Math.round(track.clientWidth / itemStep()));
  const maximumIndex = () => Math.max(0, items.length - visibleItems());
  const currentIndex = () => Math.min(maximumIndex(), Math.max(0, Math.round(track.scrollLeft / itemStep())));

  function updateCarouselState() {
    const index = currentIndex();
    const visible = visibleItems();
    const first = index + 1;
    const last = Math.min(items.length, index + visible);
    position.textContent = first === last ? `${first} de ${items.length}` : `${first}–${last} de ${items.length}`;
    previous.disabled = index === 0;
    next.disabled = index >= maximumIndex();
  }

  function goTo(index) {
    const target = Math.min(maximumIndex(), Math.max(0, index));
    track.scrollTo({ left: items[target].offsetLeft, behavior: "smooth" });
  }

  previous.addEventListener("click", () => goTo(currentIndex() - 1));
  next.addEventListener("click", () => goTo(currentIndex() + 1));
  track.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    goTo(currentIndex() + (event.key === "ArrowRight" ? 1 : -1));
  });
  let updateFrame;
  track.addEventListener("scroll", () => {
    cancelAnimationFrame(updateFrame);
    updateFrame = requestAnimationFrame(updateCarouselState);
  });
  window.addEventListener("resize", updateCarouselState);
  updateCarouselState();
}

document.querySelectorAll(".correction-carousel-section").forEach(initializeCorrectionCarousel);

function renderReportChart(chart) {
  const configNode = chart.querySelector("[data-chart-config]");
  const canvas = chart.querySelector("[data-chart-canvas]");
  const legend = chart.querySelector("[data-chart-legend]");
  if (!configNode || !canvas) return;
  const config = JSON.parse(configNode.textContent);
  const labels = config.labels || [];
  const datasets = config.datasets || [];
  if (!labels.length || !datasets.length) return;
  const width = 720;
  const height = 280;
  const margin = { top: 28, right: 22, bottom: 48, left: 42 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const maximum = Math.max(Number(config.max) || 0, ...datasets.flatMap((item) => item.values.map(Number)), 1);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-hidden", "true");
  const add = (name, attrs, content = "") => {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    element.textContent = content;
    svg.appendChild(element);
    return element;
  };
  for (let step = 0; step <= 4; step += 1) {
    const y = margin.top + plotHeight - (step / 4) * plotHeight;
    add("line", { x1: margin.left, y1: y, x2: width - margin.right, y2: y, class: "chart-grid" });
    add("text", { x: margin.left - 9, y: y + 4, "text-anchor": "end" }, (maximum * step / 4).toFixed(maximum <= 10 ? 1 : 0).replace(".", ","));
  }
  labels.forEach((label, index) => {
    const x = margin.left + (labels.length === 1 ? plotWidth / 2 : index * plotWidth / (labels.length - 1));
    add("text", { x, y: height - 17, "text-anchor": "middle" }, label.length > 14 ? `${label.slice(0, 12)}…` : label);
  });
  if (chart.dataset.reportChart === "bar") {
    const groupWidth = plotWidth / labels.length;
    const barWidth = Math.min(54, groupWidth * .58 / datasets.length);
    datasets.forEach((dataset, datasetIndex) => dataset.values.forEach((rawValue, index) => {
      const value = Number(rawValue);
      const barHeight = value / maximum * plotHeight;
      const x = margin.left + index * groupWidth + (groupWidth - barWidth * datasets.length) / 2 + datasetIndex * barWidth;
      const y = margin.top + plotHeight - barHeight;
      add("rect", { x, y, width: barWidth - 3, height: barHeight, rx: 4, fill: dataset.color || "#b96121" });
      add("text", { x: x + (barWidth - 3) / 2, y: Math.max(14, y - 7), "text-anchor": "middle", class: "chart-value" }, String(rawValue).replace(".", ","));
    }));
  } else {
    datasets.forEach((dataset) => {
      const points = dataset.values.map((rawValue, index) => {
        const x = margin.left + (labels.length === 1 ? plotWidth / 2 : index * plotWidth / (labels.length - 1));
        const y = margin.top + plotHeight - Number(rawValue) / maximum * plotHeight;
        return { x, y, value: rawValue };
      });
      add("path", { d: points.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" "), stroke: dataset.color || "#2d3d5f", class: "chart-line" });
      points.forEach((point) => {
        add("circle", { cx: point.x, cy: point.y, r: 5, fill: dataset.color || "#2d3d5f", class: "chart-point" });
        if (datasets.length === 1) add("text", { x: point.x, y: point.y - 11, "text-anchor": "middle", class: "chart-value" }, String(point.value).replace(".", ","));
      });
    });
  }
  add("line", { x1: margin.left, y1: margin.top + plotHeight, x2: width - margin.right, y2: margin.top + plotHeight, class: "chart-axis" });
  canvas.replaceChildren(svg);
  if (legend && datasets.length > 1) {
    const entries = datasets.map((dataset) => {
      const entry = document.createElement("span");
      const marker = document.createElement("i");
      marker.style.backgroundColor = dataset.color || "#2d3d5f";
      entry.append(marker, document.createTextNode(dataset.label));
      return entry;
    });
    legend.replaceChildren(...entries);
  }
}

document.querySelectorAll("[data-report-chart]").forEach(renderReportChart);
