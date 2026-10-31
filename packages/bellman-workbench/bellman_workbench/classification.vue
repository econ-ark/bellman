<template>
  <div class="bl-class-tables" :class="{ 'bl-stale': disabled }">
    <datalist id="bl-class-sets">
      <option v-for="name in completions" :key="name" :value="name"></option>
    </datalist>
    <section v-for="perch in perches" :key="perch" class="bl-class-perch" :data-perch="perch">
      <h4 class="bl-class-perch-name" :title="textsOf(perch).hover"><span
          class="bl-class-sign">{{ textsOf(perch).sign + ' ' }}</span><span
          class="bl-class-perch-word">{{ textsOf(perch).word }}</span></h4>
      <div v-for="group in groupsAt(perch)" :key="group.key" class="bl-class-group"
           :data-group="group.key">
        <h5 v-if="group.heading" class="bl-class-branch bl-code-small">{{ group.heading }}</h5>
        <div class="bl-class-scroll">
          <table class="bl-class-table">
            <thead>
              <tr>
                <th v-for="head in heads" :key="head.word" :title="head.hover">{{ head.word }}</th>
              </tr>
            </thead>
            <tbody class="bl-code-small">
              <tr v-for="row in group.rows" :key="row.identity"
                  :class="['bl-class-row', {
                    'bl-selected': row.identity === selected,
                    'bl-refusal-mark': refusalOf(row) !== null,
                  }]"
                  :data-identity="row.identity" :title="refusalOf(row)">
                <td>
                  <button v-if="row.linked" class="bl-class-field" :data-line="row.line || null"
                          :aria-description="row.line ? 'line ' + row.line : null"
                          :title="hoverOf(row, row.field)" :disabled="disabled"
                          @click="select_field({ identity: row.identity, line: row.line })">{{
                    row.field
                  }}</button>
                  <span v-else class="bl-class-field" :data-line="row.line || null"
                        :title="hoverOf(row, row.field)">{{
                    row.field
                  }}</span>
                </td>
                <td :data-set="row.set">
                  <input class="bl-class-set" list="bl-class-sets" :value="row.set"
                         :title="hoverOf(row, row.set)"
                         :class="{ 'bl-refusal-mark': marks(group, 'set', row) }"
                         :disabled="disabled || !row.editable"
                         @keydown.enter="commitSet(group, row, $event)"
                         @keydown.esc="$event.target.value = row.set"
                         @keydown.tab="expand($event)" />
                </td>
                <td :data-role="row.role">
                  <select class="bl-class-role" :disabled="disabled || !row.editable"
                          :title="hoverOf(row, (role_hovers || {})[row.role])"
                          :class="{ 'bl-refusal-mark': marks(group, 'role', row) }"
                          @change="commitRole(group, row, $event)">
                    <option v-for="word in role_choices" :key="word" :value="word"
                            :selected="word === row.role">{{ word }}</option>
                  </select>
                </td>
              </tr>
            </tbody>
            <tfoot v-if="group.roles.length" class="bl-code-small">
              <tr class="bl-add-field" :class="{ 'bl-refusal-mark': marks(group, 'add', null) }">
                <td>
                  <input data-entry="field" placeholder="New field" :disabled="disabled"
                         @keydown.enter="addField(group, $event)"
                         @keydown.esc="emptyAddRow($event)" @keydown.tab="expand($event)" />
                </td>
                <td>
                  <input data-entry="set" placeholder="Set" list="bl-class-sets"
                         :disabled="disabled" @keydown.enter="addField(group, $event)"
                         @keydown.esc="emptyAddRow($event)" @keydown.tab="expand($event)" />
                </td>
                <td>
                  <select data-entry="role" :disabled="disabled" @keydown.esc="emptyAddRow($event)">
                    <option v-for="word in group.roles" :key="word" :value="word">{{ word }}</option>
                  </select>
                </td>
                <td>
                  <vscode-toolbar-button class="bl-add-button" icon="add" title="Add field"
                                         :label="textsOf(group.perch).add"
                                         :aria-disabled="disabled ? 'true' : null"
                                         @click="disabled || addField(group, $event)"
                  ></vscode-toolbar-button>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p v-if="note && note.group === group.key" class="bl-class-note">{{ note.sentence }}</p>
      </div>
    </section>
  </div>
