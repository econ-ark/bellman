"""The examples of the package's refusals: for each rule of
the three vocabularies of `bellman.refusals`, the smallest text that breaks
it, with the way it is provoked, the address or target the refusal names and
the words its message must hold.

A rule of `RULES` is broken by a stage text, most by a change to one of the
corpus stages `CORPUS` names; a rule of `TARGET_RULES` by a methods-file
target on `cons.bl`; a rule of `FACTORY_RULES` by the smallest change to the
registry `REGISTRY_FILES`, by a fill, or by one period of corpus stages.
`bellman.refusal_catalogue` provokes each and answers every rule with its
refusal, and the refusal test reads the same table and provokes each. The
examples therefore stand once, in the package, and the package and its test
state one fact one way.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

__all__ = (
    "BRANCHING",
    "CORPUS",
    "EXAMPLES",
    "Example",
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
    target `target` of it; `target` the reading of the methods-file target
    `target`; `methodize` the binding of the methods entry `entry`;
    `configure-option` the stage methodized with the methods source `methods`
    and configured with the settings source `settings`; `other-version` a box
    of a second version of the same stage; `load_recipe` a registry made of
    `REGISTRY_FILES` with `files` replacing entries, its recipe `recipe` read
    with the fills `fills`, and `assemble_trellis` that registry's recipe read,
    elaborated and bound; `load_trellis` the file `file` of such a registry;
    `load_stage` the path `path`; `elaborate_stage` the value `record` itself;
    and `elaborate_trellis` one period of the corpus stages `stages` names, by
    key, with the connectors `connectors`. `address` is the address a refusal
    of graph construction names, the target a refusal of the identity table
    names, or the recipe address, slot, record or period a refusal of the
    factory names, and `words` the words its message must hold. `write` is
    separately registered guidance for the catalogue."""

    rule: str
    address: str
    words: tuple
    write: str = ""
    text: str = ""
    corpus: str = ""
    changes: tuple = ()
    origin: str = "t.bl"
    provokes: str = "elaborate"
    target: str = ""
    entry: dict = dataclasses.field(default_factory=dict)
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

