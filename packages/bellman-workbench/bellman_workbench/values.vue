<template>
  <div class="bl-values" :class="{ 'bl-stale': disabled }" :data-tab="tab">
    <p v-if="file" class="bl-values-file" :data-path="file"
       title="the last file of this kind the recipe lists"
    >writes <span class="bl-code-small">{{ file }}</span></p>
    <p v-if="sentence" class="bl-values-sentence">{{ sentence }}</p>
    <table v-if="rows.length" class="bl-class-table bl-values-table">
      <thead>
        <tr><th v-for="word in columns" :key="word">{{ word }}</th></tr>
      </thead>
      <tbody class="bl-code-small">
        <tr v-for="row in rows" :key="tab + ' ' + row.name" class="bl-values-row"
            :data-name="row.name">
          <td class="bl-values-name">
            <button v-if="row.line" :data-path="row.file" :data-line="row.line"
                    :aria-description="row.file + ':' + row.line"
                    @click="open_place({ file: row.file, line: row.line })">{{
              row.name
            }}</button>
            <template v-else>{{ row.name }}</template>
          </td>
          <template v-if="tab === 'Methods'">
            <td>
              <select v-if="row.choices.length" class="bl-values-method"
                      :class="{ 'bl-refusal-mark': row.name === refused || row.refused }"
                      :title="row.refused ? row.note : null"
                      :disabled="disabled || !file" @change="chooseTag(row, $event)">
                <option v-if="!row.choices.includes(row.value)" :value="row.value" selected
                        disabled>{{ row.value || "no method" }}</option>
                <option v-for="tag in row.choices" :key="tag" :value="tag"
                        :selected="tag === row.value">{{ tag }}</option>
              </select>
              <span v-else class="bl-values-tag" :class="{ 'bl-refusal-mark': row.refused }"
                    :title="row.refused ? row.note : null">{{ row.value }}</span>
            </td>
            <td class="bl-values-detail">
              <span v-if="row.note && !row.refused" class="bl-values-refusal">{{
                row.note
              }}</span>
              <template v-else>{{ row.detail }}</template>
            </td>
          </template>
          <template v-else>
            <td class="bl-values-detail">{{ row.detail }}</td>
            <td>
              <input class="bl-values-value" :value="valueOf(row)" :disabled="disabled || !file"
                     :class="{ 'bl-refusal-mark': row.name === refused || row.note }"
                     :title="row.note || null"
                     @keydown.enter="commitValue(row, $event)"
                     @keydown.esc="$event.target.value = valueOf(row)" />
            </td>
          </template>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
// The tabs Parameters, Settings and Methods of the BellmanType panel
// (AMD-MI-002 §5 rules 3 to 6): the values and the methods of the shown
// stage at the occurrence it is bound as, read by Python through the tab's
// recipe, one row each, set in Code small, the file's words, with the file
// the tab writes named above them (design pass 8 §5.1). A
// value typed in a row of Parameters or Settings is sent on Enter, and a
// method chosen in a row of Methods at once; Python writes it, or refuses
// it in one sentence, which stands in the list under the error mark while
// the row's input or select carries the refusal's mark (AMD-MI-002 §6a
// rule 1). A row's name is a button that opens the file at the line at
// which its value or its method is written, its accessible description
// that file and line, `declaration/settings/cons.yml:5`, since the tab has
// no line column (spec 0.4 §5.5; unit R, review 13, R-D23); a row that no
// file writes prints its name alone. A value typed is held in its input
// from its Enter until Python answers the write, written or refused, so
// that no table drawn from an earlier reading takes it out; the input of a
// parameter whose value the package refuses is marked, the package's
// sentence its hover (unit L, Task 16; defects 4 and 5 of the UX
// simulation). The choice of a Methods row whose entry the package refuses
// is marked alone, the package's sentence its hover and not printed in the
// row (AMD-MI-002 §6a rule 1; unit L, Task 18; defect 8 of the UX
// simulation).
//
// Properties, each set from Python:
//   tab       the tab shown: Parameters, Settings or Methods
//   rows      one row each, {name, detail, value, choices, note, refused,
//             file, line}: `name` the parameter, the setting or the
//             target; `detail` the set the parameter is declared in, the
//             kind of the setting's value, or the method the stage binds
//             within the target; `value` the value as the file writes it,
//             or as it was typed while its write waits, or the method's
//             tag; `choices` the tags the package admits at the target,
//             none for a parameter or a setting; `note` the refusal of the
//             stage where it binds no method at the target, the package's
//             refusal of the target's entry, or the package's refusal of a
//             parameter's value; `refused` true where the package refuses
//             the target's entry; `file` and `line` where the value or the
//             method is written, null where no file writes it
//   file      the file the tab writes, null where the recipe lists none,
//             the tab then taking no value
//   sentence  the tab's one sentence, null where none applies
//   refused   the name of the row whose write the tab last refused, whose
//             input or select carries the refusal's mark, null for none
//   answered  the ids of the last writes Python answered, written or
//             refused, whose values the inputs no longer hold
//   disabled  true while the stage the tab shows is not the one the loop
//             elaborated from the last text the editor sent: the tab is
//             dimmed and takes no value
// Events, each a call of a Python function:
//   write({tab, name, shown, typed, id})   a value typed in a row, on Enter
//   choose({name, shown, tag})             a method chosen in a row of Methods
//   open_place({file, line})               a row's name, its file and line
module.exports = {
  data() {
    // the values typed and not yet answered, by the tab, the file it writes
    // and the row's name: {id, typed}
    return { held: {} };
  },
  computed: {
    // the headings of the columns of the tab shown, each with a capital as
    // the Fields tab's (design pass 6 §3.1; AAS, L-D24)
    columns() {
      if (this.tab === "Methods") return ["Target", "Method", "Bound"];
      if (this.tab === "Settings") return ["Setting", "Kind", "Value"];
      return ["Parameter", "Set", "Value"];
    },
  },
  watch: {
    // A write answered releases its value, the row then showing the value
    // as the file writes it.
    answered(ids) {
      const done = new Set(ids || []);
      const held = {};
      for (const [key, value] of Object.entries(this.held)) {
        if (!done.has(value.id)) held[key] = value;
      }
      this.held = held;
    },
  },
  methods: {
    // The key under which a row's typed value is held.
    heldKey(row) {
      return [this.tab, this.file, row.name].join(" ");
    },
    // The value a row's input shows: the text typed while its write is not
    // answered, else the row's value.
    valueOf(row) {
      const held = this.held[this.heldKey(row)];
      return held ? held.typed : row.value;
    },
    // A row's text, on Enter, is written in place of the value the input
    // shows, and held there until Python answers; a text equal to that
    // value writes nothing.
    commitValue(row, event) {
      const typed = event.target.value.trim();
      const shown = this.valueOf(row);
      if (typed === shown) return;
      const id = Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
      this.held = { ...this.held, [this.heldKey(row)]: { id, typed } };
      this.write({ tab: this.tab, name: row.name, shown, typed, id });
    },
    chooseTag(row, event) {
      const tag = event.target.value;
      if (tag !== row.value) this.choose({ name: row.name, shown: row.value, tag });
      // the select shows the row's method until the tab reads the file again
      event.target.value = row.value;
    },
  },
};
</script>
