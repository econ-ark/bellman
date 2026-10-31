// The Unicode shortcuts of the VS Code extension (model interface
// specification 0.3, unit T, rule 6): the snippets of
// editor/dynspec-vscode/snippets/dynspec.json, which Python reads once and
// hands to the code editor and to the set cells of the classification table,
// so that the two editors expand alike. A shortcut is expanded on Tab, as VS
// Code accepts a snippet: the prefix that ends the text before the cursor,
// `\StrictlyPositiveReals`, is replaced by its body, `ℝ₊₊`. The prefix must
// begin a token, the character before it being no letter, digit or
// underscore, as the extension's italic input reads a token, so that the
// underscore of a name, `μ_y`, begins no shortcut. The module imports
// nothing, so that the tests run it under Node.

// A character that continues a name, after which no shortcut begins.
const NAME_CHARACTER = /[\p{L}\p{Nd}_]$/u;

// The shortcut of `table`, prefix to body, that ends `before`, the text of a
// line before the cursor: the longest prefix `before` ends with that begins
// a token. Answers {length, insert}, the code units of the prefix and the
// body that replaces it, or null where no prefix ends there.
export function expandShortcut(before, table) {
  let found = null;
  for (const [prefix, body] of Object.entries(table ?? {})) {
    if (!prefix || !before.endsWith(prefix)) continue;
    if (NAME_CHARACTER.test(before.slice(0, before.length - prefix.length))) continue;
    if (found === null || prefix.length > found.length) found = { length: prefix.length, insert: body };
  }
  return found;
}
