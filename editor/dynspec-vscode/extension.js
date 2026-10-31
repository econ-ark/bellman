const vscode = require("vscode");
const path = require("node:path");

async function openWorkbench() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.isUntitled || editor.document.uri.scheme !== "file"
      || vscode.env.remoteName) {
    await vscode.window.showErrorMessage("Open a saved local file to use Bellman Workbench.");
    return;
  }

  const file = editor.document.uri.fsPath;
  const workspace = vscode.workspace.getWorkspaceFolder(editor.document.uri);
  const folder = workspace ? workspace.uri.fsPath : path.dirname(file);
  const query = new URLSearchParams({
    folder,
    file: path.relative(folder, file).split(path.sep).join("/"),
    line: String(editor.selection.active.line + 1),
  });
  try {
    // VS Code preserves an encoded string; Uri.parse decodes query delimiters
    // inside file names before the external opener serializes the URI again.
    const opened = await vscode.env.openExternal(`bellman://open?${query}`);
    if (!opened) {
      await vscode.window.showErrorMessage("Could not open Bellman Workbench. Install the desktop application first.");
    }
  } catch (error) {
    await vscode.window.showErrorMessage(`Could not open Bellman Workbench: ${error.message || error}`);
  }
}

// ── Header collapsing ────────────────────────────────────────────────
// Every bracket group carrying an identity — `[id=g_ad, (…) @arvl ->
// (…) @dcsn]`, `[label=work, …]`, `:: [id=cash_on_hand]` — displays as
// just `[g_ad]`, `[work]`, `[cash_on_hand]`: the key and the signature
// / annotation tail are hidden, the equations are untouched. Moving
// the cursor onto a line reveals its full text for editing. The
// command "dynspec: Toggle header collapsing" switches the view off
// and on. Hiding uses a decoration (the inline-fold technique): the
// real text is unchanged.

const HIDE = vscode.window.createTextEditorDecorationType({
  textDecoration: "none; display: none;",
  rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed,
});

function collapseOn() {
  return vscode.workspace
    .getConfiguration("dynspec")
    .get("collapseHeaders", false);
}

function hiddenRanges(document, selections) {
  const ranges = [];
  const cursorLines = new Set();
  for (const sel of selections || []) {
    for (let l = sel.start.line; l <= sel.end.line; l++) cursorLines.add(l);
  }
  for (let line = 0; line < document.lineCount; line++) {
    if (cursorLines.has(line)) continue;
    const text = document.lineAt(line).text;
    let i = 0;
    while ((i = text.indexOf("[", i)) !== -1) {
      const m = /^\[\s*(id|label)\s*=\s*([A-Za-z_][\w]*)/.exec(text.slice(i));
      if (!m) {
        i += 1;
        continue;
      }
      // one combined depth over both bracket kinds: half-open
      // intervals close [ with ) (and ( with ]), so counting square
      // brackets alone never returns to zero on a header that types
      // a value on [-inf, inf).
      let depth = 0;
      let close = -1;
      for (let j = i; j < text.length; j++) {
        if (text[j] === "[" || text[j] === "(") depth += 1;
        else if (text[j] === "]" || text[j] === ")") {
          depth -= 1;
          if (depth === 0) {
            close = j;
            break;
          }
        }
      }
      if (close === -1 || text[close] !== "]") break;
      const nameEnd = i + m[0].length;
      const nameStart = nameEnd - m[2].length;
      ranges.push(new vscode.Range(line, i + 1, line, nameStart));
      if (close > nameEnd)
        ranges.push(new vscode.Range(line, nameEnd, line, close));
      i = close + 1;
    }
  }
  return ranges;
}

function refresh(editor) {
  if (!editor || editor.document.languageId !== "dynspec") return;
  const ranges = collapseOn()
    ? hiddenRanges(editor.document, editor.selections)
    : [];
  editor.setDecorations(HIDE, ranges);
}

let statusItem;

function refreshAll() {
  vscode.window.visibleTextEditors.forEach(refresh);
  updateStatus();
}

// Status-bar switch: visible whenever a stage file is active; shows
// the current view and toggles it on click (same as Ctrl+Alt+H).
function updateStatus() {
  if (!statusItem) return;
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "dynspec") {
    statusItem.hide();
    return;
  }
  statusItem.text = collapseOn()
    ? "$(fold) dynspec: names"
    : "$(unfold) dynspec: full";
  statusItem.tooltip =
    "Click to toggle header collapsing (or Ctrl+Alt+H in the editor)";
  statusItem.show();
}

