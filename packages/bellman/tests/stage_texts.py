"""The stage texts that the tests elaborate, their lines, their calibrations
and the identities of their declarations, and functions that return a text
with one line changed."""

from application_files import BUFFER_STOCK_FILE, COPIED_FILES_FOLDER, CORPUS, ROOT

from bellman.refusal_examples import BRANCHING, EXPLICIT_POLICY, INVERSE_EULER, TWO_NODES


def changed(text, *changes):
    """`text` with each `(written, replacement)` pair applied in order; a
    written fragment that the text does not hold exactly once raises
    `ValueError`, so that no change is lost."""
    for written, replacement in changes:
        count = text.count(written)
        if count != 1:
            raise ValueError(f"the text holds this fragment {count} times, not once: {written!r}")
        text = text.replace(written, replacement)
    return text


# the two changes of the buffer-stock stage file by which its feasible set
# also reads the continuation field Θ[>], which the header of its policy
# block then lists beside the borrowing bound L. Θ is a constant beside V,
# `Θ[>] : ℝ @ !vlu @ !cnst`, since a feasible set reads only fields known
# before the choice, and the feasible set reads it as a lower bound on the
# saving x - c.
CHANGES_TO_READ_THE_SECOND_FIELD = (
    (
        "Γ_c(x : Xm) := {c : ℝ₊₊ | c < x - L}",
        "Γ_c(x : Xm) := {c : ℝ₊₊ | c < x - L, x - c >= Θ[>]}",
    ),
    (
        "[id=policy, (V[>] : ℝ @ !vlu, L) : !cntn ->",
        "[id=policy, (V[>] : ℝ @ !vlu, Θ[>] : ℝ @ !vlu @ !cnst, L) : !cntn ->",
    ),
)


# the two changes of the buffer-stock stage file by which its value block
# and its arrival block write the constant Θ as they write the value
CHANGES_TO_WRITE_THE_SECOND_FIELD = (
    (
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, L : (-inf, 0] @ !vlu @ !cnst, c) : !cntn"
        " -> (V : ℝ @ !vlu, L) : !dcsn] {\n"
        "    V = 𝑢(c) + β*V[>]               :: [id=value]\n",
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, Θ[>] : ℝ @ !vlu @ !cnst,"
        " L : (-inf, 0] @ !vlu @ !cnst, c) : !cntn"
        " -> (V : ℝ @ !vlu, Θ : ℝ @ !vlu @ !cnst, L) : !dcsn] {\n"
        "    V = 𝑢(c) + β*V[>]\n"
        "    Θ = Θ[>]\n",
    ),
    (
        "[id=dcsn_to_arvl, (V, L) : !dcsn"
        " -> (V[<] : ℝ @ !vlu, L[<] : (-inf, 0] @ !vlu @ !cnst) : !arvl] {\n"
        "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]\n",
        "[id=dcsn_to_arvl, (V, Θ, L) : !dcsn"
        " -> (V[<] : ℝ @ !vlu, Θ[<] : ℝ @ !vlu @ !cnst, L[<] : (-inf, 0] @ !vlu @ !cnst)"
        " : !arvl] {\n"
        "    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)\n"
        "    Θ[<] = E_{ψ,ξ}(Θ)\n",
    ),
)


def renamed(text, name):
    """The stage text `text` with its stage named `name`."""
    _, rest = text.split("\n", 1)
    return f"@stage: {name}\n{rest}"


def two_nodes_text_with_parameter_sets(declaration, interest="R : ℝ₊₊"):
    """The two-node stage, the declaration of β replaced by `declaration`
    and that of R by `interest`.

    The two-node stage is the stage `two_nodes` of the module
    `bellman.refusal_examples`, whose block `cntn_to_dcsn` writes two lines
    marked `!node`, each the expectation over the two shocks y and z."""
    return changed(TWO_NODES, ("β : ℝ₊₊\n", declaration + "\n"), ("R : ℝ₊₊\n", interest + "\n"))


# the declarations of β and R of the two-node stage, one after the other
BETA_AND_R_DECLARATIONS = "β : ℝ₊₊\nR : ℝ₊₊\n"


# the listing of the arrival field k on the header of the block
# arvl_to_dcsn of the two-node stage
TWO_NODES_ARRIVAL_K_DECLARATION = "(k : ℝ) : !arvl"


# the sentence of every refusal of `if`, `then` or `else` written as a name
IF_THEN_ELSE_REFUSAL = (
    "`if`, `then` and `else` are the words of a definition by cases, and none of them is a name"
)


# the declarations of the settings of a grid on m at the Evaluation of the
# explicit policy builder of the perfect-foresight stage
EXPLICIT_GRID_SETTINGS = "n : ℕ\nlo : Xm\nhi : Xm\n"


def explicit_policy_with_entries(entries):
    """The text of the addition `EXPLICIT_POLICY` after its first line, the
    header of whose policy block also writes `entries`."""
    return changed(
        EXPLICIT_POLICY.split("\n", 1)[1],
        (
            "[id=policy, policy.method : !explicit]",
            f"[id=policy, policy.method : !explicit | {entries}]",
        ),
    )


