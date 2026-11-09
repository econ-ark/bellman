<template>
  <span hidden></span>
</template>

<script>
module.exports = {
  mounted() {
    this.tree = this.$el.closest(".bl-tree");
    this.tree.addEventListener("focusin", this.rememberRow);
    this.tree.addEventListener("click", this.rememberRow);
    this.tree.addEventListener("keydown", this.moveFocus);
    this.changes = new MutationObserver(this.updateTabStop);
    this.changes.observe(this.tree, { childList: true, subtree: true });
    this.updateTabStop();
  },
  unmounted() {
    this.changes.disconnect();
    this.tree.removeEventListener("focusin", this.rememberRow);
    this.tree.removeEventListener("click", this.rememberRow);
    this.tree.removeEventListener("keydown", this.moveFocus);
  },
  methods: {
    rows() {
      return Array.from(this.tree.querySelectorAll('[role="treeitem"]'));
    },
    rowAction(row) {
      return row.parentElement.querySelector(":scope > .bl-tree-remove");
    },
    setTabStop(row, rows) {
      this.path = row?.dataset.path;
      for (const item of rows) item.tabIndex = item === row ? 0 : -1;
    },
    updateTabStop() {
      const rows = this.rows();
      const row = rows.find(item => item.dataset.path === this.path)
        || rows.find(item => item.getAttribute("aria-current") === "page")
        || rows[0];
      this.setTabStop(row, rows);
      for (const item of rows) {
        const action = this.rowAction(item);
        if (action) {
          item.setAttribute("aria-keyshortcuts", "Delete");
          action.tabIndex = -1;
          const button = action.shadowRoot?.querySelector("button");
          if (button) button.tabIndex = -1;
        } else {
          item.removeAttribute("aria-keyshortcuts");
        }
      }
    },
    rememberRow(event) {
      const row = event.target.closest('[role="treeitem"]');
      if (!row) return;
      this.setTabStop(row, this.rows());
      if (event.type === "click") row.focus({ preventScroll: true });
    },
    moveFocus(event) {
      const row = event.target.closest('[role="treeitem"]');
      if (!row || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      const rows = this.rows();
      const index = rows.indexOf(row);
      const next = rows[index + 1];
      const expanded = row.getAttribute("aria-expanded");
      let target;
      switch (event.key) {
        case "ArrowUp":
          target = rows[index - 1];
          break;
        case "ArrowDown":
          target = next;
          break;
        case "Home":
          target = rows[0];
          break;
        case "End":
          target = rows[rows.length - 1];
          break;
        case "ArrowRight":
          if (expanded === "false") row.click();
          else if (expanded === "true" && next?.dataset.path.startsWith(row.dataset.path + "/")) {
            target = next;
          }
          break;
        case "ArrowLeft":
          if (expanded === "true") row.click();
          else {
            const parent = row.dataset.path.split("/").slice(0, -1).join("/");
            target = rows.find(item => item.dataset.path === parent);
          }
          break;
        case "Enter":
        case " ":
          row.click();
          break;
        case "Delete": {
          const action = this.rowAction(row);
          if (!action) return;
          action.click();
          break;
        }
        default:
          return;
      }
      event.preventDefault();
      if (target) target.focus();
    },
  },
};
</script>