// ── Line folding of block bodies (gutter chevrons) ───────────────────
function foldingRanges(document) {
  const ranges = [];
  const stack = [];
  for (let line = 0; line < document.lineCount; line++) {
    const code = document.lineAt(line).text.replace(/#.*$/, "");
    for (const ch of code) {
      // brackets do not balance by kind (half-open intervals), so
      // all three opener kinds share one stack.
      if (ch === "{" || ch === "(" || ch === "[") {
        stack.push(line);
      } else if (ch === "}" || ch === ")" || ch === "]") {
        const open = stack.pop();
        if (open !== undefined && line - 1 > open) {
          ranges.push(new vscode.FoldingRange(open, line - 1));
        }
      }
    }
  }
  return ranges;
}

// ── Italic input (_c → 𝑐, _duinv → 𝑑𝑢𝑖𝑛𝑣) ──────────────────────────
// Typing `_` then Latin letters, where the underscore begins a token
// (not preceded by a letter, digit, or underscore), marks an italic
// name. The replacement fires when the word ENDS — on the next
// character that cannot continue a name (space, parenthesis,
// operator, newline) — so it serves one letter and whole words
// uniformly: `_c*` → `𝑐*`, `_duinv(` → `𝑑𝑢𝑖𝑛𝑣(`. Digits pass
// through (`_x2` → 𝑥2); an interior underscore blocks the expansion
// (use Ctrl+Alt+I there). A name-continuation underscore (μ_y,
// foc_ς) or a binder subscript (E_{y}) never triggers. Italic
// letters are distinct characters, so `𝑐` and `c` parse as two
// names. Off switch: dynspec.italicUnderscoreInput. Italic h is
// U+210E (ℎ) — Unicode reserved the math-italic slot for the Planck
// constant.

function italicLetter(ch) {
  if (ch.length !== 1) return null;
  const c = ch.codePointAt(0);
  if (c >= 0x61 && c <= 0x7a)
    return c === 0x68 ? "ℎ" : String.fromCodePoint(0x1d44e + c - 0x61);
  if (c >= 0x41 && c <= 0x5a) return String.fromCodePoint(0x1d434 + c - 0x41);
  return null;
}

function italicInputOn() {
  return vscode.workspace
    .getConfiguration("dynspec")
    .get("italicUnderscoreInput", true);
}

function maybeItalicize(e) {
  if (e.document.languageId !== "dynspec" || !italicInputOn()) return;
  if (e.reason !== undefined) return; // never rewrite an undo or redo
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document !== e.document) return;
  const edits = [];
  for (const change of e.contentChanges) {
    if (change.rangeLength !== 0) continue; // insertions only
    // the typed text must END a word: one character that cannot
    // continue a name, or a newline (with any auto-indent).
    if (!/^\r?\n[ \t]*$/.test(change.text)) {
      if (Array.from(change.text).length !== 1) continue;
      if (/[\p{L}\p{Nd}_]/u.test(change.text)) continue;
    }
    const { line, character: col } = change.range.start;
    const before = e.document.lineAt(line).text.slice(0, col);
    const m = before.match(/_([A-Za-z][A-Za-z0-9]*)$/);
    if (!m) continue;
    const start = col - m[0].length;
    // the `_` must begin a token, not continue a name (μ_y, foc_ς);
    // the $-anchored test reads a surrogate pair whole.
    if (/[\p{L}\p{Nd}_]$/u.test(before.slice(0, start))) continue;
    edits.push({ range: new vscode.Range(line, start, line, col),
                 text: italicizeText(m[1]) });
  }
  if (!edits.length) return;
  editor.edit((b) => edits.forEach((x) => b.replace(x.range, x.text)));
}

// ── Italicize word/selection (toggle) ───────────────────────────────
// dynspec.italicizeWord converts every ASCII Latin letter in the
// selection (or the word at the cursor) to its mathematical-italic
// letter: duinv → 𝑑𝑢𝑖𝑛𝑣. If the text contains no ASCII letter, the
// conversion runs backward (𝑑𝑢𝑖𝑛𝑣 → duinv), so one key toggles. This
// is the whole-word companion of the token-initial `_c` input, which
// by design cannot continue an existing name.

function deitalicLetter(ch) {
  const c = ch.codePointAt(0);
  if (c === 0x210e) return "h";                                  // ℎ
  if (c >= 0x1d44e && c <= 0x1d467)
    return String.fromCodePoint(0x61 + c - 0x1d44e);
  if (c >= 0x1d434 && c <= 0x1d44d)
    return String.fromCodePoint(0x41 + c - 0x1d434);
  return null;
}

function italicizeText(text) {
  const chars = Array.from(text);
  const hasAscii = chars.some((ch) => /[A-Za-z]/.test(ch));
  return chars
    .map((ch) => (hasAscii ? italicLetter(ch) : deitalicLetter(ch)) || ch)
    .join("");
}

