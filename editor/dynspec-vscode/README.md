# dynspec language support

Highlighting, comment handling, set-glyph input, and italic-letter
input for `.bl` stage files, as a local VS Code / Cursor
extension.

## Open in Workbench

Install the Bellman Workbench desktop application, open a saved local file,
and run **Bellman: Open in Workbench** from the command palette. The command
opens a `bellman://` link naming the containing workspace folder, the file
relative to that folder, and the cursor's line. For a file outside the
workspace, it uses the file's own folder. Save changes first: the Workbench
reads the file on disk.

The command is available in VS Code and Cursor. Its identifier is
`dynspec.openWorkbench`, for users who want to assign a keyboard shortcut.

## Italic-letter input

An italic letter is a distinct character (`𝑐` is U+1D450, not a
styled `c`), so `𝑐` and `c` parse as two different names. Typing
`_` then Latin letters where the underscore **begins a token** marks
an italic name; the replacement fires when the word **ends** — on
the next space, parenthesis, operator, or newline — and serves one
letter and whole words uniformly: `_c*` → `𝑐*`, `_duinv(` →
`𝑑𝑢𝑖𝑛𝑣(`, `_x2` → `𝑥2` (digits pass through). The underscore of a
composite name or a binder never triggers, because it follows a
letter: `μ_y`, `foc_ς`, and `E_{y}` are untouched; an interior
underscore (`_du_inv`) blocks the expansion. Italic h is ℎ
(U+210E, the Planck-constant slot). Two companions: the snippets
(type `_c`, accept with Tab) and **Ctrl+Alt+I** ("Italicize word or
selection"), which converts the word at the cursor — or any
selection — and toggles back on a second press. The automatic
replacement switches off with the setting
`dynspec.italicUnderscoreInput`. The
glyphs need a font that covers the mathematical alphanumeric block
(JuliaMono does); and note that any code generation downstream must
not NFKC-normalize names, which would fold 𝑐 back to c.

## Install

**From the repository.** A symbolic link from the editor's folder of
extensions to this folder installs the extension; an edit to it takes
effect on the next window reload, with no packaging:

```bash
ln -s "$(pwd)/editor/dynspec-vscode" ~/.vscode/extensions/dynspec-lang
ln -s "$(pwd)/editor/dynspec-vscode" ~/.cursor/extensions/dynspec-lang
```

Run from the repository root.

**From a packaged file (a reader without the repository).** The
repository keeps no packaged file. Run
`npx @vscode/vsce package --allow-missing-repository` in this folder;
it writes `dynspec-lang-<version>.vsix`, the version being that of
`package.json`. Send that one file; it installs with

```bash
code --install-extension dynspec-lang-<version>.vsix     # VS Code
cursor --install-extension dynspec-lang-<version>.vsix   # Cursor
```

or, in the editor: Extensions panel → the `…` menu at its top →
"Install from VSIX…" → choose the file. Reinstalling a newer file
upgrades in place.

Use one route or the other, not both (a packaged install and the
symbolic link would load the extension twice).

After either install, reload the editor window (Cmd+Shift+P →
"Developer: Reload Window"). The glyphs need a font covering the
mathematical alphanumeric block (JuliaMono does; macOS falls back to
STIX). To inspect what any token received: Cmd+Shift+P →
"Developer: Inspect Editor Tokens and Scopes".

## The colour design

Colour marks category, and the language has five categories worth a
hue; every scope is a standard TextMate name, so the active theme
(Rosé Pine here) supplies the palette.

1. **The `@` register** (typing: `@in`, `@dist`, `@arvl`, `@dcsn`,
   `@cntn`, `@control`, `@marginal`, `@state`, `@value`) takes the
   Python *decorator* colour — the reader's instinct for "this line
   carries meta-typing" transfers directly.
2. **The `!` register** (`!node`, method marks later) takes the
   *tag* colour, so the two registers can never be confused.
3. **Block identity**: the value of `id=` takes the
   *function-definition* colour, so the five block headers read the
   way `def` lines read in Python and give the file its skeleton;
   other keys (`label=`) get the parameter colour.
4. **The mathematical vocabulary** coheres: reserved set glyphs
   (ℝ, ℝ₊, ℝ₊₊, ℕ, ℤ, `R+`, `R++`) take the builtin-type colour;
   `->`, `:=`, `<-`, `∈`, `×`, `≤`, `≥`, `=` the symbol-operator
   colour. The **operators** — `E`, `argmax`, `max`, `evaluate`,
   subscripted or bare — take the builtin-function colour, the hue
   themes give Python's `len` and `print`: an `evaluate(…)` must
   never look like an ordinary call. The **space constructors**
   (`interval`, `labels`, `product`) and **distribution families**
   (`N`) are not operators — they build sets and laws — so their
   calls take the builtin-type colour, joining the glyphs in the
   set world.
5. **Selection brackets** on symbols (`V[>]`, `k[t]`, `Q[d]`,
   `V[>][work]`) take a constant colour — a small mark that reads
   as "component of a family" without shouting.

A sixth mark, added later: a **parameter declaration** — a
line-initial name followed by `@in` with no `@dist` on the line —
takes the constants colour (`constant.other.parameter.dynspec`;
the workspace pins gold, `#D8A657`). Beyond the declaration site, the extension serves **semantic
tokens**: it scans the file's declarations by shape and colours
every *occurrence* of a declared name by role — parameters gold,
shocks teal, spaces in the set colour, functions italic (the
workspace pins the hues). Presentation only; undefined-name
diagnostics wait for the checker. Markdown pages may tag fenced
code blocks as ```bl to receive the stage grammar in the editor
view (the markdown *preview* and Obsidian render them plain).

Everything else — declared names (a soft parameter tint before
their `@`), numbers, strings, comments — follows the theme's
defaults. Sparseness is deliberate: most text stays foreground, and
colour is spent only where a category changes.
