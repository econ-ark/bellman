// The spans the editor hides while the types are hidden (model interface
// specification 0.3, §2.2 rule 5). The rule is the VS Code extension's
// setting `dynspec.collapseHeaders`, the function `hiddenRanges` of
// editor/dynspec-vscode/extension.js, on the same patterns, so that a file
// hides the same spans in both editors. The module imports nothing, so that
// the tests run it under Node beside the extension's own function.
//
// Every bracket group that carries an identity, a block header
// `[id=g_ad, (…) : !arvl -> (…) : !dcsn]`, a label group `[label=work, …]`
// or a statement's annotation `:: [id=cash_on_hand]`, is drawn as its name
// alone, `[g_ad]`, `[work]`, `[cash_on_hand]`. Two spans of its line are
// hidden: the key, from after `[` to the name, and the tail, from after the
// name to the closing `]`. The brackets, the name and the equations are
// drawn as written.
//
// The extension's rule is kept with these consequences:
//   - a group opens and closes on one line;
//   - the group's end is found by one depth count over both bracket kinds,
//     `[` and `(` opening, `]` and `)` closing, since a half-open interval
//     `[-inf, inf)` closes a `[` with `)`; a group whose count returns to
//     zero on `)`, or not at all on its line, is not hidden, and neither is
//     any later group of that line;
//   - the name is `[A-Za-z_][A-Za-z0-9_]*`: a group named with another
//     character, such as `[id=ν]`, is not hidden, and a name that continues
//     with one, such as `foc_ς`, ends before it, the rest hidden with the tail;
//   - a comment is not skipped: a group after `#` is hidden too;
//   - offsets count UTF-16 code units, as VS Code and CodeMirror count them.

// The head of a group carrying an identity, matched at a `[`: the key `id`
// or `label`, `=`, and the name.
export const GROUP_HEAD = /^\[\s*(id|label)\s*=\s*([A-Za-z_][\w]*)/;

// The hidden spans of `lines`, the text of each line without its line
// break, leaving out every line whose index, counted from zero, is in
// `shown`: a list of {line, from, to}, `from` and `to` offsets in the line
// with `to` excluded, in the order of the lines and, within a line, of the
// text.
export function hiddenRanges(lines, shown = new Set()) {
  const ranges = [];
  for (let line = 0; line < lines.length; line++) {
    if (shown.has(line)) continue;
    const text = lines[line];
    let i = 0;
    while ((i = text.indexOf("[", i)) !== -1) {
      const match = GROUP_HEAD.exec(text.slice(i));
      if (!match) {
        i += 1;
        continue;
      }
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
      const nameEnd = i + match[0].length;
      const nameStart = nameEnd - match[2].length;
      ranges.push({ line, from: i + 1, to: nameStart });
      if (close > nameEnd) ranges.push({ line, from: nameEnd, to: close });
      i = close + 1;
    }
  }
  return ranges;
}