</template>

<script>
// The three tables of the classification table (model interface
// specification 0.3, unit T): one section per perch, `arvl`, `dcsn`,
// `cntn`, under its title, its sign and its word with a capital, `≺
// Arrival`, `∼ Decision`, `≻ Continuation`, each with its hover (spec 0.4
// §5.5; design pass 6 §§3.1 and 3.7, AAS, L-D24), each holding its groups
// (one, or one per branch and `all branches` in the continuation table of
// a branching stage, each under its heading, `cntn · d = keep`, AMD-MI-002
// §5 rule 2), each group a table headed `Field`, `Set` and `Role`, each
// head with its hover, of its rows whose last row is the box `add field`:
// its entries `New field` and `Set` and its role select in the table's
// three columns, and `+`, the icon button of VSCode Elements that draws
// the Codicon `add` (design pass 8 §3), its hover `Add field` and its
// accessible name `Add field at arrival`, in a fourth cell at the row's
// end (unit L, L-D21; design pass 6 §3.6), which does not act while the
// tables are dimmed; Enter in an entry adds the field as `+` does, and
// Escape empties the box. The rows and the box are set in Code small, the
// file's words (design pass 8 §5.1). A role's hover is the role
// in words, `Marginal value` (§3.7). A
// row's field is a button whose click, or Enter, moves the editor to the
// header that first lists the field and selects the field's box where an
// initial diagram is shown; its accessible description is that line,
// `line 17`, since the table has no line column (spec 0.4 §5.5; unit R,
// review 13, R-D23). The field is text, linking to
// nothing, where the last construction holds no box of it (unit R, R-D57;
// amendment 02 ruling 8). The row of a field a refusal names is marked as
// refused, the refusal's sentence its hover (R-D57; ruling 7). The set
// column is as wide as the group's widest set as the browser draws it,
// which a set cell carries as `data-set` for brand.css to measure, the role
// column as wide as its widest role, which a role cell carries as
// `data-role` (design pass 6 §3.5), and a name or a set wider than its
// column is cut, its hover the whole text (unit L, L-D4 and L-D21).
//
// Properties, each set from Python:
//   groups        the groups of model.classification, each {perch, branch,
//                 key, heading, roles, rows}, the heading null for a table
//                 of one group, a row {identity, field, set, role, line,
//                 editable, linked}, `linked` true where the last
//                 construction holds the field's box
//   perch_texts   the texts of each perch's section, by its perch word:
//                 {sign, word, hover, add}, the sign and the word of its
//                 title, `≺` and `Arrival` for `arvl`, the title's hover
//                 and the accessible name of its `+`, `Add field at
//                 arrival`
//   role_choices  the words a role cell offers
//   role_hovers   the hover of each role word, `Marginal value` for
//                 `!mrgnvl`
//   completions   the sets a set cell offers: the file's, then the
//                 primitive sets
//   shortcuts     the Unicode shortcuts, prefix to body, which Tab expands in
//                 a set cell by the editor bundle's expandShortcut
//   disabled      true while the last text the editor sent does not parse,
//                 the tables being those of the last text that parsed: the
//                 tables are dimmed and no cell, field's button or box acts
//   note          {group, sentence}: the sentence of a change written,
//                 under its group
//   refused       {group, kind, identity}: the change refused, whose cell
//                 (`set` or `role`, the row of `identity`) or box (`add`,
//                 its entries) the group draws in the refusal's color while
//                 the refusal stands; its sentence stands in the list under
//                 the error mark (AMD-MI-002 §6a rule 1)
//   selected      the selected initial-diagram node's identity, or null
//   named         {identity: sentence}: the fields a refusal of the open
//                 file names, each with the refusal's sentence, whose rows
//                 the tables mark while the refusal stands
// Events, each a call of a Python function:
//   select_field({identity, line})                           a field's button
//   change({kind: "set" | "role", group, identity, value})   a cell, on Enter
//                                                            or a choice
//   change({kind: "add", group, perch, branch, field, set, role})
//                                                            the box's button
module.exports = {
  computed: {
    // the perches of the groups, in the order of the groups
    perches() {
      return [...new Set((this.groups || []).map((group) => group.perch))];
    },
    // the heads of a table's columns, each with its hover (design pass 6
    // §§3.1 and 3.7)
    heads() {
      return [
        { word: "Field", hover: "The field's name, as the stage file writes it." },
        { word: "Set", hover: "The set in which the field takes its values." },
        { word: "Role", hover: "Whether the field is a state, a control or a value." },
      ];
    },
  },
  methods: {
    groupsAt(perch) {
      return (this.groups || []).filter((group) => group.perch === perch);
    },
    // The texts of the perch's section, its perch word alone where Python
    // gives none.
    textsOf(perch) {
      return (this.perch_texts || {})[perch] || { sign: "", word: perch, hover: null, add: null };
    },
    // The sentence of the refusal that names the row's field, or null.
    refusalOf(row) {
      return (this.named || {})[row.identity] || null;
    },
    // The hover of a row's name, set or role, `text` (L-D4; design pass 6
    // §3.7); none where a refusal names the row, whose sentence is then
    // the hover (R-D57).
    hoverOf(row, text) {
      return this.refusalOf(row) === null && text ? text : null;
    },
    // Whether the change refused is of `kind` in `group`, at the row `row`
    // for a cell, so that the cell or the box carries the refusal's mark.
    marks(group, kind, row) {
      const refused = this.refused;
      if (!refused || refused.group !== group.key || refused.kind !== kind) return false;
      return row === null || refused.identity === row.identity;
    },
    // A set cell's text, on Enter, is written where a block header declares
    // the field; a text equal to the printed set writes nothing.
    commitSet(group, row, event) {
      const value = event.target.value.trim();
      if (value === row.set) return;
      this.change({ kind: "set", group: group.key, identity: row.identity, value });
    },
    commitRole(group, row, event) {
      this.change({ kind: "role", group: group.key, identity: row.identity, value: event.target.value });
      // the select shows the row's role, until a text holding the chosen
      // word elaborates
      event.target.value = row.role;
    },
    // Escape in the box `add field` empties its entries and returns its
    // role select to its first role (design pass 6 §3.6).
    emptyAddRow(event) {
      const box = event.target.closest(".bl-add-field");
      for (const input of box.querySelectorAll("input")) input.value = "";
      box.querySelector("select").selectedIndex = 0;
    },
    addField(group, event) {
      const box = event.target.closest(".bl-add-field");
      const entry = (name) => box.querySelector(`[data-entry="${name}"]`).value;
      this.change({
        kind: "add",
        group: group.key,
        perch: group.perch,
        branch: group.branch,
        field: entry("field"),
        set: entry("set"),
        role: entry("role"),
      });
    },
    // On Tab, the shortcut that ends the text before the caret is replaced
    // by its body, by the rule the code editor runs; where none ends there,
    // Tab moves on as usual.
    expand(event) {
      const input = event.target;
      const caret = input.selectionStart;
      if (!window.bellmanEditor || caret == null || caret !== input.selectionEnd) return;
      const found = window.bellmanEditor.expandShortcut(input.value.slice(0, caret), this.shortcuts || {});
      if (!found) return;
      event.preventDefault();
      input.setRangeText(found.insert, caret - found.length, caret, "end");
    },
  },
};
</script>
