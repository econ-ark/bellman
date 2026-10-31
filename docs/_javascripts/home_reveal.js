/**
 * Bellman calculus homepage: "delayed load" section reveal.
 *
 * Progressive enhancement:
 * - If JS fails or features are unavailable, content remains readable.
 * - Respects prefers-reduced-motion.
 *
 * Implementation:
 * - `home.html` adds `bc-home` + `bc-reveal-init` on <html> (with a failsafe).
 * - This script reveals each direct child of `.md-content__inner` as it scrolls into view.
 */

function bcInitHomeReveal() {
  const root = document.documentElement;
  const isHome = Boolean(document.querySelector(".bc-hero"));

  // Clean up if we navigated away (Material instant navigation).
  if (!isHome) {
    root.classList.remove("bc-home");
    root.classList.remove("bc-reveal-init");
    if (window.__bcHomeRevealObserver) {
      try { window.__bcHomeRevealObserver.disconnect(); } catch (_e) {}
      window.__bcHomeRevealObserver = null;
    }
    return;
  }

  root.classList.add("bc-home");

  // Reduced motion: never hide content.
  const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion) {
    root.classList.remove("bc-reveal-init");
    if (window.__bcRevealFailSafe) window.clearTimeout(window.__bcRevealFailSafe);
    return;
  }

  // If IntersectionObserver isn't available, show everything immediately.
  if (typeof window.IntersectionObserver === "undefined") {
    root.classList.remove("bc-reveal-init");
    if (window.__bcRevealFailSafe) window.clearTimeout(window.__bcRevealFailSafe);
    return;
  }

  const inner = document.querySelector(".md-content__inner");
  if (!inner) {
    root.classList.remove("bc-reveal-init");
    if (window.__bcRevealFailSafe) window.clearTimeout(window.__bcRevealFailSafe);
    return;
  }

  // Disconnect any previous observer (instant navigation).
  if (window.__bcHomeRevealObserver) {
    try { window.__bcHomeRevealObserver.disconnect(); } catch (_e) {}
    window.__bcHomeRevealObserver = null;
  }

  const targets = Array.from(inner.children).filter((el) => {
    const tag = (el.tagName || "").toLowerCase();
    if (tag === "script" || tag === "style" || tag === "link" || tag === "noscript") return false;
    return true;
  });

  // If there is nothing to reveal, don't keep the page in "init" mode.
  if (targets.length === 0) {
    root.classList.remove("bc-reveal-init");
    if (window.__bcRevealFailSafe) window.clearTimeout(window.__bcRevealFailSafe);
    return;
  }

  const obs = new IntersectionObserver(
    (entries, observer) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const el = entry.target;
        el.classList.add("bc-reveal--in");
        observer.unobserve(el);
      }
    },
    {
      threshold: 0.14,
      rootMargin: "0px 0px -10% 0px",
    }
  );
  window.__bcHomeRevealObserver = obs;

  // Stagger within each viewport "batch" using a capped delay.
  targets.forEach((el, i) => {
    el.classList.remove("bc-reveal--in");
    el.style.setProperty("--bc-reveal-delay", `${Math.min(i * 40, 240)}ms`);
    obs.observe(el);
  });

  // Reveal anything already above the fold immediately.
  const vh = window.innerHeight || 0;
  targets.forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.top < vh * 0.92) {
      el.classList.add("bc-reveal--in");
      try { obs.unobserve(el); } catch (_e) {}
    }
  });

  // If `home.html` set a failsafe, cancel it now that we're active.
  if (window.__bcRevealFailSafe) window.clearTimeout(window.__bcRevealFailSafe);
}

document.addEventListener("DOMContentLoaded", bcInitHomeReveal);

// If Material's instant navigation is enabled, re-init on page change.
if (typeof window.document$ !== "undefined" && typeof window.document$.subscribe === "function") {
  window.document$.subscribe(bcInitHomeReveal);
}