# The smallest registry: the two-node stage, one source of
# each kind, a period template, a trellis file of three periods and a recipe
# with two slots, which names its trellis file and its stage's file by their
# paths from its folder. Each example of a rule of the factory replaces one
# of its files or gives a fill; the fixtures module of the tests adds files
# to it.
REGISTRY_FILES = {
    "stages/two_nodes/two_nodes.bl": TWO_NODES,
    "calibration/main.yml": "calibration:\n  β: 0.96\n  R: 1.02\n",
    "settings/main.yml": "settings:\n  n_k: 10\n",
    "methods/two_nodes.yml": (
        "stage: two_nodes\nmethods:\n  - on: cntn_to_dcsn\n    handler: test:backward\n"
        "    settings:\n      points: n_k\n"
    ),
    "period.yml": "name: one_stage\nstages: [two_nodes]\nconnectors: []\n",
    "trellis.yml": "periods:\n  - {template: period.yml, repeat: 3}\n"
    "inter_connectors:\n  - {a: k}\n",
    "spec.yml": (
        "trellis: trellis.yml\nstages:\n  two_nodes:\n    stage: stages/two_nodes/two_nodes.bl\n"
        "    calibration: {all: [calibration/main, $fill]}\n"
        "    settings: {all: [settings/main, $fill]}\n"
        "    methods: {all: [methods/two_nodes, $method_switch]}\n"
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
        words=("`]`", "`)`", "`,`", "a side of a block header"),
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
        write=(
            "Remove the marginal field from the header; write its line as a derivative "
            "line of the value, `D_{m}V = …`, and read the derivative where a block "
            "needs it as the term `D_{a}V[>]`."
        ),
    ),
    "stage-name": Example(
        rule="stage-name",
        text="@stage: one\n@stage: two\n",
        address="2",
        words=("'one'", "'two'", "exactly one"),
    ),
    "declared-once": Example(
        rule="declared-once",
        text="@stage: t\n[id=b, (x : ℝ, z : ℝ) : !dcsn -> (y : ℝ, w : ℝ) : !dcsn] {\n"
        "    w = z     :: [id=first]\n    u = x^2   :: [id=square]\n    y = u + z :: [!node]\n}\n",
        address="b.3",
        words=("node", "explicit id"),
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
        write=(
            "Remove one definition, give one result another name, or mark "
            "a line that only documents the model `!doc`."
        ),
    ),
    "one-name-one-meaning": Example(
        rule="one-name-one-meaning",
        text="@stage: t\ny(x : ℝ) := x\n"
        "[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        address="b",
        words=("'y' is a field", "and a function"),
    ),
    "parameter-or-field": Example(
        rule="parameter-or-field",
        text="@stage: t\nc : ℝ₊ @ !ctrl\n"
        "[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n",
        address="2",
        words=("'c'", "control", "no block header lists 'c'"),
    ),
    "field-perch": Example(
        rule="field-perch",
        text="@stage: t\n[id=b, (V[>] : ℝ @ !vlu) : !dcsn -> (W : ℝ) : !dcsn] {\n"
        "    W = V[>]\n}\n",
        address="b",
        words=("V[>]", "cntn", "!dcsn"),
    ),
    "name-in-scope": Example(
        rule="name-in-scope",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = q\n}\n",
        address="b.1",
        words=("mentions q", "block 'b'"),
    ),
    "family-selection": Example(
        rule="family-selection",
        text="@stage: t\n[id=b, (a : ℝ, b : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n"
        "    y = (a, b)[q]\n}\n",
        address="b.1",
        words=("(a, b)[q]", "'q'", "2 members"),
    ),
    "well-typed": Example(
        rule="well-typed",
        text="@stage: t\n𝑓(x : ℝ₊) := x + 1\n"
        "[id=b, (v : ℝ₊) : !arvl -> (w : ℝ₊) : !dcsn] {\n    w = 𝑓 + 1\n}\n",
        address="b.1",
        words=("`𝑓` is a function", "`𝑓 + 1` reads it as a number", "`𝑓(…)`"),
    ),
    "divisor-nonzero": Example(
        rule="divisor-nonzero",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x/0\n}\n",
        address="b.1",
        words=("`x/0` divides by zero", "defined at no point"),
    ),
    "shock-observed": Example(
        rule="shock-observed",
        corpus="cons_savings_iid",
        changes=(("V[<] = E_{y}(V)", "V[<] = V"),),
        address="dcsn_to_arvl.value",
        words=("arvl perch", "mentions V", "shock y", "E_{y}"),
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
    ),
    "transition-without-expectation": Example(
        rule="transition-without-expectation",
        text="@stage: flow\nz : ℝ\nz ~ N(0, 1)\n[id=step, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] {\n"
        "    y = x + E_{z}(z)\n}\n",
        address="step.1",
        words=("transition block 'step'", "shock", "push-forward"),
    ),
    "one-implicit-statement": Example(
        rule="one-implicit-statement",
        text="@stage: t\n𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-2)\n"
        "[id=dcsn_to_cntn, (w : ℝ₊, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {\n"
        "    a = w - c\n}\n"
        "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {\n"
        "    c[>] = 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) :: [id=InvEuler]\n"
        "    c + 0 = c[>]   :: [id=first]\n"
        "    c + 1 = 2*c[>] :: [id=second]\n}\n",
        address="policy.second",
        words=("block 'policy'", "second implicit statement", "'c'", "policy.first"),
    ),
    "definition-order": Example(
        rule="definition-order",
        text="@stage: t\n𝑓(x : ℝ) := 𝑔(x)\n𝑔(x : ℝ) := 𝑓(x)\n",
        address="2",
        words=("cycle", "𝑓", "𝑔"),
    ),
    "derivative-one-name": Example(
        rule="derivative-one-name",
        text="@stage: t\nf(x : ℝ, y : ℝ) := x + y\ndf := D_{x,y}(f)\n",
        address="3",
        words=("D_{x, y}(f)", "2 formal arguments", "x, y", "exactly one"),
        write="Write one derivative for one named formal argument, such as `D_{x}(f)`.",
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
        write="Name a state coordinate of the perch at which the value is read, `D_{a}V[>]`.",
    ),
    "derivative-scalar-coordinate": Example(
        rule="derivative-scalar-coordinate",
        text="@stage: t\nf(x : ℝ × ℝ) := x[1]\ndf := D_{x}(f)\n",
        address="3",
        words=("D_{x}(f)", "formal argument 'x'", "function 'f'", "product-valued", "scalar"),
        write=(
            "Declare scalar formal arguments and write one derivative with respect to one of them."
        ),
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
    ),
    "output-defined": Example(
        rule="output-defined",
        corpus="cons",
        changes=(("    a = m_d - c\n", "    a = m_d - c :: !doc\n"),),
        address="dcsn_to_cntn",
        words=("block 'dcsn_to_cntn'", "cons:cntn:a", "no defining equation"),
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
    ),
    "identity-collision": Example(
        rule="identity-collision",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (result : ℝ) : !dcsn] {\n    result = x\n}\n",
        address="b",
        words=("the field 'result'", "reserved words", "last segment of an identity"),
    ),
    "readable-form": Example(
        rule="readable-form",
        text="@stage: t\nρ : ℝ := 2\n",
        address="2",
        words=("ρ", "carries a value", "calibration"),
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
    ),
    "set-mismatch": Example(
        rule="set-mismatch",
        text="@stage: mismatch\n[id=a, (x : ℝ) : !arvl -> (y : ℝ) : !dcsn] { y = x }\n"
        "[id=b, (y : ℝ₊₊) : !dcsn -> (w : ℝ) : !cntn] { w = y }\n",
        address="a",
        words=("field y", "'a' on ℝ", "'b' on ℝ₊₊"),
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
    ),
    "value-input-role": Example(
        rule="value-input-role",
        text="@stage: mixed\n"
        "[id=arvl_to_dcsn, (m : ℝ₊) : !arvl -> (m_d : ℝ₊) : !dcsn] {\n    m_d = m\n}\n"
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, dV[>] : ℝ₊₊ @ !mrgnvl) : !cntn "
        "-> (V : ℝ @ !vlu) : !dcsn] {\n"
        "    V = V[>] + dV[>] :: [id=value]\n}\n",
        address="cntn_to_dcsn.value",
        words=("the value V[>]", "the marginal value dV[>]"),
    ),
    "signature-complete": Example(
        rule="signature-complete",
        text="@stage: t\n[id=b, (x : ℝ) : !dcsn -> (y : ℝ) : !dcsn] {\n    y = x\n}\n"
        "[id=d, (y) : !dcsn -> (w : ℝ) : !dcsn] {\n    w = x + y\n}\n",
        address="d.1",
        words=("reads x", "header of block 'd'", "`(y, x) : !dcsn -> (w : ℝ) : !dcsn`"),
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
        write=(
            "Remove the state from the header; a line of the block may mention a state "
            "of the perch at which its output stands, as a coordinate of what it defines."
        ),
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
        write=(
            "Write the forward block's expression for the state in its place, or read "
            "the state under the expectation over the shock drawn on the edge."
        ),
    ),
    "shock-reintroduced": Example(
        rule="shock-reintroduced",
        text=_two_nodes(
            backward="    V = E_{y,z}(V[>]) + y :: [id=value]\n",
            header="(V[>] : ℝ @ !vlu, y) : !cntn -> (V : ℝ @ !vlu) : !dcsn]",
        ),
        address="cntn_to_dcsn.value",
        words=("the shock y", "cntn_to_dcsn.value:Expectation:1", "already integrated"),
    ),
    "distribution-dependency": Example(
        rule="distribution-dependency",
        text="@stage: t\ny : ℝ\nz : ℝ\ny ~ N(z, 1)\nz ~ N(y, 1)\n",
        address="4",
        words=("cycle", "t:distribution:y (at 4) reads z", "t:distribution:z (at 5) reads y"),
    ),
    "distribution-edge": Example(
        rule="distribution-edge",
        text="@stage: t\ny : ℝ\ny ~ N(0, 1)\n"
        "[id=arvl_to_dcsn, (k : ℝ, y) : !arvl -> (k_d : ℝ) : !dcsn] {\n    k_d = k + y\n}\n"
        "[id=dcsn_to_cntn, (k_d, y) : !dcsn -> (a : ℝ) : !cntn] {\n    a = k_d + y\n}\n",
        address="3",
        words=("the shock y", "'arvl_to_dcsn'", "'dcsn_to_cntn'"),
    ),
    # the refusal is raised at the distribution record, whose address is the
    # file position of its declaration
    "distribution-domain": Example(
        rule="distribution-domain",
        text="@stage: t\ny : ℝ\nz : ℝ\n(y, z) ~ N((0, 0), ((1, 2), (2, 1)))\n",
        address="t.bl:4",
        words=("t:distribution:y_z", "not positive semidefinite", "-1.0"),
    ),
    "conditional-not-declared": Example(
        rule="conditional-not-declared",
        text=_two_nodes(
            backward="    V = E_{z}(E_{y}(V[>])) :: [id=value]\n",
            transition="    a = y\n",
            declarations="z : ℝ\nr : [-1,1]\n(y, z) ~ N((0,0),((1,0),(0,0)))\n",
        ),
        address="cntn_to_dcsn.value",
        words=("cntn_to_dcsn.value:Expectation:2", "y given z", "Σ_CC", "singular"),
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
        words=("block 'dcsn_to_cntn'", "one nested block", "at least two"),
    ),
    "branch-labels": Example(
        rule="branch-labels",
        text=_changed(BRANCHING, ("[label=retire,", "[label=stop,")),
        address="dcsn_to_cntn.stop",
        words=("'stop'", "{work, retire}"),
    ),
    "branch-tuple-mismatch": Example(
        rule="branch-tuple-mismatch",
        text=_changed(BRANCHING, ("argmax_{d}(V_w[>], V_r[>])", "argmax_{d}(V_r[>], V_w[>])")),
        address="cntn_to_dcsn.choice_value",
        words=("policy.choice", "(V_w[>], V_r[>])", "(V_r[>], V_w[>])"),
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
    ),
    "branch-law": Example(
        rule="branch-law",
        text=_changed(
            SHOCK_BRANCHING,
            ("s : {young, old}\ns ~ Categorical((π, 1 - π))\n", "s : {young, old} @ !shck\n"),
        ),
        address="dcsn_to_cntn",
        words=("'s'", "has no distribution", "Categorical((p_young, p_old))"),
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
    ),
    "method-option-value": Example(
        rule="method-option-value",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="configure-option",
        address="cntn_to_dcsn:Evaluation",
        methods={
            "stage": "cons",
            "methods": [
                {
                    "on": "cntn_to_dcsn.value",
                    "method": "Cartesian",
                    "settings": {"orders": {"m_d": "n_m"}, "bounds": {"m_d": ["m_min", "m_max"]}},
                }
            ],
        },
        settings={"settings": {"n_m": -5, "m_min": 0.1, "m_max": 10.0}},
        words=("method !Cartesian", "option 'orders'", "positive integer", "write"),
    ),
    "kernel-target": Example(
        rule="kernel-target",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="compile_kernel",
        target="cntn_to_dcsn:Evaluation",
        address="cntn_to_dcsn",
        words=("'cntn_to_dcsn:Evaluation'", "Evaluation box", "kernel(stage, box)"),
    ),
}


