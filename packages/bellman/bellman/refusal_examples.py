"""The examples of the package's refusals: for each rule of
the three vocabularies of `bellman.refusals`, the smallest text that breaks
it, with the way it is provoked, the address or target the refusal names and
the words its message must hold.

A rule of `RULES` is broken by a stage text, most by a change to one of the
corpus stages `CORPUS` names; a rule of `TARGET_RULES` by a name read against
the pieces of `cons.bl`; a rule of `FACTORY_RULES` by the smallest change to
the registry `REGISTRY_FILES`, by a fill, or by one period of corpus stages.
`bellman.refusal_catalogue` provokes each and answers every rule with its
refusal, and the refusal test reads the same table and provokes each. The
examples therefore stand once, in the package, and the package and its test
state one fact one way.

Each example also gives the edit that makes it pass, `write`: the fields of
the example the corrected form replaces. `corrected` applies it, and the
catalogue runs the corrected example through the operation that refused the
example, so that every admitted form the table gives is checked and not
merely printed.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path


__all__ = (
    "BRANCHING",
    "CORPUS",
    "EXAMPLES",
    "Example",
    "corrected",
    "INVERSE_EULER",
    "REGISTRY_FILES",
    "SHOCK_BRANCHING",
    "TWO_NODES",
    "write_registry",
)


# --- the example of a rule ---


@dataclasses.dataclass(frozen=True, kw_only=True)
class Example:
    """The smallest text that breaks one rule, and how it is provoked.

    `text` is the stage text, or `corpus` the stage file of the repository the
    example changes and `changes` the pairs of the line as written and the line
    as changed. `origin` is the file name the refusal names. `provokes` says
    which verb refuses: `elaborate` the stage text itself; `compile_kernel` or
    `kernel` the box `target` of the built stage; `card` the card of the
    target `target` of it; `methodize` the reading of the addition `methods`, a
    mapping holding its text and its origin; `configure-option` the stage
    methodized with the addition `methods` and configured with the settings
    source `settings`; `configure-addition` the stage text with its
    `additions` unioned into it and configured with `settings`;
    `other-version` a box
    of a second version of the same stage; `load_recipe` a registry made of
    `REGISTRY_FILES` with `files` replacing entries, its recipe `recipe` read
    with the fills `fills`, and `assemble_trellis` that registry's recipe read,
    elaborated and bound; `load_trellis` the file `file` of such a registry;
    `load_stage` the path `path`; `elaborate_stage` the value `record` itself;
    `elaborate_trellis` one period of the corpus stages `stages` names, by
    key, with the connectors `connectors`; `union` the stage text with the
    `additions`, each the origin and the text of a methods file, unioned into
    it (specification 0.7 §4), the refusal positioned in the file `origin`
    names; and `same-version` the kernel of a box of the example's own stage.
    `edits` are further (line as written, line as changed) pairs, each applied
    to the one text among the stage text and the additions that holds the
    line once. `address` is the address a refusal of graph construction
    names, the name a refusal of a name that reaches no piece names, or the
    recipe address, slot, record or period a refusal of the factory names,
    and `words` the words its message must hold. `write` is the edit that
    makes the example pass: the fields of the example the corrected form
    replaces, which `corrected` applies; `edits` for a changed line of the
    stage text or of an addition, `changes` emptied for a corpus file restored
    as the repository writes it, and a replaced file, fill, record, path,
    target or settings source otherwise."""

    rule: str
    address: str
    words: tuple
    write: dict = dataclasses.field(default_factory=dict)
    text: str = ""
    corpus: str = ""
    changes: tuple = ()
    edits: tuple = ()
    origin: str = "t.bl"
    provokes: str = "elaborate"
    target: str = ""
    methods: dict = dataclasses.field(default_factory=dict)
    settings: dict = dataclasses.field(default_factory=dict)
    files: dict = dataclasses.field(default_factory=dict)
    fills: dict = dataclasses.field(default_factory=dict)
    recipe: str = "spec.yml"
    file: str = ""
    record: object = None
    path: str = ""
    stages: dict = dataclasses.field(default_factory=dict)
    connectors: list = dataclasses.field(default_factory=list)
    additions: tuple = ()


def corrected(example):
    """The example with its edit applied: the fields its `write` names
    replaced by the values given there, the admitted form of the text the
    example refuses. An example that gives no edit is refused here, so that
    the catalogue names the gap in place of passing over it."""
    if not example.write:
        raise ValueError(f"the example of {example.rule!r} gives no corrected form")
    return dataclasses.replace(example, **example.write)


# --- the corpus and the smallest stages the examples change ---

# The corpus stages, by stage name, as paths in the repository.
CORPUS = {
    "cons": "applications/portfolio-choice/declaration/stages/cons/cons.bl",
    "disc": "applications/portfolio-choice/declaration/stages/disc/disc.bl",
    "port": "applications/portfolio-choice/declaration/stages/port/port.bl",
    "ez_savings": "applications/epstein-zin-savings/declaration/stages/ez_savings/ez_savings.bl",
    "cons_savings_iid": ("applications/consumption-savings-iid/declaration/stages/"
                         "cons_savings_iid/cons_savings_iid.bl"),
    "sa_savings": ("applications/smooth-ambiguity-savings/declaration/stages/"
                   "sa_savings/sa_savings.bl"),
}

# the inverse Euler form of the consumption stage, whose policy block writes the
# candidate, the grid line and the identification (AMD-MB-001 §4.1); the corpus
# writes the maximization alone, so the examples of the grid line read this text
INVERSE_EULER = """@stage: t
𝑢(c : ℝ₊₊) := c^(1-2)/(1-2)
𝑑𝑢(c : ℝ₊₊) := c^(-2)
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/2)
[id=arvl_to_dcsn, (m[<] : ℝ₊) : !arvl -> (m : ℝ₊) : !dcsn] {
    m = m[<]
}
[id=dcsn_to_cntn, (m, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]    :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]
    m[>] = a + c[>]        :: [id=grid]
    c = c[>]               :: [id=identification]
}
"""

# the header of the policy block of the inverse Euler form, and the same header
# with the endogenous grid method and a grid of savings written in it, which
# the examples of the grid rules write with one factor each
_POLICY_HEADER = "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {"


def _egm_with_grid(factor):
    return (
        "[id=policy, method : !egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn\n"
        f"    | grid : !Cartesian({factor})] {{"
    )


# the settings of the grid of savings, declared as a methods file declares
# them (specification 0.7, S1), the addition of the two settings examples
_SAVINGS_SETTINGS = """@methods: t
n_a : ℕ              :: ["number of points of the savings grid"]
a_min : ℝ₊           :: ["lower bound of the savings grid"]
a_max : ℝ₊           :: ["upper bound of the savings grid"]
"""

# The two-node stage, two shocks integrated by two nodes of one backward
# block, which two examples change and the fixtures module of the tests reads
# for the stages it builds.
TWO_NODES = """@stage: two_nodes
β : ℝ₊₊
R : ℝ₊₊
y : ℝ
y ~ N(0,1)
z : ℝ
z ~ N(0,1)
Γ(k : ℝ) := [0,1]

