// The assembly sequences of the inlined figures (docs/overview) wait until the figure is on screen.
// A figure with a sequence carries the class bf-wait, which pauses it, until four fifths of its height are visible
// (or four fifths of the window, when the window is shorter than the figure). Only the height is compared, since
// in a narrow window the figure scrolls sideways and part of its width is always out of view.
(function () {
  function arm() {
    if (!("IntersectionObserver" in window)) return;
    var steps = []; for (var i = 0; i <= 20; i++) steps.push(i / 20);
    document.querySelectorAll("figure > svg").forEach(function (svg) {
      if (!svg.querySelector(".bf-seq")) return;
      svg.classList.add("bf-wait");
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var need = 0.8 * Math.min(entry.boundingClientRect.height, window.innerHeight);
          if (entry.isIntersecting && entry.intersectionRect.height >= need) { svg.classList.remove("bf-wait"); io.disconnect(); }
        });
      }, { threshold: steps });
      io.observe(svg);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", arm); else arm();
})();