# --- the examples of the rules of the identity table ---

# The rules of the identity table, each provoked by the methods-file target a
# reader writes after `on:` in a methods file for `cons.bl`, and the four
# failures beside them.
_TARGET_EXAMPLES = {
    "(a) a builder box by its block id; `<block-id>_builder` for a transition block": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="nowhere",
        address="nowhere",
        words=("names no builder of the stage", "no operator a statement of it records"),
    ),
    "(b), (c) a node box or a line by `<block-id>.<statement-id>`": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="cntn_to_dcsn.absent",
        address="cntn_to_dcsn.absent",
        words=(
            "names no line of block 'cntn_to_dcsn'",
            "no line carries the id 'absent'",
            "cntn_to_dcsn.value",
        ),
    ),
    "(ii) a positional address `<block-id>.<n>` is not a target; the line needs an id": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="cntn_to_dcsn.1",
        address="cntn_to_dcsn.1",
        words=("is a positional address", "name it by its id", "'cntn_to_dcsn.value'"),
    ),
    "(d) every occurrence of an operator by its stage-wide name": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="E",
        address="E",
        words=(
            "the expectation over the shocks",
            "no statement of the stage records an occurrence",
        ),
    ),
    "(e) one occurrence by `<block-id>.<statement-id>.<operator>`": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="cntn_to_dcsn.value.E",
        address="cntn_to_dcsn.value.E",
        words=("the output statement cntn_to_dcsn.value", "carries no operator occurrence"),
    ),
    "(g) `evaluate`: the one authored occurrence, else the boundary "
    "representation; two or more authored occurrences are named by their addresses": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="evaluate",
        address="evaluate",
        words=("names no authored occurrence", "the implicit statement policy.cons_choice"),
    ),
    "(h) one target per entry; a comma-separated entry is split by L02": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="policy, cntn_to_dcsn",
        address="policy, cntn_to_dcsn",
        words=("lists several targets separated by commas", "an entry names one target"),
    ),
    "a target has one, two, or three dot-separated parts": Example(
        rule="",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="target",
        target="a.b.c.d",
        address="a.b.c.d",
        words=("is not the form of a target", "a block id"),
    ),
    # a name reaches two places only where the file writes a block id that is
    # another block's id under the retired suffix, so this example carries its
    # own stage rather than a target on `cons.bl`
    "a target reaches one place; two is a construction defect": Example(
        rule="",
        provokes="target",
        target="arvl_to_dcsn_builder",
        text="@stage: two_places\n"
        "[id=arvl_to_dcsn, (m : ℝ) : !arvl -> (m_d : ℝ) : !dcsn] {\n    m_d = m\n}\n"
        "[id=arvl_to_dcsn_builder, (m_d : ℝ) : !dcsn -> (a : ℝ) : !cntn] {\n    a = m_d\n}\n",
        address="arvl_to_dcsn_builder",
        words=(
            "reaches 2 places",
            "the builder box 'arvl_to_dcsn_builder'",
            "under the suffix `_builder`",
        ),
    ),
    "target-not-found": Example(
        rule="target-not-found",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="card",
        target="cntn_to_dcsn:Substitution:V",
        address="cntn_to_dcsn:Substitution:V",
        words=("'cntn_to_dcsn:Substitution:V'", "names no box", "rule target-not-found"),
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
            "rule target-ambiguous",
        ),
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
            "rule target-version",
        ),
    ),
    "method-attachment": Example(
        rule="method-attachment",
        corpus="cons",
        origin=CORPUS["cons"],
        provokes="methodize",
        entry={"on": "cntn_to_dcsn.value", "method": "!egm"},
        address="cntn_to_dcsn.value",
        words=(
            "Method target 'cntn_to_dcsn.value' in stage 'cons'",
            "!egm does not admit target kind",
            "method-attachment admits",
        ),
    ),
}

