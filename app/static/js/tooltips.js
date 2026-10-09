(() => {
  let trigger = null;
  let timer = null;
  let previousDescription = null;
  let lastInputWasTouch = false;
  const tooltip = document.createElement("div");
  tooltip.id = "site-tooltip";
  tooltip.className = "site-tooltip";
  tooltip.setAttribute("role", "tooltip");
  tooltip.hidden = true;
  document.body.append(tooltip);

  function position() {
    if (!trigger || tooltip.hidden) return;
    const target = trigger.getBoundingClientRect();
    const gap = 12;
    const width = tooltip.offsetWidth;
    const height = tooltip.offsetHeight;
    const above = target.bottom + gap + height > window.innerHeight && target.top - gap - height >= 0;
    const left = Math.max(12, Math.min(target.left + target.width / 2 - width / 2, window.innerWidth - width - 12));
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${above ? target.top - gap - height : target.bottom + gap}px`;
    tooltip.dataset.placement = above ? "top" : "bottom";
  }

  function hide() {
    clearTimeout(timer);
    timer = null;
    if (trigger) {
      if (previousDescription === null) trigger.removeAttribute("aria-describedby");
      else trigger.setAttribute("aria-describedby", previousDescription);
    }
    trigger = null;
    previousDescription = null;
    tooltip.classList.remove("is-visible");
    tooltip.hidden = true;
  }

  function show(element) {
    if (trigger === element && !tooltip.hidden) return;
    hide();
    if (!element?.dataset.tooltip || element.matches(":disabled, [aria-disabled='true']")) return;
    trigger = element;
    previousDescription = element.getAttribute("aria-describedby");
    tooltip.textContent = element.dataset.tooltip;
    element.setAttribute("aria-describedby", [previousDescription, tooltip.id].filter(Boolean).join(" "));
    tooltip.hidden = false;
    position();
    requestAnimationFrame(() => {
      if (trigger === element) tooltip.classList.add("is-visible");
    });
  }

  document.addEventListener("pointerover", (event) => {
    if (event.pointerType === "touch") return;
    const element = event.target.closest?.("[data-tooltip]");
    if (!element || element === trigger) return;
    clearTimeout(timer);
    timer = setTimeout(() => show(element), 320);
  });
  document.addEventListener("pointerout", (event) => {
    const element = event.target.closest?.("[data-tooltip]");
    if (element && !element.contains(event.relatedTarget)) {
      clearTimeout(timer);
      timer = null;
      if (trigger === element && document.activeElement !== element) hide();
    }
  });
  document.addEventListener("focusin", (event) => {
    if (lastInputWasTouch) return;
    const element = event.target.closest?.("[data-tooltip]");
    if (element) show(element);
  });
  document.addEventListener("focusout", (event) => {
    if (event.target === trigger) hide();
  });
  document.addEventListener("pointerdown", (event) => {
    lastInputWasTouch = event.pointerType === "touch";
    if (event.pointerType === "touch" || !event.target.closest?.("[data-tooltip]")) hide();
  });
  document.addEventListener("keydown", (event) => {
    lastInputWasTouch = false;
    if (event.key === "Escape") hide();
  });
  window.addEventListener("scroll", hide, true);
  window.addEventListener("resize", hide);
})();
