window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true,
    packages: {'[+]': ['extpfeil']}
  },
  options: {
    // MathJax v3 already skips <pre>, <code>, <script>, <style> by default.
    // Only ignore syntax-highlighted code blocks explicitly.
    ignoreHtmlClass: "highlight|highlight-ipynb|codehilite"
  }
};

document$.subscribe(() => {
  MathJax.typesetPromise()
})