for _rule, _example in _TARGET_EXAMPLES.items():
    EXAMPLES[_rule] = dataclasses.replace(_example, rule=_rule)
del _rule, _example

# A second example of the rule `method-attachment`, the admissibility of a
# method for its target: `!gauss-hermite` is a quadrature rule and the block
# `policy` a builder, which admits a handler, so the entry binds a method the
# target does not admit, and the attachment refuses it.
EXAMPLES["method-admissibility"] = Example(
    rule="method-attachment",
    corpus="cons",
    origin=CORPUS["cons"],
    provokes="methodize",
    entry={"on": "policy", "method": "!gauss-hermite"},
    address="policy",
    words=("Method target 'policy' in stage 'cons'", "builder", "admits"),
)

# The places of the methods of a policy block, each refused where a methods
# file writes it elsewhere. `!egm` stands at the Evaluation of a block that
# writes the grid line, `m_d[>] = a + c[>]` in `cons.bl`, or on a maximization
# that carries its first-order condition as a property; the policy block of
# `port.bl` writes a `solve` of the first-order condition in the share and
# neither of the two, so the method is refused there.
EXAMPLES["egm-without-a-grid-line"] = Example(
    rule="method-attachment",
    corpus="port",
    origin=CORPUS["port"],
    provokes="methodize",
    entry={"on": "policy", "method": "!egm"},
    address="policy",
    words=("Method target 'policy' in stage 'port'", "the grid line", "writes neither"),
)

