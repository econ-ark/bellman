// The coloring of stage files (.bl) as a CodeMirror stream language.
//
// The tokenizer is written from the eighteen top-level patterns of the
// repository's TextMate grammar, editor/dynspec-vscode/syntaxes/
// dynspec.tmLanguage.json, and tries them at each position in the grammar's
// order, which is how a TextMate scanner picks among patterns that match at
// one position. It is presentation only: the only parser of the language is
// the package's, and a refusal is set on the editor from Python.
//
// Two patterns of the grammar span several tokens and are held in the
// tokenizer's state: a metadata line (`@stage: cons`) is three tokens, and
// a subscripted operator (`argmax_{cp : Γ(m_d)}`) is a name, `_{`, the
// bound names and `}`. Two tokens are the editor's own, beyond the
// grammar's patterns (AAS, 1 October 2026: the tags seen as tags, the block
// ids seen as the blocks' names): a statement's annotation, from `::` to
// the end of the line, is one muted run in which a marked tag keeps its
// own color, and the brackets of a block header are punctuation.
//
// A marked tag is of three kinds, colored apart by spec 0.4 §5.2 (unit R,
// brief rule 5; R-D18): a perch tag, `!arvl`, `!dcsn` or `!cntn`; a role
// tag, one of the words setRoleWords was given, which the Workbench takes
// from its list of role choices, so that the tokenizer holds no list of
// its own; and any other tag. The TextMate grammar gives every marked tag
// the one scope `entity.name.tag.mark.dynspec`, which unit D's item 3
// meets when it compares the VS Code theme with this one.
import { StreamLanguage, syntaxTree } from "@codemirror/language";
import { Tag, tags as t } from "@lezer/highlight";