# a stage whose forward measures are refused, since its shock is declared
# with a family that the package does not admit
UNADMITTED_FAMILY_AT_ARRIVAL = """@stage: opaque_family
z : ℝ₊
z ~ Weird(0.2, 0.8)
[id=arvl_to_dcsn, (x : ℝ₊, z) : !arvl -> (y : ℝ₊) : !dcsn] { y = x + z }
[id=cntn_to_dcsn, (W : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
 V = E_{z}(W) :: [id=average]
}
"""


# a small stage named cons, with the parameter ρ of cons.bl and the decision
# state m_d; its decision value is the continuation value read through the law
# of motion and divided by 1 − ρ, so that a calibration of ρ establishes the
# condition `arithmetic-definedness`, that the divisor 1 − ρ is nonzero
SMALL_CONS = """@stage: cons
ρ : [1, inf)
[id=dcsn_to_cntn, (m_d : ℝ₊₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = V[>]/(1-ρ)
}
"""


# the methods of the small stage: a linear representation of the decision
# value on a grid of m_d, whose three settings the addition declares
SMALL_CONS_METHODS = {
    "text": (
        "@methods: cons\nn_m : ℕ\nm_min : ℝ₊₊\nm_max : ℝ₊₊\n"
        "cntn_to_dcsn.evaluate.method : !Linear\n"
        "cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))\n"
    ),
    "origin": "cons.methods.bl",
}


# the two places where the buffer-stock stage file declares the set of `a`
# and of `k`, and the line that defines that set
(
    BUFFER_STOCK_ARRIVAL_K_DECLARATION,
    BUFFER_STOCK_CONTINUATION_A_DECLARATION,
    BUFFER_STOCK_XA_DEFINITION,
) = "(k : Xa, ψ, ξ)", "(a : Xa)", "Xa := ℝ\n"


def buffer_stock_text_with_changes(*changes):
    """The text of the buffer-stock stage file with each pair (text as
    written, text as changed) replaced once."""
    return changed(buffer_stock_text(), *changes)


# where a definition by cases stands, the advice of a refusal of the parser
# at a line that writes the word `if`. The language fixes the three places
# that it names: the whole right side of a definition without arguments, the
# whole right side of a line of a block, and a branch of another conditional.
# The words are those of the package's advice, which the tests compare whole
CONDITIONAL_PLACE = (
    "a conditional, `if … then … else …`, stands as the whole right side of a definition "
    "without arguments, `x := if a < b then 1 else 2`, with or without a declared set. "
    "It can also be the whole right side of a block equation, "
    "`x = if a < b then 1 else 2`, or a branch of another conditional. "
    f"{IF_THEN_ELSE_REFUSAL}"
)


def line_of(text, written):
    """The number of the one line of `text` that holds `written`."""
    (number,) = [n for n, line in enumerate(text.splitlines(), 1) if written in line]
    return number


