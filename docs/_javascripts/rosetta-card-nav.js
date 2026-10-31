/* Rosetta Stone card pages (individual handler / operator / method / example cards) are
   intentionally not listed in the mkdocs nav, so with navigation.tabs the left sidebar
   has no active tab and collapses to nothing. This restores it: on a card page we find
   the card's parent catalogue or toolkit entry in the nav and activate its trail —
   checking the toggles and marking the items active, exactly the state an in-nav page
   has — so the side navigation stays visible and highlights where you are.

   Pure client-side, scoped to /rosetta-stone/ pages that have no active nav item. */
(function () {
  /* The Rosetta wiki's field/concept pages are dense reference tables (field | meaning |
     values). Tag them so the stylesheet (.r-schema-table) can give them a calmer, denser,
     top-aligned treatment — scoped precisely to /rosetta-stone/ URLs, no per-file class. */
  function tagTables() {
    if (location.pathname.indexOf("/rosetta-stone/") === -1) return;
    document
      .querySelectorAll(".md-content .md-typeset table")
      .forEach(function (t) { t.classList.add("r-schema-table"); });
  }

  function run() {
    tagTables();
    var primary = document.querySelector(".md-sidebar--primary");
    var nav = primary && primary.querySelector(".md-nav--primary");
    if (!nav) return;
    if (nav.querySelector(".md-nav__link--active")) return; // already an in-nav page

    var p = location.pathname;
    var i = p.indexOf("/rosetta-stone/");
    if (i === -1) return;
    var prefix = p.slice(0, i) + "/rosetta-stone/";

    var target = null, m;
    if ((m = p.match(/\/rosetta-stone\/handlers\/([^/]+)\//)))
      target = prefix + "toolkits/" + m[1] + "/";            // handler card -> its toolkit
    else if (p.indexOf("/rosetta-stone/operators/") !== -1)
      target = prefix + "operators/";                         // operator card -> Operators
    else if (p.indexOf("/rosetta-stone/methods/") !== -1)
      target = prefix + "methods/";                           // method card  -> Methods
    else if (p.indexOf("/rosetta-stone/examples/") !== -1)
      target = prefix + "examples/";
    if (!target) return;

    var hit = null;
    nav.querySelectorAll("a.md-nav__link").forEach(function (a) {
      try { if (new URL(a.href).pathname === target) hit = a; } catch (e) {}
    });
    if (!hit) return;

    hit.classList.add("md-nav__link--active");
    var node = hit.closest("li.md-nav__item");
    while (node && nav.contains(node)) {
      node.classList.add("md-nav__item--active");
      var toggle = node.querySelector(":scope > input.md-nav__toggle");
      if (toggle) toggle.checked = true;
      var parent = node.parentElement;
      node = parent ? parent.closest("li.md-nav__item") : null;
    }
  }
  if (window.document$ && typeof window.document$.subscribe === "function")
    window.document$.subscribe(run);                    // Material instant navigation
  else if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", run);
  else run();
})();