// The regular expressions of the grammar, each anchored at the current
// position of the stream. A lookbehind of the grammar is a test on the text
// before the position, since the stream matches on the rest of the line.
const COMMENT = /^#.*$/;
const METADATA_NAME = /^@[A-Za-z_]\w*(?=:)/;
const SUBSCRIPTED_NAME = /^[A-Za-z_]\w*(?=_\{)/;
const SUBSCRIPT_OPEN = /^_\{/;
const BOUND_NAME = /^[A-Za-z_]\w*/;
const OPERATOR_HEAD = /^(E|argmax|max|evaluate|upper_env|solve|Inv|D)\b(?=\s*\()/;
const SPACE_CONSTRUCTOR =
  /^(interval|labels|product|linspace|N|Mixture|LogNormal|Normal|UNormal|Bernoulli|MarkovChain|DiscreteMarkov|Uniform|TruncatedNormal|TruncatedLogNormal|TypeIExtremeValue|Categorical)\b(?=\s*\()/;
const CLASSIFIER = /^@(in|dist|arvl|dcsn|cntn|control|marginal|state|value)\b/;
// a marked tag that names one of the three perches CLASSIFIER also names
const PERCH_TAG = /^!(arvl|dcsn|cntn)$/;
const MARKED_TAG = /^![A-Za-z_]\w*/;
const ID_VALUE = /^[^,\]\s]+/;
const ID_VALUE_BEFORE = /\bid=$/;
const KV_KEY = /^[A-Za-z_]\w*(?==)/;
const SET_GLYPH = /^(ℝ_\{[+\-±]∞\}|ℝ̄|ℝ₊₊|ℝ₊|ℝ|ℕ|ℤ|R\+\+|R\+|∞)/;
const SET_GLYPH_LATIN = /^R\+/;
const SELECTION_BRACKET = /^\[[^[\]\r\n]{1,12}\]/;
const SELECTION_BEFORE = /[\w)\]]$/;
const BUILTIN_CALL = /^(exp|log|sqrt|abs)\b(?=\s*\()/;
const CALL_HEAD = /^[\p{L}][\p{L}\p{Nd}_]*(?=\s*\()/u;
const OPERATOR = /^(->|:=|<-|∈|⟂|×|≤|≥|<=|>=|=)/;
const ANNOTATION_MARK = /^::/;
// a run of an annotation up to the next `!`, which may begin a marked tag
const ANNOTATION_RUN = /^[^!]+/;
const HEADER_BRACKET = /^[\[\]]/;
const PARAMETER_DECLARATION = /^[\p{L}][\p{L}\p{Nd}_]*(?=\s+@in\b)/u;
const DECLARED_NAME = /^[\p{L}\p{N}_]+(?=\s+@)/u;
const STRING = /^("[^"\r\n]*"|'[^'\r\n]*')/;
const NUMBER = /^\d+(\.\d+)?\b/;
// The grammar writes `\b` before a word; on this side of the position it is
// the test that the character before is no word character.
const WORD_END = /\w$/;
const BLANK = /^\s*$/;

// The role words, each a marked tag such as `!ctrl`, which the tokenizer
// gives the token `roleTag`; setRoleWords replaces them.
let roleWords = new Set();

// Replaces the role words by `words`, a list of marked tags. A document
// tokenized afterwards reads them; the editor sets them before it holds a
// document.
export function setRoleWords(words) {
  roleWords = new Set(words ?? []);
}

// The token of the marked tag `text`: a perch tag, a role tag or any other
// tag.
function markedTagToken(text) {
  if (PERCH_TAG.test(text)) return "perchTag";
  if (roleWords.has(text)) return "roleTag";
  return "markedTag";
}

// The tokenizer's state. `metadata` is 0 outside a metadata line, 1 after
// its name and 2 after its colon. `subscript` is 0 outside a subscripted
// operator, 1 after its name and 2 inside the braces.
function startState() {
  return { metadata: 0, subscript: 0, kvEquals: false, annotation: false };
}

function copyState(state) {
  return { ...state };
}

function token(stream, state) {
  if (stream.sol()) state.annotation = false;
  if (state.annotation) {
    if (stream.eatSpace()) return null;
    if (stream.match(MARKED_TAG)) return markedTagToken(stream.current());
    // A `!` that begins no tag, as in a note `"x != y"`, is one character
    // of the run (unit N, Task 4).
    if (!stream.match(ANNOTATION_RUN)) stream.next();
    return "annotation";
  }
  if (state.metadata === 1) {
    state.metadata = stream.eat(":") ? 2 : 0;
    if (state.metadata === 2) return "metadataColon";
  }
  if (state.metadata === 2) {
    state.metadata = 0;
    stream.eatSpace();
    stream.skipToEnd();
    return stream.current().trim() ? "metadataValue" : null;
  }
  if (state.subscript === 1) {
    state.subscript = stream.match(SUBSCRIPT_OPEN) ? 2 : 0;
    if (state.subscript === 2) return "subscriptBrace";
  }
  if (state.subscript === 2) {
    if (stream.eat("}")) {
      state.subscript = 0;
      return "subscriptBrace";
    }
    if (stream.eat("∈")) return "operator";
    if (stream.match(BOUND_NAME)) return "boundName";
    stream.next();
    return null;
  }
  if (state.kvEquals) {
    state.kvEquals = false;
    if (stream.eat("=")) return "operator";
  }
  if (stream.eatSpace()) return null;

  const before = stream.string.slice(0, stream.pos);
  const atWordStart = !WORD_END.test(before);

  if (stream.match(COMMENT)) return "comment";
  if (BLANK.test(before) && stream.match(METADATA_NAME)) {
    state.metadata = 1;
    return "metadataName";
  }
  if (atWordStart && stream.match(SUBSCRIPTED_NAME)) {
    state.subscript = 1;
    return "builtinOperator";
  }
  if (atWordStart && stream.match(OPERATOR_HEAD)) return "builtinOperator";
  if (atWordStart && stream.match(SPACE_CONSTRUCTOR)) return "builtinSet";
  if (stream.match(CLASSIFIER)) return "classifier";
  if (stream.match(MARKED_TAG)) return markedTagToken(stream.current());
  if (ID_VALUE_BEFORE.test(before) && stream.match(ID_VALUE)) return "blockId";
  if (stream.match(KV_KEY)) {
    state.kvEquals = true;
    return "key";
  }
  if (stream.match(SET_GLYPH, false)) {
    // `R+` and `R++` of the grammar carry `\b`; the glyphs do not.
    if (!stream.match(SET_GLYPH_LATIN, false) || atWordStart) {
      stream.match(SET_GLYPH);
      return "builtinSet";
    }
  }
  if (SELECTION_BEFORE.test(before) && stream.match(SELECTION_BRACKET)) return "selector";
  if (atWordStart && stream.match(BUILTIN_CALL)) return "builtinMath";
  if (stream.match(CALL_HEAD)) return "callHead";
  if (stream.match(ANNOTATION_MARK)) {
    state.annotation = true;
    return "annotation";
  }
  if (stream.match(OPERATOR)) return "operator";
  if (stream.match(HEADER_BRACKET)) return "bracket";
  const parameter = BLANK.test(before) && stream.match(PARAMETER_DECLARATION, false);
  // The grammar's `(?!.*@dist)`: no `@dist` after the name on this line.
  if (parameter && !/@dist/.test(stream.string.slice(stream.pos + parameter[0].length))) {
    stream.match(PARAMETER_DECLARATION);
    return "parameter";
  }
  if (stream.match(DECLARED_NAME)) return "declaredName";
  if (stream.match(STRING)) return "string";
  if (atWordStart && stream.match(NUMBER)) return "number";
  stream.next();
  return null;
}

// The highlighting tags of a perch tag and of a role tag, each a kind of
// `tagName`, so that theme.js colors them apart from any other tag.
export const perchTagName = Tag.define("perchTag", t.tagName);
export const roleTagName = Tag.define("roleTag", t.tagName);

// The token names above and the highlighting tag of each. A theme colors
// tags, not token names; theme.js holds the colors. A built-in operator
// such as `argmax` is an operator keyword, which spec 0.4 §5.2 colors as a
// keyword (Design brief 7 §8).
const tokenTable = {
  comment: t.lineComment,
  metadataName: t.keyword,
  metadataColon: t.punctuation,
  metadataValue: t.string,
  builtinOperator: t.operatorKeyword,
  subscriptBrace: t.punctuation,
  boundName: t.local(t.variableName),
  builtinSet: t.typeName,
  classifier: t.annotation,
  perchTag: perchTagName,
  roleTag: roleTagName,
  markedTag: t.tagName,
  blockId: t.labelName,
  key: t.propertyName,
  annotation: t.meta,
  bracket: t.punctuation,
  selector: t.atom,
  builtinMath: t.standard(t.function(t.variableName)),
  callHead: t.function(t.variableName),
  operator: t.operator,
  parameter: t.constant(t.variableName),
  declaredName: t.definition(t.variableName),
  string: t.string,
  number: t.number,
};

export const blLanguage = StreamLanguage.define({
  name: "bl",
  startState,
  copyState,
  token,
  tokenTable,
  languageData: { commentTokens: { line: "#" } },
});

// The stage name of the editor state `state` (unit R, brief rule 5): the
// value of the first line whose `metadataName` token reads `@stage`, read
// from the language's syntax tree and without the white space around it,
// as {line, from, to}, `line` counted from one and `from` and `to` offsets
// in the document; null where the part of the document parsed so far
// holds no such line or the line no value.
export function stageName(state) {
  const cursor = syntaxTree(state).cursor();
  while (cursor.next()) {
    if (cursor.name !== "metadataName" || state.sliceDoc(cursor.from, cursor.to) !== "@stage") {
      continue;
    }
    const line = state.doc.lineAt(cursor.from);
    while (cursor.next() && cursor.from < line.to) {
      if (cursor.name !== "metadataValue") continue;
      const value = state.sliceDoc(cursor.from, cursor.to);
      const from = cursor.from + value.length - value.trimStart().length;
      const to = cursor.to - (value.length - value.trimEnd().length);
      return { line: line.number, from, to };
    }
    return null;
  }
  return null;
}