# the inverse Euler form of the consumption stage with the endogenous grid
# method, its exogenous grid of savings and its handler written in the policy
# block's header, and the decision value's representation with its grid of
# resources in the value builder's header; the policy's Evaluation writes no
# grid, since the method computes its knots
EGM_STAGE = changed(
    INVERSE_EULER,
    (
        "[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {",
        "[id=policy, method : !egm, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn\n"
        "    | grid : !Cartesian(a=(a_min, a_max, n_a, !expmult(nest=grid_phi)))\n"
        '    | handler : "cons-port:egm" | evaluate.method : !Linear] {',
    ),
    (
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {",
        "[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn\n"
        '    | evaluate.method : !Linear(extrap="clamp")\n'
        "    | evaluate.grid : !Cartesian(m=(m_min, m_max, n_m))] {",
    ),
)


# the settings that the two grids read, declared with their sets as a
# methods file declares them
SAVINGS_GRID_SETTINGS = """@methods: t
n_a : ℕ              :: ["number of points of the savings grid"]
a_min : ℝ₊           :: ["lower bound of the savings grid"]
a_max : ℝ₊           :: ["upper bound of the savings grid"]
grid_phi : ℝ₊₊       :: ["nesting factor of the exponentially spaced savings grid"]
n_m : ℕ              :: ["number of points of the grid of resources"]
m_min : ℝ₊           :: ["lower bound of the grid of resources"]
m_max : ℝ₊           :: ["upper bound of the grid of resources"]
"""


# the values of those settings
SAVINGS_GRID_VALUES = {
    "n_a": 30,
    "a_min": 0.0,
    "a_max": 20.0,
    "grid_phi": 3.0,
    "n_m": 50,
    "m_min": 0.1,
    "m_max": 10.0,
}


def addition_of_text(text, origin="methods.bl"):
    """The record of an addition: its text and the name of its file."""
    return {"text": text, "origin": origin}


def methods_addition(stage, *lines):
    """The addition to the stage named `stage` that holds `lines`, as a
    mapping of its text and its origin `<stage>.methods.bl`."""
    return {
        "text": f"@methods: {stage}\n" + "".join(f"{line}\n" for line in lines),
        "origin": f"{stage}.methods.bl",
    }


def two_nodes_text_with_changes(
    backward=None, transition=None, declarations=None, header=None, objective=None
):
    """The two-node stage with its four backward lines, its transition line,
    its two shock declarations, its backward header or the objective of its
    maximization replaced.

    The package refuses a maximization whose objective is not the right side
    of the decision value V, with its nodes written out. A test that changes
    that right side therefore passes the changed right side as `objective`."""
    lines = (
        (
            "    W = β*V[>]\n    N1 = E_{y,z}(W) :: [id=first, !node]\n"
            "    N2 = E_{y,z}(W) :: [id=second, !node]\n    V = N1 + N2\n",
            backward,
        ),
        ("    a = k_d*(c*y + (1-c)*R) + z\n", transition),
        ("y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n", declarations),
        ("(V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn]", header),
        (
            "(E_{y,z}(β*V[>]) + E_{y,z}(β*V[>])) :: [id=objective]",
            None if objective is None else f"({objective}) :: [id=objective]",
        ),
    )
    return changed(TWO_NODES, *[(old, new) for old, new in lines if new is not None])


def two_nodes_text_with_joint_normal_law(
    covariance="((1,r),(r,1))",
    backward="    V = E_{z}(E_{y}(V[>])) :: [id=value]\n",
    r_set="[-1,1]",
    objective="E_{z}(E_{y}(V[>]))",
):
    """The two-node stage with the joint normal law
    `(y,z) ~ N((0,0), covariance)`, the parameter `r` declared in `r_set`,
    the transition `a = y`, the one backward line `backward` and the
    objective `objective` of its maximization, the right side of that
    line."""
    return two_nodes_text_with_changes(
        backward=backward,
        transition="    a = y\n",
        declarations=f"z : ℝ\nr : {r_set}\n(y, z) ~ N((0,0),{covariance})\n",
        objective=objective,
    )


def corpus_text(name):
    """The text of the stage file of the corpus stage `name`."""
    return (ROOT / CORPUS[name]).read_text(encoding="utf-8")


# the three lines of the endogenous grid method: the candidate line with its
# clause, the grid line and the identification, which state the candidate at
# each saving, the cash on hand at each saving and the policy; they write the
# third spelling of the Kuhn–Tucker condition, as section 4.3 of the public
# page docs/Bellman-Sym/10-constraints.md describes it. The application
# writes these lines in its methods file, not in its stage file.
EGM_LINES = (
    "    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0       :: [id=InvEuler]\n"
    "    m_d[>] = a + c[>]                :: [id=endoggrid]\n"
    "    c      = c[>]                    :: [id=cons_choice]\n"
)


# the first-order condition with its clause, written as an operative line
# of the policy block
FIRST_ORDER_CONDITION_LINE = "    𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0       :: [id=euler]\n"


def cons_text_with_policy_lines(name, lines):
    """The text of the consumption stage file `cons.bl` with its stage named
    `name`, the inverse marginal utility `𝑑𝑢𝑖𝑛𝑣` defined, and its
    maximization statement marked `!doc` and followed by the policy lines
    `lines`."""
    inverse = "𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)\n"
    return changed(
        corpus_text("cons"),
        ("@stage: cons\n", f"@stage: {name}\n" + inverse),
        (ARGMAX_LINE, ARGMAX_DOC_LINE + lines),
    )


# the input side of the header of the decision builder `cntn_to_dcsn` of
# `cons.bl`, which lists the continuation value and the control `c` without a
# perch word
INPUT_SIDE_WITH_THE_CONTROL = "(V[>] : [-inf, inf) @ !vlu, c) : !cntn ->"


# the maximization statement of the consumption stage marked `!doc`, a
# declaration that forms no operation
ARGMAX_DOC_LINE = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality, !doc]\n"


# the same statement without the mark, the operation that outputs the
# policy, as `cons.bl` writes it
ARGMAX_LINE = "    c      = argmax_{cp : Γ(m_d)}(𝑢(cp) + V[>])   :: [id=optimality]\n"


# the first-order condition with its clause, attached to the maximization
# statement as its property by the dotted id `optimality.euler`; a property
# forms no operation, has no address and takes no method
FIRST_ORDER_CONDITION_PROPERTY_LINE = (
    "    𝑑𝑢(c) = D_{a}V[>] ⟂ m_d - c >= 0                :: [id=optimality.euler]\n"
)


# the candidate line of `EGM_LINES`, which tests replace; the grid line and the
# identification, its second and third lines, are not given a name here
CANDIDATE_LINE, _, _ = EGM_LINES.splitlines(keepends=True)


