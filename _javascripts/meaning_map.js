/**
 * Bellman calculus: Υ meaning-map walkthrough (homepage).
 *
 * This is intentionally lightweight:
 * - no dependencies
 * - degrades gracefully (shows the static <pre><code> if JS fails)
 *
 * Behavior:
 * - Find a YAML code block marked with `.bc-mm-target`
 * - Read walkthrough steps from the immediately-following
 *   `<script class="bc-mm-steps" type="application/json">…</script>` (JSON array)
 * - Animate by typing end-of-line `# ...` comments on the right
 * - No line highlighting and no auto-scroll
 */

function bcInitMeaningMap() {
  const targets = Array.from(document.querySelectorAll(".bc-mm-target"));
  if (targets.length === 0) return;

  function sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  function resolveCodeEl(el) {
    if (!el) return null;
    const tag = el.tagName ? el.tagName.toLowerCase() : "";
    if (tag === "code") return el;
    if (tag === "pre") return el.querySelector("code");
    return el.querySelector("code");
  }

  function resolveHighlightEl(markerEl) {
    if (!markerEl) return null;
    if (markerEl.classList?.contains("highlight")) return markerEl;
    const inside = markerEl.querySelector?.(".highlight");
    if (inside) return inside;
    const next = markerEl.nextElementSibling;
    if (next?.classList?.contains("highlight")) return next;
    const nested = next?.querySelector?.(".highlight");
    if (nested) return nested;
    return null;
  }

  function findStepsScript(afterEl) {
    let cur = afterEl;
    // Bound traversal so we don't scan the whole page on weird markup.
    for (let i = 0; i < 40 && cur; i++) {
      cur = cur.nextElementSibling;
      if (!cur) break;

      if (cur.tagName?.toLowerCase() === "script" && cur.classList?.contains("bc-mm-steps")) return cur;

      const nested = cur.querySelector?.("script.bc-mm-steps");
      if (nested) return nested;
    }
    return null;
  }

  targets.forEach((target) => {
    const codeHighlight = resolveHighlightEl(target) || target.closest?.(".highlight") || null;
    const initRoot = codeHighlight || target;
    if (initRoot.dataset.bcMmInitialized === "true") return;

    const codeEl = resolveCodeEl(codeHighlight) || resolveCodeEl(target) || null;
    if (!codeEl) return;

    const stepsScript = findStepsScript(codeHighlight || target) || null;
    const stepsText = (stepsScript?.textContent || "").trim();

    let steps;
    try {
      steps = JSON.parse(stepsText || "[]");
    } catch (_e) {
      steps = [];
    }
    if (!Array.isArray(steps) || steps.length === 0) return;

    // Remove the steps script from the page (keep one visible code box).
    if (stepsScript && stepsScript.isConnected) {
      const parent = stepsScript.parentElement;
      stepsScript.remove();
      // If the markdown renderer wrapped the script in an empty <p>, remove it too.
      if (parent && parent.tagName?.toLowerCase() === "p" && (parent.textContent || "").trim() === "") {
        parent.remove();
      }
    }

    // Mark initialized now that we know we can run.
    initRoot.dataset.bcMmInitialized = "true";

    // Read the YAML as plain text.
    const raw = (codeEl.textContent || "").replace(/\r\n/g, "\n").trimEnd();
    const lines = raw.split("\n");

    // Render as text + a comment slot per line (with real newlines for copy).
    codeEl.innerHTML = "";
    codeEl.classList.add("bc-mm-live");

    const base = new Map(); // lineNo -> { cmtEl }
    lines.forEach((ln, idx) => {
      const n = idx + 1;

      const lineEl = document.createElement("span");
      lineEl.className = "bc-mm-line";
      lineEl.dataset.line = String(n);

      const txtEl = document.createElement("span");
      txtEl.className = "bc-mm-txt";
      txtEl.textContent = ln === "" ? "" : ln;

      const cmtEl = document.createElement("span");
      cmtEl.className = "bc-mm-cmt";
      cmtEl.textContent = "";

      lineEl.appendChild(txtEl);
      lineEl.appendChild(cmtEl);
      codeEl.appendChild(lineEl);
      codeEl.appendChild(document.createTextNode("\n"));

      base.set(n, { cmtEl });
    });

    const typeMs = Number(target.dataset.type || blockRoot.dataset.type || "24");
    const holdMs = Number(target.dataset.interval || blockRoot.dataset.interval || "3200");
    const autoplayAttr = (target.dataset.autoplay || blockRoot.dataset.autoplay || "true").toLowerCase();
    let playing = autoplayAttr !== "false";

    let stepIdx = 0;
    let token = 0;

    function clearComments() {
      base.forEach(({ cmtEl }) => {
        cmtEl.textContent = "";
        cmtEl.classList.remove("is-typing");
      });
    }

    async function renderStep(i) {
      token += 1;
      const myToken = token;

      const s = steps[i];
      if (!s) return;

      clearComments();

      const lineNo = Number(s.comment_after || (Array.isArray(s.lines) ? s.lines[0] : 1));
      const row = base.get(lineNo);
      if (!row) return;

      let commentRaw = String(s.comment || "").trim();
      if (!commentRaw) return;

      // If the JSON was authored with literal "\\n", normalize to newlines too.
      commentRaw = commentRaw.replace(/\\n/g, "\n");

      const comment = commentRaw.replace(/\s*\n\s*/g, " · ").trim();
      const prefix = "  # ";
      const targetText = prefix + comment;

      row.cmtEl.classList.add("is-typing");
      for (let k = 0; k <= targetText.length; k++) {
        if (myToken !== token) return;
        row.cmtEl.textContent = targetText.slice(0, k);
        await sleep(Math.max(6, typeMs));
      }
      row.cmtEl.classList.remove("is-typing");
    }

    async function playLoop() {
      while (playing && initRoot.isConnected) {
        await renderStep(stepIdx);
        await sleep(Math.max(400, holdMs));
        stepIdx = (stepIdx + 1) % steps.length;
      }
    }

    if (playing) {
      playLoop().catch(() => {});
    } else {
      renderStep(stepIdx).catch(() => {});
    }
  });
}

document.addEventListener("DOMContentLoaded", bcInitMeaningMap);

// If Material's instant navigation is enabled, re-init on page change.
if (typeof window.document$ !== "undefined" && typeof window.document$.subscribe === "function") {
  window.document$.subscribe(bcInitMeaningMap);
}