# `!vfi` is a handler for the whole backward decision builder, `cntn_to_dcsn`,
# which it realizes with its maximization; it stands on no row of the policy
# block, and the maximization of `ez_savings.bl`, the row `policy.objective`
# forms, named by its occurrence, is refused.
EXAMPLES["vfi-on-a-maximization"] = Example(
    rule="method-attachment",
    corpus="ez_savings",
    origin=CORPUS["ez_savings"],
    provokes="methodize",
    entry={"on": "policy.objective.argmax", "method": "!vfi"},
    address="policy.objective.argmax",
    words=(
        "Method target 'policy.objective.argmax' in stage 'ez_savings'",
        "!vfi does not admit target kind operator argmax",
        "stands on the backward decision builder alone",
        "write `on: cntn_to_dcsn`",
    ),
)

# A dotted id `x.y` attaches its line to the line `x` of the block as a
# property; `cons.bl` at 476c31134 wrote `argmax.FOC` and
# `argmax.inverse_dcsn_kernal`, and no line of its policy block carries the id
# `argmax`, so the stage is refused at the first of the two lines, under
# `readable-form`, by the construction's check of the dotted ids.
EXAMPLES["dotted-id-without-an-owning-line"] = Example(
    rule="readable-form",
    corpus="cons",
    origin=CORPUS["cons"],
    changes=(
        ("[id=InvEuler]", "[id=argmax.FOC]"),
        ("[id=endoggrid]", "[id=argmax.inverse_dcsn_kernal]"),
    ),
    address="policy.argmax.FOC",
    words=("'argmax.FOC'", "'argmax'", "does not write"),
)