def branching_text(*changes):
    """`BRANCHING` with each `(line as written, line as changed)` pair
    applied; a line that the text does not hold once is refused, so that a
    change is never lost."""
    return changed(BRANCHING, *changes)


# a stage with one control of two coordinates, `u : ℝ × ℝ`, chosen jointly
JOINT_CHOICE = """@stage: joint_choice
[id=arvl_to_dcsn, (x : ℝ) : !arvl -> (x_d : ℝ) : !dcsn] {
 x_d = x
}
[id=dcsn_to_cntn, (x_d, u : ℝ × ℝ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
 a = x_d + u[1] + u[2]
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, u) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
 V = -u[1]^2-u[2]^2+V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
 V[<] = V
}
[id=policy, (V[>] : ℝ @ !vlu) -> (u : ℝ × ℝ @ !ctrl) : !dcsn] {
 u = argmax_{u}(-u[1]^2-u[2]^2+V[>]) :: [id=choice]
}
"""


# the line of the budget set of the public page on constraints, a feasible
# set of a joint choice: a comprehension whose first two coordinates sum to
# its argument
BUDGET_SET_LINE = "Γ(z : ℝ₊) := {q : ℝ₊ × ℝ₊ × ℝ₊ | q[1] + q[2] = z}"


# a stage whose shock θ has a law that reads the shock η directly and the
# Markov state s through a key selection; a key selection, such as
# `(σ, 0)[s]`, takes the entry of a tuple by the value of the Markov state s
TWO_PARENT_SHOCKS_TEXT = """@stage: key_selection_reads

Xk := ℝ₊
Xm := ℝ₊₊
Xa := ℝ₊
S  := {lo, hi}

β : (0,1)
γ : ℝ₊₊
R : ℝ₊₊
P : [0,1]
σ : ℝ₊

s : S
s ~ MarkovChain(P, S)              :: ["a two-point state; an admitted family, \
so that the forward view is constructed"]
η : ℝ
η ~ N(0, 1)                        :: ["a parent read directly by the law of θ"]
θ : ℝ₊₊
θ ~ LogNormal(η, (σ, 0)[s])        :: ["a shock whose law reads η directly and s \
through a key selection"]

𝑢(c : ℝ₊₊) := c^(1-γ)/(1-γ)         :: [id=util]
𝑑𝑢(c : ℝ₊₊) := c^(-γ)               :: [id=marg_util]
𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/γ)          :: [id=inv_marg_util]
𝒞(x : ℝ₊₊) := (0, x]                 :: [id=feasible]

[id=arvl_to_dcsn, (k : Xk, s, θ) : !arvl -> (m : Xm) : !dcsn] {
    m = R*k + (1, 2)[s]*θ            :: [id=market_resources, "reads s only through a key \
selection"]
}

[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : Xa) : !cntn] {
    a = m - c                        :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V      = 𝑢(c) + β*V[>]           :: [id=value]
    D_{m}V = 𝑑𝑢(c)                   :: [id=marginal]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<]      = E_{s,θ,η}(V)         :: [id=value]
    D_{k}V[<] = E_{s,θ,η}(R * D_{m}V) :: [id=marginal]
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c    = argmax_{c : 𝒞(m)}(𝑢(c) + β*V[>])   :: [id=optimality, !doc]
    c[>] <= 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])                 :: [id=InvEuler]
    m[>] = a + c[>]                            :: [id=endoggrid]
    c    = c[>]                                :: [id=cons_choice]
}
"""


# the portfolio stage of the model ConsRiskyAsset, from the folder of copies
CONS_RISKY_ASSET_PORT_TEXT = (ROOT / COPIED_FILES_FOLDER / "ConsRiskyAsset/port.bl").read_text(
    encoding="utf-8"
)


# a stage with a value and its stated derivative on one arrival edge with
# two shocks, whose backward block and shock declarations the tests replace;
# `k_d = k + y + z` puts both shocks in the law of motion of `arvl_to_dcsn`,
# so the arrival edge integrates both
BUNDLES = """@stage: bundles
β : ℝ₊₊
R : ℝ₊₊
y : ℝ
y ~ N(0,1)
z : ℝ
z ~ N(0,1)
Γ(k : ℝ) := (0,1]

[id=arvl_to_dcsn, (k : ℝ, y, z) : !arvl -> (k_d : ℝ) : !dcsn] {
    k_d = k + y + z
}
[id=dcsn_to_cntn, (k_d, c : !ctrl @ ℝ₊₊) : !dcsn -> (a : ℝ) : !cntn] {
    a = k_d - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V        = c + β*V[>]           :: [id=value]
    D_{k_d}V = c                    :: [id=marginal]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<]     = E_{y,z}(V)           :: [id=value]
    D_{k}V[<] = E_{y,z}(R*D_{k_d}V)  :: [id=marginal]
}
[id=policy, (V[>] : ℝ @ !vlu) -> c] {
    c = argmax_{cp : Γ(k_d)}(cp + β*V[>]) :: [id=objective]
}
"""


