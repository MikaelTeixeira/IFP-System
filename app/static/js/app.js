const shell = document.querySelector("[data-app-shell]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const menuClose = document.querySelector("[data-menu-close]");

function setMenu(open) {
  if (!shell || !menuToggle) return;
  shell.classList.toggle("menu-open", open);
  menuToggle.setAttribute("aria-expanded", String(open));
  document.body.style.overflow = open ? "hidden" : "";
}

menuToggle?.addEventListener("click", () => setMenu(!shell.classList.contains("menu-open")));
menuClose?.addEventListener("click", () => setMenu(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setMenu(false);
});
window.addEventListener("resize", () => {
  if (window.innerWidth >= 1024) setMenu(false);
});