function italicizeCommand() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;
  const wordRe = /[\p{L}\p{Nd}_]+/u;
  editor.edit((b) => {
    for (const sel of editor.selections) {
      let range = sel;
      if (sel.isEmpty) {
        range = editor.document.getWordRangeAtPosition(sel.active, wordRe);
        if (!range) continue;
      }
      b.replace(range, italicizeText(editor.document.getText(range)));
    }
  });
}

// ── Semantic tokens: occurrences colored by declared role ───────────
// The scan reads the file's own declarations by shape — a parameter
// (line-initial name + @in, no @dist), a shock (@dist, single or
// joint), a space (name := set expression), a function (name(…) :=,
// or name := call) — and every occurrence of a declared name is then
// colored by its role, the way Pylance colors Python. Presentation
// only: the checker remains the authority on resolution, and
// undefined-name diagnostics wait for it.

const NAME_RE = /[\p{L}][\p{L}\p{Nd}_]*/gu;

function scanRoles(text) {
  const roles = new Map();
  for (let line of text.split(/\r?\n/)) {
    line = line.split("#")[0];
    let m;
    if ((m = line.match(/^\s*\(([^)]*)\)\s*@dist/u))) {
      for (const seg of m[1].split(",")) {
        const n = seg.match(/[\p{L}][\p{L}\p{Nd}_]*/u);
        if (n) roles.set(n[0], "shock");
      }
      continue;
    }
    if ((m = line.match(/^\s*([\p{L}][\p{L}\p{Nd}_]*)\s+@in\b/u))) {
      roles.set(m[1], /@dist/.test(line) ? "shock" : "parameter");
      continue;
    }
    if ((m = line.match(/^\s*([\p{L}][\p{L}\p{Nd}_]*)\s*\([^)]*\)\s*:=/u))) {
      roles.set(m[1], "func");
      continue;
    }
    if ((m = line.match(/^\s*([\p{L}][\p{L}\p{Nd}_]*)\s*:=\s*(.*)$/u))) {
      roles.set(m[1],
        /^[\p{L}][\p{L}\p{Nd}_]*(?:_\{[^}]*\})?\s*\(/u.test(m[2])
          ? "func" : "space");
      continue;
    }
  }
  return roles;
}

const TOKEN_TYPES = ["blParameter", "blShock", "blSpace", "blFunction"];
const ROLE_TO_TYPE = { parameter: 0, shock: 1, space: 2, func: 3 };

function activate(context) {
  statusItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusItem.command = "dynspec.toggleHeaderCollapse";
  context.subscriptions.push(
    statusItem,
    vscode.languages.registerFoldingRangeProvider("dynspec", {
      provideFoldingRanges: (document) => foldingRanges(document),
    }),
    vscode.languages.registerDocumentSemanticTokensProvider(
      { language: "dynspec" },
      {
        provideDocumentSemanticTokens(doc) {
          const legend = new vscode.SemanticTokensLegend(TOKEN_TYPES, []);
          const roles = scanRoles(doc.getText());
          const b = new vscode.SemanticTokensBuilder(legend);
          for (let li = 0; li < doc.lineCount; li++) {
            let text = doc.lineAt(li).text;
            const hash = text.indexOf("#");
            if (hash >= 0) text = text.slice(0, hash);
            if (/^\s*@/.test(text)) continue; // metadata lines
            for (const m of text.matchAll(NAME_RE)) {
              if (m.index > 0 && text[m.index - 1] === "@") continue;
              const role = roles.get(m[0]);
              if (role !== undefined)
                b.push(li, m.index, m[0].length, ROLE_TO_TYPE[role], 0);
            }
          }
          return b.build();
        },
      },
      new vscode.SemanticTokensLegend(TOKEN_TYPES, [])
    ),
    vscode.commands.registerCommand("dynspec.openWorkbench", openWorkbench),
    vscode.commands.registerCommand("dynspec.italicizeWord", italicizeCommand),
    vscode.commands.registerCommand("dynspec.toggleHeaderCollapse", () => {
      vscode.workspace
        .getConfiguration("dynspec")
        .update("collapseHeaders", !collapseOn(),
                vscode.ConfigurationTarget.Global);
    }),
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("dynspec.collapseHeaders")) refreshAll();
    }),
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      refresh(editor);
      updateStatus();
    }),
    vscode.window.onDidChangeTextEditorSelection((e) => refresh(e.textEditor)),
    vscode.workspace.onDidChangeTextDocument((e) => {
      vscode.window.visibleTextEditors
        .filter((ed) => ed.document === e.document)
        .forEach(refresh);
    }),
    vscode.workspace.onDidChangeTextDocument(maybeItalicize)
  );
  refreshAll();
}

function deactivate() {}

module.exports = { activate, deactivate };