[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (k_d : ℝ) : !dcsn] {
    k_d = k
}
[id=dcsn_to_cntn, (k_d, c : !ctrl @ [0,1], y, z) : !dcsn -> (a : ℝ) : !cntn] {
    a = k_d*(c*y + (1-c)*R) + z
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    W = β*V[>]
    N1 = E_{y,z}(W) :: [id=first, !node]
    N2 = E_{y,z}(W) :: [id=second, !node]
    V = N1 + N2
}
[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V[>]) -> c] {
    c = argmax_{c : Γ(k_d)}(E_{y,z}(V[>])) :: [id=objective]
}
"""

_TWO_NODES_PARTS = {
    "backward": (
        "    W = β*V[>]\n    N1 = E_{y,z}(W) :: [id=first, !node]\n"
        "    N2 = E_{y,z}(W) :: [id=second, !node]\n    V = N1 + N2\n"
    ),
    "transition": "    a = k_d*(c*y + (1-c)*R) + z\n",
    "declarations": "y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n",
    "header": "(V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
}


def _two_nodes(**parts):
    """The two-node stage with its backward lines, its transition line, its
    shock declarations or its backward header replaced."""
    return _changed(
        TWO_NODES,
        *(
            (written, parts[name])
            for name, written in _TWO_NODES_PARTS.items()
            if parts.get(name) is not None
        ),
    )


def _changed(text, *changes):
    """`text` with each (line as written, line as changed) pair applied; a
    line the text does not hold once is refused, so that a change is never
    lost."""
    for written, changed in changes:
        if text.count(written) != 1:
            raise ValueError(f"the example's text does not hold the line {written!r} once")
        text = text.replace(written, changed)
    return text


# The smallest stage of the one form of a branching block, a choice between
# two branches, which the examples of the four branching rules change and the
# fixtures module of the tests reads.
BRANCHING = """@stage: t
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    [label=work, () -> (a_w : ℝ₊) : !cntn] {
        a_w = a_d                          :: [id=working]
    }
    [label=retire, () -> (a_r : ℝ₊) : !cntn] {
        a_r = a_d                          :: [id=retiring]
    }
}
[id=cntn_to_dcsn, (V_w[>] : ℝ @ !vlu, V_r[>] : ℝ @ !vlu, d) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = (V_w[>], V_r[>])[d]                :: [id=choice_value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                               :: [id=value]
}
[id=policy, (V_w[>], V_r[>]) : !cntn -> (d : {work, retire} @ !ctrl) : !dcsn] {
    d = argmax_{d}(V_w[>], V_r[>])         :: [id=choice]
}
"""


# The smallest stage of a branch a shock selects, which the example of the
# rule of a label shock's law changes and the fixtures module of the tests
# reads.
SHOCK_BRANCHING = """@stage: t
π : [0,1]
s : {young, old}
s ~ Categorical((π, 1 - π))
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d, s) : !dcsn -> ()] {
    [label=young, () -> (a_y : ℝ₊) : !cntn] {
        a_y = a_d                          :: [id=staying]
    }
    [label=old, () -> (a_o : ℝ₊) : !cntn] {
        a_o = a_d                          :: [id=ageing]
    }
}
[id=cntn_to_dcsn, (V_y[>] : ℝ @ !vlu, V_o[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = E_{s}((V_y[>], V_o[>])[s])         :: [id=value]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V                               :: [id=value]
}
"""


# --- the smallest registry ---

# The smallest registry: the two-node stage with its addition beside it, one
# source of each valued kind, a period template, a trellis file of three
# periods and a recipe with one slot, which names its trellis file and its
# stage's file by their paths from its folder. Each example of a rule of the
# factory replaces one of its files or gives a fill; the fixtures module of
# the tests adds files to it. The addition types value function iteration on
# the backward decision builder, with the one setting of the settings file as
# the number of candidates its search compares, and names its handler.
TWO_NODES_METHODS = (
    "@methods: two_nodes\n"
    "n_k : ℕ              :: [\"number of candidate levels of the search\"]\n"
    "cntn_to_dcsn.method : !vfi(n_c=n_k)\n"
    "cntn_to_dcsn.handler : \"test:backward\"\n"
)
REGISTRY_FILES = {
    "stages/two_nodes/two_nodes.bl": TWO_NODES,
    "stages/two_nodes/methods.bl": TWO_NODES_METHODS,
    "calibration/main.yml": "calibration:\n  β: 0.96\n  R: 1.02\n",
    "settings/main.yml": "settings:\n  n_k: 10\n",
    "period.yml": "name: one_stage\nstages: [two_nodes]\nconnectors: []\n",
    "trellis.yml": "periods:\n  - {template: period.yml, repeat: 3}\n"
    "inter_connectors:\n  - {a: k}\n",
    "spec.yml": (
        "trellis: trellis.yml\nstages:\n  two_nodes:\n    stage: stages/two_nodes/two_nodes.bl\n"
        "    calibration: {all: [calibration/main, $fill]}\n"
        "    settings: {all: [settings/main, $fill]}\n"
        "    methods: {all: [stages/two_nodes/methods.bl]}\n"
    ),
}


def write_registry(directory, files):
    """`REGISTRY_FILES`, with `files` replacing or adding entries, written
    under `directory`, which is returned."""
    for relative, text in {**REGISTRY_FILES, **files}.items():
        path = Path(directory) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return Path(directory)


# --- the examples of the rules of graph construction ---

# The smallest text that breaks each rule of `RULES`, by rule name; the
# examples of `TARGET_RULES` and `FACTORY_RULES` join the table below.
EXAMPLES = {
    "syntax": Example(
        rule="syntax",
        corpus="cons",
        changes=(
            (
                "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊) : !dcsn",
                "[id=dcsn_to_cntn, (m_d, c : !ctrl @ ℝ₊₊] : !dcsn",
            ),
        ),
        origin="cons.bl",
        address=None,
        words=("`]`", "`)`", "`,`"),
        write={"changes": ()},
    ),
    # a header writing a retired role word (AMD-MB-001 §4.1)
    "marginal-role-retired": Example(
        rule="marginal-role-retired",
        text="@stage: t\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c : !ctrl @ ℝ₊₊) : !cntn "
        "-> (V : ℝ @ !vlu, dV : ℝ₊₊ @ !mrgnvl) : !dcsn] {\n"
        "    V  = V[>]\n    dV = 1\n}\n",
        address=None,
        words=("`!mrgnvl`", "retired", "D_{x}V", "D_{a}V[>]"),
        write={"edits": ((", dV : ℝ₊₊ @ !mrgnvl", ""), ("    dV = 1\n", ""))},
    ),
    "stage-name": Example(
        rule="stage-name",
        text="@stage: one\n@stage: two\n",
        address="2",
        words=("'one'", "'two'", "exactly one"),
        write={"edits": (("@stage: two\n", ""),)},
    ),
    "declared-once": Example(
        rule="declared-once",
        text="@stage: t\n[id=b, (x : ℝ, z : ℝ) : !dcsn -> (y : ℝ, w : ℝ) : !dcsn] {\n"
        "    w = z     :: [id=first]\n    u = x^2   :: [id=square]\n    y = u + z :: [!node]\n}\n",
        address="b.3",
        words=("`y = u + z`", "`!node`", "no id"),
        write={"edits": ((":: [!node]", ":: [id=sum, !node]"),)},
    ),
    "defined-once": Example(
        rule="defined-once",
        text="@stage: t\n[id=b, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    W = V[>]   :: [id=first, !node]\n"
        "    W = 2*V[>] :: [id=second, !node]\n"
        "    V = W\n}\n",
        address="b.second",
        words=(
            "block 'b' already defines W",
            "t.bl:3:5 (term address 'b.first')",
            "this operative equation defines it again",
            "an operative left side is defined once within a block",
        ),
        write={"edits": (("    W = 2*V[>] :: [id=second, !node]\n", ""),)},
    ),
    "one-name-one-meaning": Example(
        rule="one-name-one-meaning",
        text="@stage: t\ny(x : ℝ) := x\n"
        "[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        address="b",
        words=("'y' is a field", "and a function", "another name"),
        write={"edits": (("y(x : ℝ) := x\n", "𝑓(x : ℝ) := x\n"),)},
    ),
    "parameter-or-field": Example(
        rule="parameter-or-field",
        text="@stage: t\nc : ℝ₊ @ !ctrl\n"
        "[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        address="2",
        words=("'c'", "control", "no block header lists 'c'"),
        write={"edits": (("c : ℝ₊ @ !ctrl\n", "c : ℝ₊\n"),)},
    ),
    "field-perch": Example(
        rule="field-perch",
        text="@stage: t\n[id=b, (V[>] : ℝ @ !vlu) : !dcsn -> (W : ℝ) : !dcsn] {\n"
        "    W = V[>]\n}\n",
        address="b",
        words=("V[>]", "cntn", "`: !dcsn`", "without its mark"),
        write={
            "edits": (
                ("(V[>] : ℝ @ !vlu) : !dcsn", "(V : ℝ @ !vlu) : !dcsn"),
                ("W = V[>]", "W = V"),
            )
        },
    ),
    "name-in-scope": Example(
        rule="name-in-scope",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = q\n}\n",
        address="b.1",
        words=("mentions q", "block 'b'"),
        write={"edits": (("y = q", "y = x"),)},
    ),
    "family-selection": Example(
        rule="family-selection",
        text="@stage: t\n[id=b, (a : ℝ, b : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n"
        "    y = (a, b)[q]\n}\n",
        address="b.1",
        words=("(a, b)[q]", "'q'", "2 members", "`(a, b)[1]`"),
        write={"edits": (("(a, b)[q]", "(a, b)[1]"),)},
    ),
    "well-typed": Example(
        rule="well-typed",
        text="@stage: t\n𝑓(x : ℝ₊) := x + 1\n"
        "[id=b, (v : ℝ₊) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = 𝑓 + 1\n}\n",
        address="b.1",
        words=("`𝑓` is a function", "`𝑓 + 1` reads it as a number", "`𝑓(…)`"),
        write={"edits": (("w = 𝑓 + 1", "w = 𝑓(v) + 1"),)},
    ),
    "divisor-nonzero": Example(
        rule="divisor-nonzero",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x/0\n}\n",
        address="b.1",
        words=("`x/0` divides by zero", "defined at no point"),
        write={"edits": (("y = x/0", "y = x/2"),)},
    ),
    "shock-observed": Example(
        rule="shock-observed",
        corpus="cons_savings_iid",
        changes=(("V[<] = E_{y}(V)", "V[<] = V"),),
        address="dcsn_to_arvl.value",
        words=("arvl perch", "mentions V", "shock y", "E_{y}"),
        write={"changes": ()},
    ),
    # the application writes the grid line in the method block of a block file
    # (AMD-MB-001 §4.1); the example writes the policy block of the stage file
    # the explicit way (D7), with a grid line that reads the decision state
    "forward-composite": Example(
        rule="forward-composite",
        corpus="cons_savings_iid",
        changes=(
            (
                "    c = argmax_{cp : Γ(w)}(𝑢(cp) + β*V[>])  :: [id=optimality]\n",
                "    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]\n"
                "    w[>] = w                        :: [id=g_cntn_to_dcsn]\n"
                "    c[~] = c[>]                     :: [id=cons_choice]\n",
            ),
        ),
        address="policy.g_cntn_to_dcsn",
        words=("cntn perch", "mentions w", "dcsn perch"),
        write={"changes": ()},
    ),
    "transition-without-expectation": Example(
        rule="transition-without-expectation",
        text="@stage: flow\nz : ℝ\nz ~ N(0, 1)\n[id=step, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n"
        "    y = x + E_{z}(z)\n}\n",
        address="step.1",
        words=("transition block 'step'", "shock", "push-forward"),
        write={
            "edits": (("(x : ℝ) : !arvl", "(x : ℝ, z) : !arvl"), ("y = x + E_{z}(z)", "y = x + z"))
        },
    ),
    # two implicit statements for the one output c, each a relation in c that
    # reads the continuation value; a candidate line beside them would make a
    # system of statements in unknowns, which the construction refuses under
    # `not-constructed` before this rule, and two equations with c on the left
    # are refused under `defined-once` before it
    "one-implicit-statement": Example(
        rule="one-implicit-statement",
        text="@stage: t\n"
        "[id=dcsn_to_cntn, (w : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
        "    a = w - c\n}\n"
        "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
        "    c + 0 = w - V[>]   :: [id=first]\n"
        "    c + 1 = 2*V[>]     :: [id=second]\n}\n",
        address="policy.second",
        words=("block 'policy'", "second implicit statement", "'c'", "`c + 1 = 2*V[>]`",
               "`c + 0 = w - V[>]`", "policy.first"),
        write={"edits": (("    c + 1 = 2*V[>]     :: [id=second]\n", ""),)},
    ),
    "definition-order": Example(
        rule="definition-order",
        text="@stage: t\n𝑓(x : ℝ) := 𝑔(x)\n𝑔(x : ℝ) := 𝑓(x)\n",
        address="2",
        words=("cycle", "𝑓", "𝑔"),
        write={"edits": (("𝑔(x : ℝ) := 𝑓(x)", "𝑔(x : ℝ) := x"),)},
    ),
    "derivative-one-name": Example(
        rule="derivative-one-name",
        text="@stage: t\nf(x : ℝ, y : ℝ) := x + y\ndf := D_{x,y}(f)\n",
        address="3",
        words=("D_{x, y}(f)", "2 formal arguments", "x, y", "exactly one"),
        write={"edits": (("D_{x,y}(f)", "D_{x}(f)"),)},
    ),
    # the subscript of a derivative of a value names no state of the perch at
    # which the value is read (AMD-MB-001 §4.2)
    "derivative-coordinate": Example(
        rule="derivative-coordinate",
        text="@stage: t\n𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-2)\n"
        "[id=dcsn_to_cntn, (m : ℝ₊, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
        "    a = m - c\n}\n"
        "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
        "    c = 𝑑𝑢𝑖𝑛𝑣(D_{q}V[>]) :: [id=InvEuler]\n}\n",
        address="policy.InvEuler",
        words=("D_{q}V[>]", "'q'", "cntn", "a"),
        write={"edits": (("D_{q}V[>]", "D_{a}V[>]"),)},
    ),
    # a second policy block beside `policy`, both from the continuation perch
    # to the decision perch and both writing the control c: the block file of
    # benhabib-2019 kept under its own id beside the stage's policy block (F17)
    "one-builder-per-output": Example(
        rule="one-builder-per-output",
        text=INVERSE_EULER
        + "[id=egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
        "    c = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])    :: [id=closed]\n}\n",
        address="egm",
        words=("block 'egm' writes c", "dcsn perch", "cntn perch", "block 'policy' already writes"),
        write={"text": INVERSE_EULER},
    ),
    # the grid line of housing-owner's block file written on `w`, the cash on
    # hand of another stage, where the stage's decision state is `w_d` (F39);
    # here the decision state is m and the line names w
    "candidate-coordinate": Example(
        rule="candidate-coordinate",
        text=_changed(
            INVERSE_EULER,
            ("    m[>] = a + c[>]        :: [id=grid]", "    w[>] = a + c[>]        :: [id=grid]"),
        ),
        address="policy.grid",
        words=("writes w[>]", "'w'", "no control", "The controls are c", "states of the dcsn perch are m"),
        write={"edits": (("    w[>] = a + c[>]", "    m[>] = a + c[>]"),)},
    ),
    # the candidate c[>] of the inverse Euler line with the grid line and the
    # identification removed, so that no line reads it (F61)
    "candidate-read": Example(
        rule="candidate-read",
        text=_changed(
            INVERSE_EULER,
            (
                "    m[>] = a + c[>]        :: [id=grid]\n    c = c[>]               :: [id=identification]\n",
                "    c = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>])     :: [id=closed]\n",
            ),
        ),
        address="policy.InvEuler",
        words=("the candidate c[>]", "no later line of block 'policy' reads"),
        write={"edits": (("    c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]\n", ""),)},
    ),
    "derivative-scalar-coordinate": Example(
        rule="derivative-scalar-coordinate",
        text="@stage: t\nf(x : ℝ × ℝ) := x[1]\ndf := D_{x}(f)\n",
        address="3",
        words=("D_{x}(f)", "formal argument 'x'", "function 'f'", "product-valued", "scalar"),
        write={"edits": (("f(x : ℝ × ℝ) := x[1]", "f(x : ℝ, y : ℝ) := x"),)},
    ),
    "stage-boundary": Example(
        rule="stage-boundary",
        corpus="cons_savings_iid",
        changes=(
            (
                (
                    "[id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊) : !dcsn "
                    "-> (a : ℝ₊) : !cntn] {"
                ),
                (
                    "[id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊, z : ℝ) : !dcsn "
                    "-> (a : ℝ₊) : !cntn] {"
                ),
            ),
        ),
        address="dcsn_to_cntn",
        words=("'z'", "dcsn perch", "does not receive"),
        write={"changes": ()},
    ),
    "output-defined": Example(
        rule="output-defined",
        corpus="cons",
        changes=(("    a = m_d - c\n", "    a = m_d - c :: !doc\n"),),
        address="dcsn_to_cntn",
        words=(
            "block 'dcsn_to_cntn'", "lists a on its output side", "no line of the block defines a"
        ),
        write={"changes": ()},
    ),
    # the grid line of `cons.bl` with the candidate doubled: the law of motion
    # `a = m_d - c` solved for m_d at the candidate gives `m_d[>] = a + c[>]`,
    # and the message names the line as written and the law of motion so
    # solved (RL5)
    "grid-line-consistency": Example(
        rule="grid-line-consistency",
        text=_changed(INVERSE_EULER, ("    m[>] = a + c[>]        :: [id=grid]", "    m[>] = a + 2*c[>]      :: [id=grid]")),
        address="policy.grid",
        words=(
            "the grid line m[>] = a + 2*c[>]",
            "its line a = m - c solved for m at the candidate c[>]",
            "the law of motion gives m[>] = a + c[>]",
            "a + 2*c[>] does not reduce to a + c[>]",
        ),
        write={"text": INVERSE_EULER},
    ),
    "identity-collision": Example(
        rule="identity-collision",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (result : ℝ) : !dcsn] {\n    result = x\n}\n",
        address="b",
        words=("the field 'result'", "reserved words", "last segment of an identity"),
        write={"edits": (("(result : ℝ)", "(total : ℝ)"), ("    result = x", "    total = x"))},
    ),
    "readable-form": Example(
        rule="readable-form",
        text="@stage: t\nρ : ℝ := 2\n",
        address="2",
        words=("ρ", "carries the value 2", "`ρ : ℝ`", "calibration file"),
        write={"edits": (("ρ : ℝ := 2", "ρ : ℝ"),)},
    ),
    # two entries type one component of one object: the entry for the whole
    # of an Evaluation beside the entry for the one object it stores, two
    # keys of the union and one place of the semantics (specification 0.7 §4
    # rule 4; D4); the second is refused where it is written
    "component-typed-twice": Example(
        rule="component-typed-twice",
        text="@stage: t\nβ : (0,1)\n"
        "[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {\n    x_d = x\n}\n"
        "[id=dcsn_to_cntn, (x_d) : !dcsn -> (a : ℝ) : !cntn] {\n    a = x_d\n}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn\n"
        "    | evaluate.method : !Linear | evaluate[V].method : !pchip] {\n    V = β*V[>]\n}\n"
        "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n",
        address="cntn_to_dcsn.evaluate[V].method",
        words=("method component is typed twice", "`cntn_to_dcsn.evaluate.method : !Linear`",
               "`cntn_to_dcsn.evaluate[V].method : !pchip`", "the object `V`"),
        write={"edits": ((" | evaluate[V].method : !pchip", ""),)},
    ),
    # the derivative operator admits no typing: nothing is differentiated by
    # a method (specification 0.7 §5; F44)
    "no-method-for-derivative": Example(
        rule="no-method-for-derivative",
        text="@stage: t\nβ : (0,1)\nD.method : !Linear\n"
        "[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {\n    x_d = x\n}\n"
        "[id=dcsn_to_cntn, (x_d) : !dcsn -> (a : ℝ) : !cntn] {\n    a = x_d\n}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = β*V[>]\n    D_{x_d}V = β*D_{a}V[>]\n}\n"
        "[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {\n    V[<] = V\n}\n",
        # the entry's term address in the constructed term, where the union
        # orders a file-level typing entry after the blocks
        address="7",
        words=("`D.method : !Linear`", "derivative operator `D`", "admits no typing"),
        write={"edits": (("D.method : !Linear\n", ""),)},
    ),
    # a representation typed on a builder, a place its row does not admit
    # (specification 0.7 §5, "Admission")
    "method-admission": Example(
        rule="method-admission",
        corpus="cons",
        origin=CORPUS["cons"],
        changes=(("@stage: cons\n", "@stage: cons\ncntn_to_dcsn.method : !Linear\n"),),
        # a file-level entry whose path names a block is addressed under the
        # block in the constructed term
        address="cntn_to_dcsn.method",
        words=("`cntn_to_dcsn.method : !Linear`", "kind builder", "admits"),
        write={
            "changes": (
                ("@stage: cons\n", "@stage: cons\ncntn_to_dcsn.evaluate.method : !Linear\n"),
            )
        },
    ),
    # the grid of `!egm`, which lies on the continuation state `a`, written
    # with a factor for the decision state `m` (the grid note §3); the stage
    # is read with the addition that declares the grid's settings, so that the
    # corrected factor names declared settings
    "grid-coordinate": Example(
        rule="grid-coordinate",
        text=_changed(INVERSE_EULER, (_POLICY_HEADER, _egm_with_grid("m=(a_min, a_max, n_a)"))),
        additions=(("methods.bl", _SAVINGS_SETTINGS),),
        provokes="union",
        address="policy",
        words=("m=(a_min, a_max, n_a)", "'m'", "no coordinate", "a factor names one of them"),
        write={"edits": (("m=(a_min, a_max, n_a)", "a=(a_min, a_max, n_a)"),)},
    ),
    # a bound of a grid written as a number in place of a declared setting
    "grid-setting-declared": Example(
        rule="grid-setting-declared",
        text=_changed(INVERSE_EULER, (_POLICY_HEADER, _egm_with_grid("a=(0, a_max, n_a)"))),
        additions=(("methods.bl", _SAVINGS_SETTINGS),),
        provokes="union",
        address="policy",
        words=("a=(0, a_max, n_a)", "number 0", "settings declared in the methods file"),
        write={"edits": (("a=(0, a_max, n_a)", "a=(a_min, a_max, n_a)"),)},
    ),
    # the bounds of a grid configured out of order
    "grid-bounds": Example(
        rule="grid-bounds",
        corpus="cons",
        provokes="configure-addition",
        additions=(
            (
                "methods.bl",
                "@methods: cons\n"
                "n_m : ℕ\nm_min : ℝ₊\nm_max : ℝ₊\n"
                "cntn_to_dcsn.evaluate.method : !Linear\n"
                "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n",
            ),
        ),
        settings={"settings": {"n_m": 8, "m_min": 10.0, "m_max": 1.0}},
        address="cntn_to_dcsn.evaluate",
        words=("m_d=(m_min, m_max, n_m)", "10.0", "in order", "write a lower bound"),
        write={"settings": {"settings": {"n_m": 8, "m_min": 1.0, "m_max": 10.0}}},
    ),
    # a setting the methods file declares and the settings source does not
    # value, refused at the declaration's position in the methods file
    "setting-unvalued": Example(
        rule="setting-unvalued",
        text=_changed(INVERSE_EULER, (_POLICY_HEADER, _egm_with_grid("a=(a_min, a_max, n_a)"))),
        additions=(("methods.bl", _SAVINGS_SETTINGS),),
        origin="methods.bl",
        provokes="configure-addition",
        settings={"settings": {"a_min": 0.0, "a_max": 20.0}},
        address="methods.bl:2",
        words=("'n_a'", "supplies no value", "`n_a: <value>`"),
        write={"settings": {"settings": {"n_a": 30, "a_min": 0.0, "a_max": 20.0}}},
    ),
    # a setting valued outside the set its declaration names, refused at the
    # declaration's position in the methods file
    "setting-outside-set": Example(
        rule="setting-outside-set",
        text=_changed(INVERSE_EULER, (_POLICY_HEADER, _egm_with_grid("a=(a_min, a_max, n_a)"))),
        additions=(("methods.bl", _SAVINGS_SETTINGS),),
        origin="methods.bl",
        provokes="configure-addition",
        settings={"settings": {"n_a": 30, "a_min": -1.0, "a_max": 20.0}},
        address="methods.bl:3",
        words=("'a_min'", "-1.0", "lies outside", "ℝ₊"),
        write={"settings": {"settings": {"n_a": 30, "a_min": 0.0, "a_max": 20.0}}},
    ),
    # the union of a stage file and its additions (specification 0.7 §4): the
    # consumption stage or the branching stage with one addition, the refusal
    # positioned in the addition
    "declared-twice": Example(
        rule="declared-twice",
        corpus="cons",
        origin="m.bl",
        provokes="union",
        additions=(
            (
                "m.bl",
                "@methods: cons\n"
                "[id=policy, method : !egm | policy.method : !vfi] {\n"
                "    c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])    :: [id=choice]\n}\n",
            ),
        ),
        address="policy.policy.method",
        words=("`method`", "'policy'", "written twice", "`method : !egm`", "`policy.method : !vfi`"),
        # one of the two entries kept; the block of the addition holds the
        # maximization under an id of its own, which stands at the operative
        # level in place of the stage file's line
        write={"edits": (("method : !egm | policy.method : !vfi", "policy.method : !vfi"),)},
    ),
    "label-not-in-parent": Example(
        rule="label-not-in-parent",
        text=BRANCHING,
        origin="m.bl",
        provokes="union",
        additions=(
            (
                "m.bl",
                "@methods: t\n"
                "[id=dcsn_to_cntn] {\n"
                "    [label=rent, () -> (a_x : ℝ₊) : !cntn] {\n"
                "        a_x = a_d    :: [id=renting]\n    }\n}\n",
            ),
        ),
        address="dcsn_to_cntn.rent",
        words=("`label=rent`", "'dcsn_to_cntn'", "no branch", "adds no branch"),
        write={"edits": (("[label=rent,", "[label=work,"),)},
    ),
    "type-conflict": Example(
        rule="type-conflict",
        corpus="cons",
        origin="m.bl",
        provokes="union",
        additions=(
            (
                "m.bl",
                "@methods: cons\n"
                "[id=cntn_to_dcsn, () -> (V : ℝ @ !vlu) : !dcsn] {\n"
                "    V = 𝑢(c) + V[>]    :: [id=note, !doc]\n}\n",
            ),
        ),
        address="cntn_to_dcsn.out.V",
        words=("'V'", "output side", "'cntn_to_dcsn'", "`[-inf, inf) @ !vlu`", "`ℝ @ !vlu`"),
        write={"edits": (("(V : ℝ @ !vlu) : !dcsn", "(V) : !dcsn"),)},
    ),
    "metadata-mismatch": Example(
        rule="metadata-mismatch",
        corpus="cons",
        origin="m.bl",
        provokes="union",
        additions=(
            (
                "m.bl",
                "@methods: port\n"
                "[id=cntn_to_dcsn] {\n    V = 𝑢(c) + V[>]    :: [id=note, !doc]\n}\n",
            ),
        ),
        address="1",
        words=("'port'", "'cons'", "`@methods: <stage>`"),
        write={"edits": (("@methods: port", "@methods: cons"),)},
    ),
    "multiplier-declaration": Example(
        rule="multiplier-declaration",
        text=_changed(
            INVERSE_EULER,
            (
                "    c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]",
                "    μ[>]   : ℝ₊ ⟂ c >= 0             :: [id=slackness]\n"
                "    c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]",
            ),
        ),
        address="policy.slackness",
        words=("'c'", "control", "multiplier"),
        write={"text": INVERSE_EULER},
    ),
    "set-mismatch": Example(
        rule="set-mismatch",
        text="@stage: mismatch\n[id=a, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] { y = x }\n"
        "[id=b, (y : ℝ₊₊) : !dcsn -> (w : ℝ) : !cntn] { w = y }\n",
        address="a",
        words=("field y", "'a' on ℝ", "'b' on ℝ₊₊"),
        write={"edits": (("(y : ℝ₊₊) : !dcsn", "(y : ℝ) : !dcsn"),)},
    ),
    # the code 2 lies outside the set and leaves the member 1 without a
    # category; the refusal stands at the set's file position
    "category-codes": Example(
        rule="category-codes",
        text="@stage: household_status\nβ : (0,1)\n"
        "HouseholdStatus := {i : ℤ | i >= 0, i <= 1} "
        ":: [!categories household_status, newborn=0, old=2]\n"
        "n : HouseholdStatus\nn_next : HouseholdStatus\n"
        "[id=dcsn_to_cntn, (n) : !dcsn -> (n_next) : !cntn] { n_next = 1 }\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] "
        "{ V = 100 - 120*n + β*V[>] }\n",
        address="t.bl:3",
        words=("HouseholdStatus", "`old=2`", "the member 1 has no category"),
        write={"edits": (("old=2", "old=1"),)},
    ),
    # a backward block whose header lists no value input: the statement's
    # kernel has no value or marginal value to act on
    "value-input-role": Example(
        rule="value-input-role",
        text="@stage: t\n"
        "[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {\n    x_d = x\n}\n"
        "[id=cntn_to_dcsn, () : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = 3   :: [id=value]\n}\n",
        address="cntn_to_dcsn.value",
        words=("reads no value input", "header of block 'cntn_to_dcsn'", "lists none"),
        write={
            "edits": (
                ("() : !cntn -> (V", "(V[>] : ℝ @ !vlu) : !cntn -> (V"),
                ("    V = 3   ", "    V = 3 + V[>]   "),
            )
        },
    ),
    "signature-complete": Example(
        rule="signature-complete",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n"
        "[id=d, (y) : !dcsn -> (w : ℝ) : !dcsn] {\n    w = x + y\n}\n",
        address="d.1",
        words=("reads x", "header of block 'd'", "`(y, x) : !dcsn -> (w : ℝ) : !dcsn`"),
        write={"edits": (("[id=d, (y) : !dcsn", "[id=d, (y, x) : !dcsn"),)},
    ),
    # the decision state x_d listed on the value block's header: a coordinate
    # of the value the block writes, and no input
    "header-coordinate": Example(
        rule="header-coordinate",
        text="@stage: t\n[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {\n    x_d = x\n}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, x_d : !dcsn) -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = x_d + V[>]\n}\n",
        address="cntn_to_dcsn",
        words=(
            "lists x_d",
            "coordinate of the output function",
            "`(V[>] : ℝ @ !vlu) -> (V : ℝ @ !vlu) : !dcsn`",
        ),
        write={"edits": (("(V[>] : ℝ @ !vlu, x_d : !dcsn) ->", "(V[>] : ℝ @ !vlu) ->"),)},
    ),
    # the continuation state a read directly on the value line, across the
    # edge that draws no shock: the forward block's equation a = x_d supplies
    # it (AAS's decision BH-4)
    "input-perch-state": Example(
        rule="input-perch-state",
        text="@stage: t\n[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {\n    x_d = x\n}\n"
        "[id=dcsn_to_cntn, (x_d) : !dcsn -> (a : ℝ) : !cntn] {\n    a = x_d\n}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = a + V[>]\n}\n",
        address="cntn_to_dcsn.1",
        words=("mentions a", "state of the cntn perch", "`a = x_d`", "Write `x_d`"),
        write={"edits": (("V = a + V[>]", "V = x_d + V[>]"),)},
    ),
    "shock-reintroduced": Example(
        rule="shock-reintroduced",
        text=_two_nodes(
            backward="    V = E_{y,z}(V[>]) + y :: [id=value]\n",
            header="(V[>] : ℝ @ !vlu, y) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
        ),
        address="cntn_to_dcsn.value",
        words=(
            "the shock y",
            "the expectation over y on line cntn_to_dcsn.value",
            "already integrated",
        ),
        write={"edits": (("V = E_{y,z}(V[>]) + y", "V = E_{y,z}(V[>] + y)"),)},
    ),
    "distribution-dependency": Example(
        rule="distribution-dependency",
        text="@stage: t\ny : ℝ\nz : ℝ\ny ~ N(z, 1)\nz ~ N(y, 1)\n",
        address="4",
        words=("cycle", "`y ~ N(z, 1)` reads z", "`z ~ N(y, 1)` reads y"),
        write={"edits": (("z ~ N(y, 1)", "z ~ N(0, 1)"),)},
    ),
    "distribution-edge": Example(
        rule="distribution-edge",
        text="@stage: t\ny : ℝ\ny ~ N(0, 1)\n"
        "[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (k_d : ℝ) : !dcsn] {\n    k_d = k + y\n}\n"
        "[id=dcsn_to_cntn, (k_d, y) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + y\n}\n",
        address="3",
        words=("the shock y", "'arvl_to_dcsn'", "'dcsn_to_cntn'"),
        write={"edits": (("(k_d, y) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + y",
                          "(k_d) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d"),)},
    ),
    # the refusal is raised at the distribution record, whose address is the
    # file position of its declaration
    "distribution-domain": Example(
        rule="distribution-domain",
        text="@stage: t\ny : ℝ\nz : ℝ\n(y, z) ~ N((0, 0), ((1, 2), (2, 1)))\n",
        address="t.bl:4",
        words=("`(y, z) ~ N((0, 0), ((1, 2), (2, 1)))`", "not positive semidefinite", "-1.0"),
        write={"edits": (("((1, 2), (2, 1))", "((1, 0), (0, 1))"),)},
    ),
    "conditional-not-declared": Example(
        rule="conditional-not-declared",
        text=_two_nodes(
            backward="    V = E_{z}(E_{y}(V[>])) :: [id=value]\n",
            transition="    a = y\n",
            declarations="z : ℝ\nr : [-1,1]\n(y, z) ~ N((0,0),((1,0),(0,0)))\n",
        ),
        address="cntn_to_dcsn.value",
        words=("the expectation over y on line cntn_to_dcsn.value", "y given z", "singular",
               "`(y, z) ~ N((0, 0), ((1, 0), (0, 0)))`"),
        write={"edits": (("((1,0),(0,0))", "((1,0),(0,1))"),)},
    ),
    "not-constructed": Example(
        rule="not-constructed",
        text=_changed(
            BRANCHING,
            (
                "(a_d, d : !ctrl @ {work, retire}) : !dcsn -> ()",
                "(a_d, c : !ctrl @ [0,1], d : !ctrl @ {work, retire}) : !dcsn -> ()",
            ),
        ),
        address="dcsn_to_cntn",
        words=("the controls 'c', 'd'", "beside its branches", "one control"),
        write={"text": BRANCHING},
    ),
    "branch-form": Example(
        rule="branch-form",
        text=_changed(
            BRANCHING,
            (
                "    [label=retire, () -> (a_r : ℝ₊) : !cntn] {\n"
                "        a_r = a_d                          :: [id=retiring]\n    }\n",
                "",
            ),
        ),
        address="dcsn_to_cntn",
        words=("block 'dcsn_to_cntn'", "one nested block", "`work`", "retire"),
        write={"text": BRANCHING},
    ),
    "branch-labels": Example(
        rule="branch-labels",
        text=_changed(BRANCHING, ("[label=retire,", "[label=stop,")),
        address="dcsn_to_cntn.stop",
        words=("'stop'", "{work, retire}"),
        write={"text": BRANCHING},
    ),
    "branch-tuple-mismatch": Example(
        rule="branch-tuple-mismatch",
        text=_changed(BRANCHING, ("argmax_{d}(V_w[>], V_r[>])", "argmax_{d}(V_r[>], V_w[>])")),
        address="cntn_to_dcsn.choice_value",
        words=("policy.choice", "(V_w[>], V_r[>])", "(V_r[>], V_w[>])"),
        write={"text": BRANCHING},
    ),
    "branch-value-position": Example(
        rule="branch-value-position",
        text=_changed(
            BRANCHING,
            ("V = (V_w[>], V_r[>])[d]", "V = (V_w[>], V_w[>])[d]"),
            ("argmax_{d}(V_w[>], V_r[>])", "argmax_{d}(V_w[>], V_w[>])"),
        ),
        address="cntn_to_dcsn.choice_value",
        words=("V_w[>]", "'work'", "'retire'"),
        write={"text": BRANCHING},
    ),
    "branch-law": Example(
        rule="branch-law",
        text=_changed(
            SHOCK_BRANCHING,
            ("s : {young, old}\ns ~ Categorical((π, 1 - π))\n", "s : {young, old} @ !shck\n"),
        ),
        address="dcsn_to_cntn",
        words=("'s'", "has no distribution", "Categorical((p_young, p_old))"),
        write={"text": SHOCK_BRANCHING},
    ),
    # the two rules of a compiled kernel, `kernel-form` here and
    # `kernel-target` below: the smallest call of `compile_kernel` on a
    # corpus stage that breaks each
    # the application writes the derivative line in a marginal block of a
    # block file (AMD-MB-001 §4.3); the example writes it in the decision
    # builder's block of the stage file, the explicit way (D7)
    "kernel-form": Example(
        rule="kernel-form",
        corpus="cons_savings_iid",
        changes=(
            (
                "    V = 𝑢(c) + β*V[>]               :: [id=value]\n",
                "    V = 𝑢(c) + β*V[>]               :: [id=value]\n"
                "    D_{w}V = 𝑑𝑢(c)                  :: [id=marginal]\n",
            ),
        ),
        origin=CORPUS["cons_savings_iid"],
        provokes="compile_kernel",
        target="marginal:Derivative:1",
        address="cntn_to_dcsn.marginal",
        words=(
            "'marginal:Derivative:1'",
            "cons_savings_iid:G:cntn_to_dcsn",
            "𝑑𝑢 := D_{c}(𝑢)",
            "not a closed-form function",
        ),
        write={"target": "cntn_to_dcsn:Aggregation"},
    ),
    # the tolerance of value function iteration configured as a negative number
    "method-option-value": Example(
        rule="method-option-value",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="configure-option",
        address="cntn_to_dcsn",
        methods={
            "text": "@methods: cons\ntol_v : ℝ\ncntn_to_dcsn.method : !vfi(tol=tol_v)\n",
            "origin": "methods.bl",
        },
        settings={"settings": {"tol_v": -1.0}},
        words=("method !vfi", "keyword 'tol'", "positive real", "write"),
        write={"settings": {"settings": {"tol_v": 1e-6}}},
    ),
    "kernel-target": Example(
        rule="kernel-target",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="compile_kernel",
        target="cntn_to_dcsn:Evaluation",
        address="cntn_to_dcsn",
        words=("'cntn_to_dcsn:Evaluation'", "Evaluation box", "kernel(stage, box)"),
        write={"target": "cntn_to_dcsn:Aggregation"},
    ),
}


# --- the examples of a name that reaches no piece, or two ---

# The three failures of a name read against the pieces of a version.
_TARGET_EXAMPLES = {
    "target-not-found": Example(
        rule="target-not-found",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="card",
        target="cntn_to_dcsn:Substitution:V",
        address="cntn_to_dcsn:Substitution:V",
        words=("'cntn_to_dcsn:Substitution:V'", "names no box", "record of its definitions table"),
        write={"target": "cntn_to_dcsn:Pullback"},
    ),
    "target-ambiguous": Example(
        rule="target-ambiguous",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="card",
        target="cntn_to_dcsn",
        address="cntn_to_dcsn",
        words=(
            "names 2 different targets",
            "the initial diagram, backward",
            "the builders graph, backward",
            "builder cntn_to_dcsn",
            "one name selects one target only when the boxes it names are equal",
        ),
        write={"target": "cntn_to_dcsn:Pullback"},
    ),
    "target-version": Example(
        rule="target-version",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="other-version",
        address="cntn_to_dcsn:Pullback",
        words=(
            "'cntn_to_dcsn:Pullback'",
            "no box of a graph of this version",
            "versions share no object",
        ),
        write={"provokes": "same-version"},
    ),
}

for _rule, _example in _TARGET_EXAMPLES.items():
    EXAMPLES[_rule] = dataclasses.replace(_example, rule=_rule)
del _rule, _example

# A dotted id `x.y` attaches its line to the line `x` of the block as a
# property; the inverse Euler form with the ids `argmax.FOC` and `argmax.grid`
# on two of its lines, where no line of its policy block carries the id
# `argmax`, is refused at the first of the two lines, under `readable-form`,
# by the construction's check of the dotted ids.
EXAMPLES["dotted-id-without-an-owning-line"] = Example(
    rule="readable-form",
    text=_changed(
        INVERSE_EULER,
        ("[id=InvEuler]", "[id=argmax.FOC]"),
        ("[id=grid]", "[id=argmax.grid]"),
    ),
    address="policy.argmax.FOC",
    words=("'argmax.FOC'", "'argmax'", "does not write"),
    write={"text": INVERSE_EULER},
)

# A policy block states its policy by the line that writes it; the inverse
# Euler form without its identification line `c = c[>]` writes the candidate
# and the cash on hand at each saving and no line defining the policy, and no
# operation is inferred for the line it omits, so the stage is refused under
# `output-defined`.
EXAMPLES["omitted-identification-line"] = Example(
    rule="output-defined",
    text=_changed(INVERSE_EULER, ("    c = c[>]               :: [id=identification]\n", "")),
    address="policy",
    words=("block 'policy'", "lists c on its output side"),
    write={"text": INVERSE_EULER},
)


# --- the examples of the rules of the Bellman factory ---

# The rules of the Bellman factory, each broken by the
# smallest change to the registry above, by a fill, or by one period of corpus
# stages. A refusal of the factory carries no position; `address` is the
# recipe address, the slot, the record or the period.
_FACTORY_EXAMPLES = {
    "recipe-shape": Example(
        rule="",
        provokes="load_recipe",
        files={"spec.yml": "registry: {}\n"},
        address="stages",
        words=("stages",),
        write={"files": {}},
    ),
    "recipe-source": Example(
        rule="",
        provokes="load_recipe",
        address="stages.two_nodes.calibration.all",
        files={
            "spec.yml": REGISTRY_FILES["spec.yml"].replace(
                "calibration/main", "calibration/absent"
            )
        },
        words=("calibration/absent",),
        write={"files": {}},
    ),
    "recipe-slot-unknown": Example(
        rule="",
        provokes="load_recipe",
        fills={"fil": {"β": 0.9}},
        address="fil",
        words=("'fil'", "$fill"),
        write={"fills": {"fill": {"β": 0.9}}},
    ),
    "recipe-template-agreement": Example(
        rule="",
        provokes="load_recipe",
        address="other",
        files={
            "spec.yml": REGISTRY_FILES["spec.yml"]
            + "  other:\n    stage: stages/other.bl\n    calibration: {all: [calibration/main]}\n",
            "stages/other.bl": TWO_NODES.replace("two_nodes", "other"),
        },
        words=("'other'", "no period"),
        write={"files": {}},
    ),
    "slot-value-not-a-mapping": Example(
        rule="",
        provokes="load_recipe",
        fills={"fill": "β: 0.9"},
        address="fill",
        words=("'fill'", "the text 'β: 0.9'", "no mapping"),
        write={"fills": {"fill": {"β": 0.9}}},
    ),
    "fill-names-nothing": Example(
        rule="",
        provokes="load_recipe",
        fills={"fill": {"beta": 0.9}},
        address="fill",
        words=("'beta'", "two_nodes declares", "β"),
        write={"fills": {"fill": {"β": 0.9}}},
    ),
    "fill-mixes-kinds": Example(
        rule="",
        provokes="load_recipe",
        fills={"fill": {"β": 0.9, "n_k": 4}},
        address="fill",
        words=("β", "n_k"),
        write={"fills": {"fill": {"calibration": {"β": 0.9}, "settings": {"n_k": 4}}}},
    ),
    "trellis-file-shape": Example(
        rule="",
        provokes="load_trellis",
        files={"broken.yml": "stages: []\n"},
        file="broken.yml",
        address="periods",
        words=("periods",),
        # a trellis file read on its own names the stage file of each record
        write={
            "files": {
                "broken.yml": "periods:\n  - stages:\n      two_nodes: "
                "{stage: stages/two_nodes/two_nodes.bl}\n    connectors: []\n"
                "inter_connectors: []\n"
            }
        },
    ),
    "record-shape": Example(
        rule="",
        provokes="elaborate_stage",
        record={"stage": {"text": TWO_NODES, "origin": "t.bl"}},
        address="record",
        words=("holds no", "calibration", "methods", "settings"),
        write={
            "record": {
                "stage": {"text": TWO_NODES, "origin": "t.bl"},
                "calibration": {},
                "settings": {},
                "methods": {},
            }
        },
    ),
    "period-join-cycle": Example(
        rule="",
        provokes="forward_order",
        stages={"disc": "disc", "port": "port"},
        connectors=[{"disc.a": "port.k"}, {"port.m_next": "disc.a"}],
        address="periods[0]",
        words=("disc continues to 'a'", "port arrives at 'k'", "port continues to 'm_next'", "disc arrives at 'a'"),
        write={"connectors": [{"disc.a": "port.k"}]},
    ),
    # a connector written in the keyed form with a key beside from, to and
    # fields; a connector whose endpoint names no field is no refusal since
    # AMD-COMP-001 §3: it stands as a diagnostic of the trellis's selection
    # of its connections, and the trellis is a draft
    "connector-names-no-field": Example(
        rule="",
        provokes="elaborate_trellis",
        stages={"cons": "cons", "port": "port"},
        connectors=[{"from": "cons", "to": "port", "fields": {"a": "k"}, "label": "x"}],
        address="periods[0].connectors[0]",
        words=("'label'", "from, to and fields"),
        write={"connectors": [{"from": "cons", "to": "port", "fields": {"a": "k"}}]},
    ),
    # two stages of one period declaring one parameter name with sets whose
    # intersection is empty (AMD-COMP-001 §2.3): the registry's period holds
    # the two-node stage, whose `R` lies in ℝ₊₊, beside a copy of it named
    # `other` whose `R` lies in (-inf, 0); the stage texts are parsed and the
    # declarations reconciled, and no value is read
    "period-parameter-agreement": Example(
        rule="",
        provokes="assemble_trellis",
        address="periods[0]",
        files={
            "stages/other/other.bl": TWO_NODES.replace("two_nodes", "other").replace(
                "R : ℝ₊₊\n", "R : (-inf, 0)\n"
            ),
            "period.yml": "name: one_stage\nstages: [two_nodes, other]\nconnectors: []\n",
            "spec.yml": REGISTRY_FILES["spec.yml"] + "  other:\n    stage: stages/other/other.bl\n"
            "    calibration: {all: [calibration/main]}\n",
        },
        words=("two_nodes", "other", "'R'", "ℝ₊₊", "(-inf, 0)", "no nonempty intersection"),
        write={
            "files": {
                "stages/other/other.bl": TWO_NODES.replace("two_nodes", "other"),
                "period.yml": "name: one_stage\nstages: [two_nodes, other]\nconnectors: []\n",
                "spec.yml": REGISTRY_FILES["spec.yml"]
                + "  other:\n    stage: stages/other/other.bl\n"
                "    calibration: {all: [calibration/main]}\n",
            }
        },
    ),
    # a path read before any file is opened, so that the refusal names no
    # directory of the machine
    "readable-file": Example(
        rule="",
        provokes="load_stage",
        path="cons.txt",
        address=None,
        words=("cons.txt", "no stage file", "`.bl`"),
        write={"path": CORPUS["cons"]},
    ),
}

for _rule, _example in _FACTORY_EXAMPLES.items():
    EXAMPLES[_rule] = dataclasses.replace(_example, rule=_rule)
del _rule, _example

# A recipe names every file it reads by its path from the recipe's folder
# (AAS, 2 October 2026): the registry's recipe without its `trellis:` line,
# and its one entry without its `stage:` line, are refused under
# `recipe-shape`, though `trellis.yml` and `stages/two_nodes/two_nodes.bl`
# stand in the registry, since nothing is read in place of a path the
# recipe does not write. The page of the refusals prints the two beside the
# rule's example.
EXAMPLES["recipe-names-no-trellis-file"] = Example(
    rule="recipe-shape",
    provokes="load_recipe",
    files={
        "spec.yml": _changed(
            REGISTRY_FILES["spec.yml"], ("trellis: trellis.yml\n", "")
        )
    },
    address="trellis",
    words=("the recipe names no trellis file",),
    write={"files": {}},
)
EXAMPLES["entry-names-no-stage-file"] = Example(
    rule="recipe-shape",
    provokes="load_recipe",
    files={
        "spec.yml": _changed(
            REGISTRY_FILES["spec.yml"], ("    stage: stages/two_nodes/two_nodes.bl\n", "")
        )
    },
    address="stages.two_nodes",
    words=("the entry `stages.two_nodes` names no stage file",),
    write={"files": {}},
)