# A policy block states its policy by the line that writes it; the block of
# `cons.bl` without its identification line `c = c[>]` writes the candidate
# and the cash on hand at each saving and no line defining the policy, and no
# operation is inferred for the line it omits, so the stage is refused under
# `output-defined`.
EXAMPLES["omitted-identification-line"] = Example(
    rule="output-defined",
    corpus="cons",
    origin=CORPUS["cons"],
    changes=(("    c      = c[>]                    :: [id=cons_choice]\n", ""),),
    address="policy",
    words=("block 'policy'", "cons:dcsn:c"),
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
    ),
    "recipe-slot-unknown": Example(
        rule="",
        provokes="load_recipe",
        fills={"fil": {"β": 0.9}},
        address="fil",
        words=("'fil'", "$fill", "$method_switch"),
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
    ),
    "slot-value-not-a-mapping": Example(
        rule="",
        provokes="load_recipe",
        fills={"fill": "β: 0.9"},
        address="fill",
        words=("'fill'", "str"),
    ),
    "fill-names-nothing": Example(
        rule="",
        provokes="load_recipe",
        fills={"fill": {"beta": 0.9}},
        address="fill",
        words=("'beta'", "two_nodes declares", "β"),
    ),
    "fill-mixes-kinds": Example(
        rule="",
        provokes="load_recipe",
        fills={"fill": {"β": 0.9, "n_k": 4}},
        address="fill",
        words=("β", "n_k"),
    ),
    "trellis-file-shape": Example(
        rule="",
        provokes="load_trellis",
        files={"broken.yml": "stages: []\n"},
        file="broken.yml",
        address="periods",
        words=("periods",),
    ),
    "record-shape": Example(
        rule="",
        provokes="elaborate_stage",
        record={"stage": {"text": TWO_NODES, "origin": "t.bl"}},
        address="record",
        words=("missing fields", "'calibration'", "'methods'", "'settings'"),
    ),
    "period-join-cycle": Example(
        rule="",
        provokes="forward_order",
        stages={"disc": "disc", "port": "port"},
        connectors=[{"disc.a": "port.k"}, {"port.m_next": "disc.a"}],
        address="periods[0]",
        words=("disc continues to 'a'", "port arrives at 'k'", "port continues to 'm_next'", "disc arrives at 'a'"),
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
    ),
    # a path read before any file is opened, so that the refusal names no
    # directory of the machine
    "readable-file": Example(
        rule="",
        provokes="load_stage",
        path="cons.txt",
        address=None,
        words=("load_stage reads a stage file", "cons.txt is no .bl file"),
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
)