def bundles_text(arrival=None, declarations=None, decision=None):
    """The bundle stage with its arrival block, its shock declarations or its
    decision block replaced."""
    lines = (
        (
            """    V[<]     = E_{y,z}(V)           :: [id=value]
    D_{k}V[<] = E_{y,z}(R*D_{k_d}V)  :: [id=marginal]
""",
            arrival,
        ),
        ("y ~ N(0,1)\nz : ℝ\nz ~ N(0,1)\n", declarations),
        (
            """    V        = c + β*V[>]           :: [id=value]
    D_{k_d}V = c                    :: [id=marginal]
""",
            decision,
        ),
    )
    return changed(BUNDLES, *[(old, new) for old, new in lines if new is not None])


# the discounting stage of the public page docs/Bellman-Sym/06-period.md,
# whose continuation field k_next joins the investment stage's k through the
# connector {k_next: k}; no corpus stage has that field, so the text stands
# here
DISC_WITH_K_NEXT_TEXT = """@stage: disc
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (k_next : ℝ₊) : !cntn] {
    k_next = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# two stages for the tests of the connections between stage occurrences. No
# corpus stage has two state fields whose names stand at both its arrival and
# its continuation, and none has one such field. `TWO_FIELDS` has the arrival
# states `a` and `b` and the continuation states `a` and `b`, so that two of
# its occurrences can swap the two fields at once or join them crossed.
# `UNCHANGED` carries `a` unchanged from arrival to continuation and discounts
# its value, so that no name fixes the direction of a join between two of its
# occurrences.
TWO_FIELDS = """@stage: two_fields
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊, b : ℝ₊) : !arvl -> (a_d : ℝ₊, b_d : ℝ₊) : !dcsn] {
    a_d = a
    b_d = b
}
[id=dcsn_to_cntn, (a_d, b_d) : !dcsn -> (a : ℝ₊, b : ℝ₊) : !cntn] {
    a = a_d
    b = b_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


UNCHANGED = """@stage: unchanged
β : (0,1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# a stage that carries `a` in the interval [a_min, ∞) from its arrival perch
# to its continuation perch
BOUNDED = """@stage: bounded
a_min : ℝ
β : (0,1)
[id=arvl_to_dcsn, (a : [a_min, inf)) : !arvl -> (a_d : ℝ) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d) : !dcsn -> (a : [a_min, inf)) : !cntn] {
    a = a_d
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# a stage whose shock ε, read by the law of motion of `dcsn_to_cntn`, is
# declared with a family that the package does not admit
UNADMITTED_FAMILY_AFTER_DECISION = """@stage: no_law
β : (0,1)
ε : ℝ
ε ~ Weird(0, 1)
[id=arvl_to_dcsn, (a : ℝ₊) : !arvl -> (a_d : ℝ₊) : !dcsn] {
    a_d = a
}
[id=dcsn_to_cntn, (a_d, ε) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = a_d + ε
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*E_{ε}(V[>])
}
[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}
"""


# the stage `grids`: the state m on Xm, the control c whose feasible set at m
# is [0, m], and the finite set B = {1, 2} of resources; the tests type the
# backward decision builder cntn_to_dcsn with !vfi and a grid
GRID_STAGE = """@stage: grids
B := {1, 2}
Xm := ℝ₊
Γ_c(m : Xm) := [0, m]
𝑢(c : ℝ₊) := c
[id=dcsn_to_cntn, (m : Xm, c : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + V[>]) :: [id=optimality]
}
"""


# the same choice with a second state z carried to the continuation perch, so
# that a grid on (m, z) can name a factor for m alone, and a declared set of
# pairs of reals, on which points of two coordinates are declared
TWO_STATE_GRID_STAGE = """@stage: grids
Xm := ℝ₊
X2 := ℝ × ℝ
Γ_c(m : Xm) := [0, m]
𝑢(c : ℝ₊) := c
[id=dcsn_to_cntn, (m : Xm, z : ℝ, c : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ₊, z_n : ℝ) : !cntn] {
    a = m - c
    z_n = z
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + V[>]
}
[id=policy, (V[>]) : !cntn -> (c) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + V[>]) :: [id=optimality]
}
"""


# the settings the grids of the tests name, declared as a methods file
# declares them, and their values: two control nodes, m in {1, 2} and z in
# {-1, 1}
GRID_SETTINGS = "n_c : ℕ\nm_lo : ℝ₊\nm_hi : ℝ₊\nn_m : ℕ\nz_lo : ℝ\nz_hi : ℝ\nn_z : ℕ\n"


GRID_VALUES = {"n_c": 2, "m_lo": 1.0, "m_hi": 2.0, "n_m": 2, "z_lo": -1.0, "z_hi": 1.0, "n_z": 2}


# Two lines of the perfect-foresight text that `perfect_foresight_text` gives,
# and the start of a third. `GROWTH_LINE` declares the growth factor on line 7,
# so that a line inserted after it stands on line 8, as the definition of human
# wealth does; `HUMAN_WEALTH_DEFINITION` is that definition without its
# annotation; `RESOURCES_LINE` is the law of motion of market resources.
GROWTH_LINE = 'Γ : ℝ₊₊          :: ["permanent income growth factor"]\n'
HUMAN_WEALTH_DEFINITION = "h := 1/(1 - Γ/R)"
RESOURCES_LINE = "    m = R_n*k + 1                   :: [id=market_resources]"


# the two branches of human wealth by cases: 1/(1 - Γ/R) where Γ < R, and
# the infinity otherwise
HUMAN_WEALTH_RIGHT_SIDE_BY_CASES = "if Γ < R then 1/(1 - Γ/R) else inf"


def perfect_foresight_text(*changes, table=False):
    """The text of the perfect-foresight stage of the module
    `bellman.refusal_examples`, whose derived parameters are h and R_n, with
    each pair (line as written, line as changed) of `changes` replaced once.

    With `table`, the text also holds two parameters `K` and `Y`, three
    numbers each, and a line of the arrival block that reads them as an
    authored table, `W = evaluate(K, Y, k)`, at the address
    `dcsn_to_arvl.table`. The tests of explicit solutions, of representations
    and of derived parameters read this one stage."""
    from bellman.refusal_examples import PERFECT_FORESIGHT

    text = changed(PERFECT_FORESIGHT, *changes)
    if not table:
        return text
    value = "    V[<] = Γ^(1-ρ) * V              :: [id=value]\n"
    return changed(
        text,
        (
            GROWTH_LINE,
            GROWTH_LINE + 'K : ℝ × ℝ × ℝ    :: ["the knots of the table"]\n'
            'Y : ℝ × ℝ × ℝ    :: ["the values of the table"]\n',
        ),
        (value, value + "    W = evaluate(K, Y, k)            :: [id=table]\n"),
    )


# the addition that defines the marginal propensity to consume κ, the
# method's derived parameter, which stage.par lists once it is read
MPC_ADDITION = {
    "text": "@methods: perfect_foresight\n"
    'κ := 1 - (R*β)^(1/ρ)/R   :: ["the marginal propensity to consume"]\n',
    "origin": "closed_form.bl",
}


# the declaration, in the buffer-stock stage file, of the probability ℘ that
# the transitory shock is zero, after which tests declare their lines or
# which they replace
ZERO_DRAW_PROBABILITY_LINE = 'p_zero : (0,1)   :: ["probability ℘ of a zero transitory draw"]\n'


def buffer_stock_text(scale="σ_ξ"):
    """The text of the buffer-stock stage file, which defines the log-mean
    μ_ξ := -log(1 - p_zero) - σ_ξ^2/2 of the positive transitory draw as a
    derived parameter, with `scale` the standard deviation of the logarithm
    of that draw. With `scale="μ_ξ"` the log-mean also stands as the scale,
    which is then negative where σ_ξ² exceeds −2 log(1 − p_zero)."""
    text = (ROOT / BUFFER_STOCK_FILE).read_text(encoding="utf-8")
    if scale != "σ_ξ":
        text = changed(text, ("LogNormal(μ_ξ, σ_ξ)", f"LogNormal(μ_ξ, {scale})"))
    return text


# the buffer-stock stage whose value block and arrival block write the
# constant Θ
BUFFER_STOCK_WRITING_THE_SECOND_FIELD = changed(
    buffer_stock_text(), *CHANGES_TO_WRITE_THE_SECOND_FIELD
)


# the buffer-stock stage whose feasible set alone reads the constant Θ
BUFFER_STOCK_READING_THE_SECOND_FIELD = changed(
    buffer_stock_text(), *CHANGES_TO_READ_THE_SECOND_FIELD
)


# the definition of the feasible set in the buffer-stock stage file, which
# reads the borrowing bound L that the backward blocks declare
BUFFER_STOCK_FEASIBLE_SET_LINE = (
    "Γ_c(x : Xm) := {c : ℝ₊₊ | c < x - L}   :: [id=feasible_consumption]\n"
)


# A stage whose arrival value integrates a Markov shock z, drawn from the row
# of its transition matrix that the arrival state z_pre selects, and a shock
# d with a finite law of two points, so that the places E_z and E_d, which
# the declaration examples of !exact_markov, !markov, !markov_expectation and
# !sum name, stand in it.
EXAMPLE_SHOCKS_TEXT = """@stage: example_shocks

β   : (0,1)    :: ["discount factor"]
ρ_z : [0,1]    :: ["the probability that the Markov state z keeps its value"]
p_d : [0,1]    :: ["the probability of the second point of the shock d"]

z : ℝ₊₊
z ~ MarkovChain(((ρ_z, 1 - ρ_z), (1 - ρ_z, ρ_z)), (1, 2), z_pre)\
    :: ["a Markov state of two points"]
d : ℝ
d ~ Bernoulli(p_d)    :: ["a shock with a finite law of two points"]

[id=arvl_to_dcsn, (k : ℝ₊, z_pre : ℝ₊₊, z, d) : !arvl -> (m : ℝ₊) : !dcsn] {
    m = z*k + d                    :: [id=resources]
}

[id=dcsn_to_cntn, (m) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m                          :: [id=savings]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = β*V[>]                     :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{z}(E_{d}(V))         :: [id=value]
}
"""


# the candidate line of the adjuster's consumption stage of the durables model
# in the file `ADJUSTER_CONS_WITH_EGM_LINES_FILE`, line 39, and the same line
# with the clause at the borrowing limit
DURABLES_CANDIDATE_LINE = (
    "    c[>]          <= 𝑢_c_inv(β*D_{a_nxt_adj}V[>])"
    "                                              :: [id=InvEuler]\n"
)


DURABLES_CLAUSE_LINE = (
    "    c[>]          <= 𝑢_c_inv(β*D_{a_nxt_adj}V[>]) ⟂ a_nxt_adj >= 0  :: [id=InvEuler]\n"
)


# the part of the methods file of the worker's consumption stage that types
# the upper envelope of its policy builder by the fast upper-envelope scan
WORKER_CONS_ENVELOPE = (
    '\n    | upper_env.method : !FUES(m_bar=m_bar) | upper_env.handler : "dcsmm:EGM_UE"]'
)


# A location stage: J city locations, the previous location i and the chosen
# location j among them, a location payoff δ and a distance table on city
# pairs. The value of choosing j from i is
#     V(i, j) = δ(j) − m_0 − m_1·D(j, i) + β·V≻.
LOCATION_TEXT = """@stage: location
J   : ℕ
L_J := {1, …, J}
β   : (0,1)
m_0 : ℝ₊
m_1 : ℝ₊
δ   : L_J → ℝ
dist : L_J × L_J → ℝ₊

[id=arvl_to_dcsn, (i : L_J) : !arvl -> (i_d : L_J) : !dcsn] {
    i_d = i    :: [id=carry]
}

[id=dcsn_to_cntn, (i_d, j : !ctrl @ L_J) : !dcsn -> (i_n : L_J) : !cntn] {
    i_n = j    :: [id=move]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, j) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = δ[j] - m_0 - m_1*dist[j][i_d] + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (j : !ctrl) : !dcsn] {
    j = argmax_{jp : L_J}(δ[jp] - m_0 - m_1*dist[jp][i_d] + β*V[>])   :: [id=optimality]
}
"""


# the two calibrations of the location stage: J = 2 and J = 3, the distance
# tables symmetric with zero diagonal, the payoffs δ(j) = j
LOCATION_CALIBRATION_J2 = {
    "J": 2,
    "β": 0.9,
    "m_0": 0.5,
    "m_1": 2.0,
    "δ": [1.0, 2.0],
    "dist": [[0.0, 1.5], [1.5, 0.0]],
}


LOCATION_CALIBRATION_J3 = {
    "J": 3,
    "β": 0.9,
    "m_0": 0.5,
    "m_1": 2.0,
    "δ": [1.0, 2.0, 3.0],
    "dist": [[0.0, 1.5, 4.0], [1.5, 0.0, 2.5], [4.0, 2.5, 0.0]],
}


# A stage whose state takes one of two integer values, 0 and θ, with the
# integer condition retained until θ is valued; wealth is the real entry of q:
#     w = q(s),   s ∈ S_θ = {0, θ}.
POINTS_TEXT = """@stage: points
θ   : ℝ₊
S_θ := {0, θ} ⊂ ℤ
β   : (0,1)
q   : S_θ → ℝ₊
Γ(x : ℝ₊) := [0, x]

[id=arvl_to_dcsn, (s : S_θ) : !arvl -> (w : ℝ₊) : !dcsn] {
    w = q[s]    :: [id=wealth]
}

[id=dcsn_to_cntn, (w, c : !ctrl @ ℝ₊) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = w - c    :: [id=saving]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = c + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = V
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : !ctrl) : !dcsn] {
    c = argmax_{cp : Γ(w)}(cp + β*V[>])   :: [id=optimality]
}
"""


# the points stage whose two members, θ + 1 and θ, are adjacent integers,
# which at θ = 2**53 are equal as doubles
ADJACENT_MEMBERS_TEXT = POINTS_TEXT.replace("{0, θ} ⊂ ℤ", "{θ + 1, θ} ⊂ ℤ")


# the calibration of ADJACENT_MEMBERS at θ = 2**53, by a mapping from the two
# keys to their entries
ADJACENT_CALIBRATION = {"θ": 2**53, "β": 0.9, "q": {2**53 + 1: 20.75, 2**53: 10.25}}


# A stage with a finite chain on I_J and one indexed normal shock: the next
# state e_n is drawn from the row of Π at the current state e_c, and the
# vector ε of J + 1 correlated components is drawn jointly; the decision
# state reads the component of ε at the drawn state.
CHAIN_TEXT = """@stage: chain
J   : ℕ
I_J := {0, …, J}
β   : (0,1)
Π   : I_J × I_J → [0, 1]
μ_ε : I_J → ℝ
Σ_ε : I_J × I_J → ℝ
e_n : I_J
e_n ~ Categorical(Π[e_c])
ε   : I_J → ℝ
ε   ~ N(μ_ε, Σ_ε)

[id=arvl_to_dcsn, (e_c : I_J, e_n, ε) : !arvl -> (x : ℝ, e_d : I_J) : !dcsn] {
    x   = ε[e_n]    :: [id=draw]
    e_d = e_n       :: [id=state]
}

[id=dcsn_to_cntn, (x, e_d) : !dcsn -> (x_n : ℝ, e_nxt : I_J) : !cntn] {
    x_n   = x      :: [id=carry]
    e_nxt = e_d    :: [id=state]
}

[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = x + β*V[>]    :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{e_n, ε}(V)    :: [id=value]
}
"""


# the calibration of the chain at J = 2 (three states), with a stochastic
# matrix and a correlated covariance
CHAIN_CALIBRATION_J2_WITH_JOINT_NORMAL_LAW = {
    "J": 2,
    "β": 0.9,
    "Π": [[0.8, 0.1, 0.1], [0.2, 0.6, 0.2], [0.1, 0.1, 0.8]],
    "μ_ε": [0.0, 1.0, 2.0],
    "Σ_ε": [[1.0, 0.5, 0.0], [0.5, 2.0, 0.5], [0.0, 0.5, 3.0]],
}


def points_calibration(theta, entries=(10.25, 20.75)):
    """A calibration of a points stage: θ, β = 0.9 and the two entries of q,
    in the order of the members."""
    return {"θ": theta, "β": 0.9, "q": list(entries)}


# the identities of the declarations of ψ in the buffer-stock stage and of y
# in the two-node stage
PSI_IDENTITY = "buffer_stock:distribution:ψ"
Y_IDENTITY = "two_nodes:distribution:y"


# the line of the buffer-stock stage file that declares the law of ψ
LOGNORMAL_PSI_LINE = "ψ ~ LogNormal(-(σ_ψ^2)/2, σ_ψ)"


# the law of ψ in the tests of the buffer-stock stage: the log-mean
# -(σ_ψ^2)/2 of the file, at which ψ has the mean one, the file's σ_ψ, and
# the truncation interval [0.5, 2]
TRUNCATED_PSI_LAW = "TruncatedLogNormal(-(σ_ψ^2)/2, σ_ψ, 0.5, 2)"


def text_with_psi_law(text, law, *changes):
    """The buffer-stock stage text `text` with the law of ψ replaced by `law`
    and each further pair (as written, as changed) of `changes` applied."""
    return changed(text, (LOGNORMAL_PSI_LINE, f"ψ ~ {law}"), *changes)


# the parameters of the two-node stage, bound in every calibration of it
TWO_NODES_CALIBRATION = {"β": 0.96, "R": 1.03}


def two_nodes_text_with_law_of_y(law, parameters=""):
    """The two-node stage text with `y ~ law`, the declarations `parameters`
    written before it."""
    return two_nodes_text_with_changes(declarations=f"{parameters}y ~ {law}\nz : ℝ\nz ~ N(0,1)\n")


# the two-node stage with `y ~ Uniform(a_y, b_y)`, a_y and b_y parameters
UNIFORM_ENDPOINTS_TEXT = two_nodes_text_with_law_of_y("Uniform(a_y, b_y)", "a_y : ℝ\nb_y : ℝ\n")


# the calibration of the chain stage at J = 1, without the parameters of the
# joint normal law
CHAIN_CALIBRATION_J1 = {"J": 1, "β": 0.9, "Π": [[0.9, 0.1], [0.2, 0.8]]}


def chain_text_with_law_of_epsilon(law, parent=False, value="E_{e_n, ε}(V)"):
    """The chain stage text `CHAIN_TEXT` with `ε ~ law` in place of the joint
    normal law and without its two parameters; with `parent`, the scalar
    shock η ~ N(0, 1) declared before ε; and with the arrival value
    `V[<] = value`."""
    shock = "η   : ℝ\nη   ~ N(0, 1)\n" if parent else ""
    return changed(
        CHAIN_TEXT,
        ("μ_ε : I_J → ℝ\nΣ_ε : I_J × I_J → ℝ\n", ""),
        ("ε   : I_J → ℝ\nε   ~ N(μ_ε, Σ_ε)", f"{shock}ε   : I_J → ℝ\nε   ~ {law}"),
        ("E_{e_n, ε}(V)", value),
    )


# the chain stage whose shock ε has the parent η, with the expectation over η
# outside the one over ε
PARENT_CHAIN_TEXT = chain_text_with_law_of_epsilon(
    "TypeIExtremeValue(η, 1)", parent=True, value="E_{η}(E_{e_n, ε}(V))"
)
