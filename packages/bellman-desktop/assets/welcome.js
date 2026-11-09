"use strict";

let previousAction;

window.bellmanWelcome = {
  setOpenStatus(message, busy) {
    const status = document.getElementById("open-status");
    const actions = document.querySelectorAll("[data-open-action]");
    if (busy && document.activeElement.matches("[data-open-action]")) {
      previousAction = document.activeElement;
    }
    status.textContent = message;
    for (const action of actions) action.disabled = busy;
    if (!busy && previousAction) {
      if (previousAction.isConnected && document.activeElement === document.body) {
        previousAction.focus({ preventScroll: true });
      }
      previousAction = undefined;
    }
  },
  setNativeState({ recentProjects, shortcutModifier }) {
    const mac = shortcutModifier === "⌘";
    document.querySelector('[data-shortcut="project"]').textContent = mac ? "⌘O" : "Ctrl+O";
    document.querySelector('[data-shortcut="file"]').textContent = mac ? "⇧⌘O" : "Ctrl+Shift+O";
    const list = document.getElementById("recent-projects");
    list.replaceChildren();
    recentProjects.forEach(({ name, path }, index) => {
      const item = document.createElement("li");
      const form = document.createElement("form");
      form.action = `/recent/${index}`;
      form.method = "get";
      const button = document.createElement("button");
      button.type = "submit";
      button.className = "recent-project";
      button.dataset.openAction = "";
      button.title = path;
      const icon = document.querySelector(".open-project svg").cloneNode(true);
      icon.classList.add("folder-icon");
      const details = document.createElement("span");
      details.className = "project-details";
      const title = document.createElement("span");
      title.className = "project-name";
      title.textContent = name;
      const location = document.createElement("span");
      location.className = "project-path";
      location.textContent = path;
      details.append(title, location);
      button.append(icon, details);
      form.append(button);
      item.append(form);
      list.append(item);
    });
    list.hidden = recentProjects.length === 0;
    document.getElementById("recent-empty").hidden = recentProjects.length !== 0;
  },
};