# --- the examples of the rules of a method block ---

# The consumption stage of specification 0.6 §3, which writes the
# maximization alone, and the block file of its §4 that opens the policy
# builder with the endogenous grid method; the two rules of a method block
# are each provoked by a change of the block file, which a methods file of
# one entry names under `block:` (`provokes="methodize-block"`).
SPEC_06_STAGE = """@stage: cons
Xm := ℝ₊₊
Xa := ℝ₊
ρ : (1, inf)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
Γ(x : ℝ₊₊) := (0, x]

[id=arvl_to_dcsn, (m : Xm) : !arvl -> (m_d : Xm) : !dcsn] {
    m_d = m
}
[id=dcsn_to_cntn, (m_d, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m_d - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>]) :: [id=optimality]
}
"""
SPEC_06_BLOCK = """@stage: cons
𝑑𝑢     := D_{c}(𝑢)
𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)

[id=egm, (V[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0  :: [id=InvEuler]
    m_d[>] = a + c[>]                    :: [id=grid]
    c      = c[>]                        :: [id=identification]
}
"""
_EGM_ENTRY = {"on": "policy", "method": "!egm", "block": "egm.bl"}

# an input the policy builder does not have listed on the block's header; a
# block's inputs are among the builder's own (AMD-MB-001 §5.1)
EXAMPLES["block-header-mismatch"] = Example(
    rule="block-header-mismatch",
    text=SPEC_06_STAGE,
    files={"egm.bl": _changed(SPEC_06_BLOCK, ("(V[>]) : !cntn", "(V[>], dV[>]) : !cntn"))},
    origin="egm.bl",
    provokes="methodize-block",
    entry=_EGM_ENTRY,
    address="egm",
    words=(
        "the block 'egm' of egm.bl",
        "(V[>], dV[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn",
        "(V[>]) : !cntn -> (c) : !dcsn",
        "no other field",
    ),
    write=(
        "List the builder's inputs alone, write a derivative of a value as the term "
        "`D_{a}V[>]` in the lines, and write the builder's outputs on the block's output side."
    ),
)
# the inverse marginal utility called and not defined
EXAMPLES["block-name-undefined"] = Example(
    rule="block-name-undefined",
    text=SPEC_06_STAGE,
    files={"egm.bl": _changed(SPEC_06_BLOCK, ("𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)\n", ""))},
    origin="egm.bl",
    provokes="methodize-block",
    entry=_EGM_ENTRY,
    address="egm.InvEuler",
    words=("calls '𝑑𝑢𝑖𝑛𝑣'", "neither the stage file nor the block file defines"),
    write=(
        "Define the function in the block file, `𝑑𝑢𝑖𝑛𝑣 := Inv(𝑑𝑢)`, or call a function the "
        "stage file defines."
    ),
)
# An example of the rule `method-attachment`: with the block of
# specification 0.6 §4 bound on the policy builder, an entry names an
# occurrence in the builder's declared line, which forms no operation of the
# opened builder (decision SC-23).
EXAMPLES["method-at-a-line-a-block-stands-in-for"] = Example(
    rule="method-attachment",
    text=SPEC_06_STAGE,
    origin="cons.bl",
    files={"egm.bl": SPEC_06_BLOCK},
    provokes="methodize-block",
    methods={
        "methods": [
            {"on": "policy", "method": "!egm", "block": "egm.bl"},
            {"on": "policy.optimality.argmax", "method": "!max"},
        ]
    },
    address="policy.optimality.argmax",
    words=("names a place in the line policy.optimality", "stands in for", "egm.bl"),
)


# A third example of the rule `method-attachment`: `!marginals` adds a
# marginal block's lines to a backward value builder, and the policy builder
# writes the policy, no value (specification 0.6 §5.1).
EXAMPLES["marginals-on-the-policy-builder"] = Example(
    rule="method-attachment",
    text=SPEC_06_STAGE,
    origin="cons.bl",
    provokes="methodize",
    entry={"on": "policy", "method": "!marginals", "block": "egm.bl"},
    address="policy",
    words=("adds a marginal block's lines to a backward value builder", "writes no value"),
)
