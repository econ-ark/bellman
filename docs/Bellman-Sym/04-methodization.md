---
audience: user
type: user-guide
---
# Methodization

#specification #spec_factory

> [!summary]
> **Methodization** attaches numerical methods to the operators of a stage. The methods are written in the stage's **methods file**, a `.bl` file beside the stage file, whose blocks name the stage's blocks by their ids and add to them. Its entries give an operator a method and a grid, `policy.method : !egm`, and name the handler, the routine that carries the method out; the settings a method reads are declared in the same file with their sets and valued in a settings file. Typing a method adds no equation to the model: where a solution method brings lines of its own, the stage computes with them in place of the stage file's maximization and keeps the maximization as its statement of the choice.

> [!info]- Relationship with other documents
> **Builds on** — [Stages](01-stage.md) and [Field equations](03-field-equations.md): the blocks, their ids and the derivative term that the entries and lines of a methods file refer to.
> **Formal account** — [Methods](../bellman-calculus/06-Methods.md): the method and the grid as components of an operator's signature, the grid as a discretized domain, the two erasures and the two levels; [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10 and §4.6: the reading of a solution method's lines.
> **Used by** — [Trellises](07-trellis.md) and [The Bellman factory](08-bellman-factory.md): the methods files a recipe names for each use of a stage; [Methods and places](API/stage/07-methods.md) and [Parameters and settings](API/stage/06-par-and-settings.md): what the stage object answers about its methods and its settings.
> **See also** — [Method types](reference/methods.md): every method word with the keyword arguments the package reads; the wiki entries [methods](../wiki/methods.md), [grid](../wiki/grid.md), [addition](../wiki/addition.md), [settings](../wiki/settings.md) and [handler](../wiki/handler.md).

> [!note]- Key terminology
> | Term | Meaning |
> |---|---|
> | **Operator** | One computation of a stage: a [builder](../wiki/builder.md), the operator a block denotes; an operation inside it, such as an expectation or a maximization; or the [Evaluation](reference/operations.md#evaluation) that stores a builder's result. |
> | **Place and path** | A place is an operator that a methods file can name; its path is the name the file writes for it, such as `policy`, `dcsn_to_arvl.E_ψ_ξ` or `policy.evaluate` (§2). |
> | **Typing entry** | A line `<path>.method : …`, `<path>.grid : …` or `<path>.handler : …` that gives the operator at a path its method, its grid or its handler (§3). |
> | **Method** | The numerical procedure chosen for one operator, named by a word and, where it takes options, the named options in parentheses, its keyword arguments: `!egm`, `!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)` ([wiki](../wiki/methods.md)). |
> | **Grid** | The finite set of points at which a function is computed and stored, written by one of three constructors: `!Cartesian(a=(a_min, a_max, n_a))`, one factor per coordinate; `!Points(nodes=P)`, a finite set of declared points; or `!Fibred(base=…, fibre=…)`, the feasible controls at each state of a base grid (§3.2; [wiki](../wiki/grid.md)). |
> | **Handler** | The routine outside the language that carries a method out, named by a quoted string, `"cons-port:egm"` ([wiki](../wiki/handler.md)). |
> | **Representation** | A method that stores a function from the data its place supplies and gives the function's values between those data: `!Linear`, piecewise linear interpolation; `!pchip`, piecewise cubic interpolation that keeps the monotonicity of the stored values; or `!closed_form`, the function's authored expression (§3.4). |
> | **Data source** | The data a representation is built from, decided by its place: an authored table, the policy pairs that the endogenous grid method computes, a complete authored expression, or the values of the function at the points of the representation's own grid (§3.4). |
> | **Solution method** | A method typed at a builder that says how the builder's output is computed: `!egm`, the endogenous grid method, brings the lines by which the policy is computed; `!vfi`, value function iteration, brings none; and `!explicit` reads the lines of its block, which define each output by an expression (§3.5). |
> | **Setting** | A value a method reads, such as a grid's bounds and count or a node count, declared in the methods file with its set and valued in the settings file ([wiki](../wiki/settings.md)). |
> | **Addition** | A methods file, so called because the package forms the union of its items with the stage file's items and removes nothing ([wiki](../wiki/addition.md)). |
> | **Declared level, operative level** | The builders as the stage file states them, which `stage.declared` holds, and the builders the stage computes with, which `stage.builder` holds and in which a solution method's lines stand in place of the stage file's lines (§5). |
> | **Derivative term, derivative line** | `D_{a}V[>]`, the derivative of a value in a state coordinate of its [perch](../wiki/perch.md), read where a line needs it; and a line whose left side is such a term, which states that derivative ([Field equations](03-field-equations.md) §2). |

## 1 A methods file beside its stage file

The buffer-stock stage, `applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl`, states the model and nothing about its computation. The household arrives with assets `k`. The permanent and transitory income shocks `ψ` and `ξ` then give its resources, `m = R*k/(Γ*ψ) + ξ`, from which it chooses consumption `c` and saves `a = m - c`; `Γ` is the growth factor of permanent income, and `Γ_c(m)` the set of feasible consumption levels. Its two value blocks and its policy block are:

```bl
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]               :: [id=value]
}

[id=dcsn_to_arvl, (V) : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{ψ,ξ}((Γ*ψ)^(1-ρ) * V)     :: [id=value]
}

[id=policy, (V[>] : ℝ @ !vlu) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])     :: [id=optimality]
}
```

Each block opens with a bracket that holds its id and its signature: the fields the block reads, an arrow and the fields it writes, each side followed by its perch, with `@ !vlu` marking a value and `@ !ctrl` a control ([Stages](01-stage.md) §3). The mark after a field names its [perch](../wiki/perch.md): `V[>]` is the value at the continuation perch, after the choice; `V` the value at the decision perch; and `V[<]` the value at the arrival perch, before the shocks are drawn. The policy block states the choice as a maximization over `Γ_c(m)`, and the stage file writes no derivative, no grid and no method.

The methods file, `methods.bl` in the same folder, chooses how the stage is computed: the endogenous grid method for the policy, on a grid of savings; linear interpolation of the consumption function and of the arrival value; Gauss–Hermite quadrature for the expectation over the two shocks; and the two derivative lines that the endogenous grid method reads. With its comment lines left out, each a line that begins with `#`, the file is:

```bl
@methods: buffer_stock

n_a : ℕ              :: ["number of points of the savings grid"]
a_min : Xa           :: ["lower bound of the savings grid"]
a_max : Xa           :: ["upper bound of the savings grid"]
n_k : ℕ              :: ["number of points of the asset grid"]
k_min : Xa           :: ["lower bound of the asset grid"]
k_max : Xa           :: ["upper bound of the asset grid"]
n_ψ_nodes : ℕ        :: ["quadrature nodes of the permanent shock"]
n_ξ_nodes : ℕ        :: ["quadrature nodes of the transitory shock"]

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | evaluate.method : !Linear] {
    c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])       :: [id=InvEuler]
    m[>] = a + c[>]                 :: [id=g_cntn_to_dcsn]
    c[~] = c[>]                     :: [id=cons_choice]
}

[id=cntn_to_dcsn] {
    D_{m}V = 𝑑𝑢(c)                                  :: [id=marginal]
}

[id=dcsn_to_arvl
    | E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
    | evaluate.method : !Linear
    | evaluate.grid : !Cartesian(k=(k_min, k_max, n_k))] {
    D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)    :: [id=marginal]
}
```

The file is read as follows.

- `@methods: buffer_stock` names the stage the file adds to, by the name the stage file declares after `@stage:`; a file that names another stage is refused (`metadata-mismatch`).
- The eight declarations are the **settings** the file reads, each with its set and a description, in the form in which a stage file declares a parameter (§4). A count is a natural number, `n_a : ℕ`, and a bound of a grid is a point of the set the stage declares for the coordinate, `a_min : Xa`.
- The block `[id=policy, …]` names the stage's policy block by its id and adds to it. Its bracket holds the id and three **typing entries**: the first follows the id after a comma, and each of the other two stands in a group of its own, opened by `|`. `policy.method : !egm` gives the policy builder the endogenous grid method, and `policy.grid : !Cartesian(a=(a_min, a_max, n_a))` the grid of savings on which the method computes, one factor keyed by the coordinate `a`, with its bounds and its count written as the names of settings. `evaluate.method : !Linear`, whose path is read relative to the block, types piecewise linear interpolation at the Evaluation that stores the consumption function; it interpolates the pairs of resources and consumption that the method computes, and so the block writes no grid for it (§3.4). The three lines of the block are the lines of the method: the consumption chosen at each saving, from the inverted Euler equation, `c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])`; the resources at which that consumption is chosen, `m[>] = a + c[>]`, which is the law of motion `a = m - c` solved for `m`; and the identification `c[~] = c[>]`, which states that the policy at those resources is the candidate. `c[~]` is the field `c` with its decision mark written out, the same term as `c`, and the consumption stage of §2 writes the same line as `c = c[>]`. The stage computes with these three lines in place of the maximization, and it keeps the maximization as the policy builder it declares (§5).
- The block `[id=cntn_to_dcsn]` adds one line to the decision value block, the envelope condition `D_{m}V = 𝑑𝑢(c)`: the derivative of the decision value in resources, which the arrival block of the same stage reads inside its expectation.
- The block `[id=dcsn_to_arvl …]` writes its first entry in a group of its own, opened by `|` after the id, which is read as an entry after a comma is, and it adds three entries and one line to the arrival value block: Gauss–Hermite quadrature at the expectation `E_ψ_ξ`, with one node count for each shock; linear interpolation at the Evaluation that stores the arrival value and its derivative, on the grid of assets `k`; and the derivative line of the arrival value, whose factor `R*(Γ*ψ)^(-ρ)` inside the expectation comes from the law of motion `m = R*k/(Γ*ψ) + ξ` and from the normalization `(Γ*ψ)^(1-ρ)` of the value. The policy builder of the period before reads this derivative as `D_{a}V[>]`, through the trellis's connection of its savings `a` to the assets `k` ([Trellises](07-trellis.md) §2.1).
- The file types nothing at the decision builder's Evaluation, `cntn_to_dcsn.evaluate`. An Evaluation without an entry holds no method, and the package refuses nothing there; the envelope condition gives the derivative of the decision value at any resources through the consumption function, which `policy.evaluate` represents.

The package reads a methods file only when it is given the file's path. `load_stage(stage_path, [methods_path])` reads the stage file with the methods files its list names, `methodize(methods_path)` gives a stage already elaborated its methods file, or a list of them, as its whole selection, replacing any earlier one, by elaborating the stage anew from the stage file and the files together (§7; [The binding verbs](API/stage/09-binding-verbs.md)), and in a trellis the recipe names each stage's methods files (§6). `stage.methods` then lists each place at which a component is typed, with what is typed there, and the signature of a builder prints its method and its grid beside the functions it reads and writes:

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl",
                                   ["applications/buffer-stock/declaration/stages/buffer_stock/methods.bl"]))
print(stage.methods)
print()
print(stage.builder.policy.signature())
```

```text
dcsn_to_arvl.E_ψ_ξ      !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)
dcsn_to_arvl.evaluate   !Linear   !Cartesian(k=(k_min, k_max, n_k))
policy                  !egm   !Cartesian(a=(a_min, a_max, n_a))
policy.evaluate         !Linear

in         𝑉≻ : Xa → ℝ
out        𝑐(m) : 𝒫({c ∈ (Xm → ℝ₊₊) | c(m) ∈ Γ_c(m)})
method     !egm
grid       !Cartesian(a=(a_min, a_max, n_a))
```

The `out` line writes the policy builder's output as a set of feasible consumption functions, `𝒫(…)`, the set of the maximizing policies, since a maximization may have several ([A builder](API/stage/04-builder.md) §2). Configuration assigns the values of the settings file, `applications/buffer-stock/declaration/settings/buffer_stock.yml`, to the declared settings, and `stage.settings` then prints each setting with its set, its value, the place that reads it, the method there and, for a bound or a count of a grid, the grid's kind:

```python
stage.configure("applications/buffer-stock/declaration/settings/buffer_stock.yml")
print(stage.settings)
```

```text
name       set  value  read at                by              grid
n_a        ℕ    960    policy                 !egm            !Cartesian
a_min      Xa   0.001  policy                 !egm            !Cartesian
a_max      Xa   20.0   policy                 !egm            !Cartesian
n_k        ℕ    960    dcsn_to_arvl.evaluate  !Linear         !Cartesian
k_min      Xa   0.001  dcsn_to_arvl.evaluate  !Linear         !Cartesian
k_max      Xa   20.0   dcsn_to_arvl.evaluate  !Linear         !Cartesian
n_ψ_nodes  ℕ    7      dcsn_to_arvl.E_ψ_ξ     !gauss_hermite
n_ξ_nodes  ℕ    7      dcsn_to_arvl.E_ψ_ξ     !gauss_hermite
```

The package solves nothing. It records the methods, and a handler, a routine outside the language, carries each out (§3.3); the buffer-stock file names no handler, so the program that solves the model reads the words from `stage.methods` and supplies a routine for each. [The buffer-stock example](../examples/buffer-stock/buffer_stock.md) quotes the file with its comments and shows the same calls.

## 2 The places an entry names

Every entry of a methods file names an operator of the stage by its **path**, written before the component: `<path>.method`, `<path>.grid` or `<path>.handler`. `stage.places()` lists the places of a stage, each by its path in the column `address`, with its kind, and the kind decides which method words the package admits there ([Methods and places](API/stage/07-methods.md) §1):

| Path | Place | Kind |
|---|---|---|
| a block id, `policy` or `cntn_to_dcsn` | the builder the block denotes | `builder` |
| a block id and `evaluate`, `dcsn_to_arvl.evaluate` | the Evaluation that stores the builder's result, where a representation is typed: one entry for everything the Evaluation stores, or one entry for each stored object, `dcsn_to_arvl.evaluate[V[<]]` for the value and `dcsn_to_arvl.evaluate[D_{k}V[<]]` for the derivative a derivative line states; the policy builder's object is its policy, `policy.evaluate[c]` | `operator evaluate` |
| a block id and the name of an operator, `dcsn_to_arvl.E_ψ_ξ` | every occurrence of that operator in the block | `operator E` |
| a block id, a line id and the name of an operator, `dcsn_to_arvl.value.E_ψ_ξ` | one occurrence, in one line | `operator E` |
| the name of an operator alone, at file level, `E_ψ_ξ` | every occurrence of the operator in the stage | `operator E` |
| a block id and a line id, `cntn_to_dcsn.value` | a line with an id; a line marked `!node` is a computation whose result is stored as a function of its own, at its Evaluation, as `cntn_to_dcsn.risk_ce.evaluate` stores the certainty equivalent of the smooth-ambiguity stage | `statement`, or `node` for a line marked `!node` |
| the name of a function the stage file or a methods file defines, `𝑑𝑢𝑖𝑛𝑣` | a declared function, where a representation or the closed-form inverse is typed, `𝑑𝑢𝑖𝑛𝑣.method : !analytic_inverse` at file level | `definition` |

An expectation is named by `E_` followed by the shocks it integrates, joined by underscores in the order the stage file writes them, so that `E_{ψ,ξ}` is named `E_ψ_ξ`. Every other operator is named by its head: `argmax` for the maximization, `solve` for the implicit solution, `upper_env` for the upper envelope and `evaluate` for an Evaluation. [Expression forms](reference/forms.md) gives the forms of `E`, `argmax` and `solve`, and [Operations](reference/operations.md#evaluation) the Evaluation. The derivative operator `D` is listed with its occurrences and admits no method: a derivative is read from a derivative line the author writes or, where no line states it, from the representation of the value (§5).

Inside a block's bracket a path is read relative to the block: `method : !egm` and `policy.method : !egm` both type the block's own builder, and `evaluate.method : !Linear` the Evaluation inside it. At file level a path is written in full, `dcsn_to_arvl.evaluate.method : !Linear`, and the package attaches the entry to the block its first segment names; an entry whose first segment names no block, the name of an operator alone or a function, stays at file level. A block of a methods file holds entries in its bracket and lines in its body, and a block with an empty body is refused, so the entries of a block to which the file adds no line are written at file level, each with its full path. The consumption stage of the portfolio application writes both forms in one file, `applications/portfolio-choice/declaration/stages/cons/methods.bl`:

```bl
[id=policy, method : !egm | grid : !Cartesian(a=(a_min, a_max, n_a)) | handler : "cons-port:egm"] {
    c[>]   <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0    :: [id=InvEuler]
    m_d[>] = a + c[>]                        :: [id=grid]
    c      = c[>]                            :: [id=identification]
}

cntn_to_dcsn.evaluate.method : !Linear
cntn_to_dcsn.evaluate.grid : !Cartesian(m_d=(m_min, m_max, n_m))
cntn_to_dcsn.evaluate.handler : "cons-port:_make_interp"
arvl_to_dcsn.method : !deterministic
dcsn_to_cntn.handler : "cons-port:transition_fwd"
```

The candidate line of its block `policy` carries the borrowing constraint: consumption is at most the Euler candidate, the savings `a` are nonnegative, and the clause `⟂` states that one of the two inequalities holds with equality ([Constraints](10-constraints.md) §4.3). The five entries at file level type the decision builder's Evaluation, the forward builder from arrival to decision, and the handler of the forward builder from decision to continuation.

What a method does depends on the kind of its place.

- At a builder, a **solution method** says how the builder's output is computed. `!egm` brings the lines by which the policy is computed, as the block `policy` above shows, and `!vfi`, value function iteration, brings none and leaves the maximization of the stage file to its handler. `!explicit` reads the lines of its block, as `!egm` does, each of which defines an output by an expression, in place of the maximization (§3.5). A forward builder carries the distribution of households over the states of one perch to the next perch and takes a method that represents that distribution, `!deterministic` or `!histogram`. The kind `builder` does not tell a forward builder from a backward one, so the package admits every word of a builder at both, and the author chooses the word that suits the builder.
- At an Evaluation, a line or a declared function, a **representation**, `!Linear`, `!pchip` or `!closed_form`, stores the function there from the data the place supplies (§3.4).
- At an operator inside a line, a method says how that one operation is computed: a quadrature rule or a discretization of the shock's law at an expectation, a search at a maximization, a root finder at `solve`, an upper-envelope scan at `upper_env`.

The package refuses the following entries, and each refusal names the line of the methods file and its rule ([Refusals](reference/refusals.md)):

- a method word that no row of [Method types](reference/methods.md) holds (`syntax`);
- a path that names no place of the stage (`name-in-scope`);
- a word at a place of a kind its row does not admit, such as `cntn_to_dcsn.method : !Linear` (`method-admission`);
- a typing of the derivative operator, `D.method` (`no-method-for-derivative`);
- one component written twice with different content, in one file or in two (`declared-twice`), and one component typed at one place by two paths, such as the whole of an Evaluation and one of its objects, or the name of an operator and one of its occurrences, or a representation typed both at a `!node` line and at its Evaluation, which store one function (`component-typed-twice`).

## 3 The three entries

The method and the grid are components of the operator's signature, which the signature prints beside the functions the operator reads and writes, and the handler is a binding beside them. The three are written in the same way, `<path>.<component> : <value>`.

### 3.1 The method

A method is a word, with keyword arguments where it takes them: `!egm`, `!Linear`, `!gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)`, `!vfi(tol=tol_v, n_c=n_c)`. [Method types](reference/methods.md) lists every word with the kinds of place it admits and the keyword arguments the package reads, each with the set its value lies in and whether the word requires it: the quadrature takes one node count for each shock the expectation integrates, written `n_<shock>`, and value function iteration takes a tolerance and a number of candidate levels. A keyword argument the row does not list is admitted and kept for the handler, which reads it or refuses it. The value of a keyword argument is written as the name of a setting the file declares, as every argument of the buffer-stock file is, so that its number stands in the settings file: configuration requires a value for every name a keyword argument writes (`setting-unvalued`) and refuses a value outside the set the row names (`method-option-value`). A word the catalogue writes with a hyphen, `gauss-hermite`, is written in a methods file with an underscore, `!gauss_hermite`, and the package reads the two as one word.

### 3.2 The grid

The grid is the finite set of points at which the function at a place is computed and stored; between the points, the representation's interpolation supplies the values. It is written by its own entry at the place, `<path>.grid : …`, and where an Evaluation's stored objects are represented apart, by one entry for each, `dcsn_to_arvl.evaluate[D_{k}V[<]].grid : !Cartesian(k=(k_min, k_max, n_k))`. The entry holds one grid constructor, the word that says how the points are built:

| Constructor | Meaning |
|---|---|
| `!Cartesian(a=(a_min, a_max, n_a))` | the product of one set of points for each coordinate, each factor keyed by the coordinate's name as the stage file declares it; at least one factor is written |
| `!Points(nodes=P)` | the finite set of the declared points `P`, each point written in the domain's declared coordinate order; `!Points` alone is the empty grid |
| `!Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))` | each state of the base grid paired with `n_c` points of the control's feasible set `Γ_c` at that state: a grid of feasible pairs of states and controls |

A factor of `!Cartesian` takes one of four shapes, the first with an optional spacing word:

| Factor | Meaning |
|---|---|
| `a=(a_min, a_max, n_a)` | `n_a` evenly spaced points from `a_min` to `a_max`, the three names declared settings |
| `a=(a_min, a_max, n_a, !expmult)` | `n_a` points from `a_min` to `a_max`, spaced as the fourth element names: a spacing word, with keyword arguments where the spacing has a parameter, `!expmult(nest=grid_phi)`, each a declared setting; the handler that builds the grid reads the word |
| `m=M_nodes` | the points of a node set: a setting the methods file declares and the settings file values by the list of its points, or a set the stage defines by its members |
| `ν=E_ν` | the quadrature nodes of the expectation `E_ν`, for a coordinate represented on a shock |
| `c=(Γ_c, n_c)` | `n_c` points of the feasible set `Γ_c` of a control, for a method that searches over the control |

`!Cartesian` and `!Points` stand at every place whose method reads a grid: a representation, a solution method whose grid lies on the states of its output perch, such as `!vfi`, the endogenous grid method on the continuation states, and a place with no method word, whose handler reads the grid. The points of `!Points` are a set the stage defines by its finite members, `B := {1, 2}`, or a setting the methods file declares on a fixed finite product of points, `P : ℝ₊ × ℝ₊ × ℝ₊`, which the settings file values by the list of its points, `P: [1.0, 2.0, 3.0]`; on a domain of two coordinates each point is a pair, declared through a product set, `X2 := ℝ × ℝ` and `P : X2 × X2 × X2`. Repeated points collapse in the set, and an interpolation procedure may still require at least two points. `!Fibred` stands where the domain of the problem is the base's states followed by the fibre's controls: at a solution method that chooses over the controls on the states of its output perch, such as `!vfi`, and at a representation or a place with no method word only for a function of those states and those controls. It is refused at the continuation grid of `!egm`, which holds no control, and at a representation of a function of the states alone. Its base is `!Points` or a `!Cartesian` term without feasible factors, and its fibre a `!Cartesian` term of feasible factors. A feasible factor written in `!Cartesian` without `!Fibred`, as in `cntn_to_dcsn.grid : !Cartesian(c=(Γ, n_c))`, is admitted and states a family of grids of the control, one at each state, and no one grid of pairs.

Each constructor may end with `require=` and one predicate word, or a tuple of them, which the resulting grid must satisfy: `!Empty`, the grid holds no point; `!Cartesian`, the grid is nonempty and holds every combination of its projected coordinate values; `!NonCartesian`, the grid is nonempty and misses some combination of them; and `!UniformCartesian`, the grid is Cartesian on at least one real coordinate, with at least two distinct, equally spaced values in every coordinate. A requirement is a property of the grid and no further component, and the predicate `!Cartesian` is distinct from the constructor of the same name. An outer requirement of `!Fibred` concerns the joint grid of pairs, and one written inside its fibre, `fibre=!Cartesian(c=(Γ_c, n_c), require=!UniformCartesian)`, concerns the grid of the control at each state. An unknown word, and two words that contradict each other, are refused where they are written (`grid-requirement`). In `!Cartesian`, `require=` is read as a requirement only where its value is a predicate word or a tuple of them, so that a coordinate named `require` keeps its factor.

A factor that writes a number, or names a setting no methods file declares, is refused (`grid-setting-declared`), and so are declared points of `!Points` that are neither a declared setting nor a set the stage defines. So is a factor keyed by a name that is no coordinate of the function at the place, unless it is a feasible factor for a control or a quadrature factor for a shock, a constructor at a place it may not stand at, and a grid written at a place whose method reads no grid, such as a quadrature rule (`grid-coordinate`). A place without a grid entry, and a coordinate that no factor names, take the default: a grid of the kind `!Cartesian` over the state coordinates of the function the place holds, in declared order, with no number supplied and none required of the settings file, so that the handler supplies the numbers. For an Evaluation these are the states of the perch at which the stored function stands; for the endogenous grid method they are the states of the continuation perch, on which its grid of savings lies. The buffer-stock file writes no grid at `policy.evaluate`, and none is admitted there: `!Linear` at the closing Evaluation of an `!egm` builder reads the pairs of resources `m[>]` and consumption that the method computes at the savings on its grid, and a grid entry there is refused (`grid-coordinate`; §3.4). At configuration the package checks that each pair of bounds is in order and inside the coordinate's declared set, that each count is at least two, that each node set is strictly increasing, and that each declared point of `!Points` has one finite real coordinate for each coordinate of the domain, inside the coordinate's declared set where that is decided (`grid-bounds`); it decides each requirement that the bound values decide and refuses one that fails (`grid-requirement`). It checks nothing about accuracy. What a method does outside its grid, such as extrapolation, is a keyword argument of the method word and no part of the grid.

Once the settings are bound, the package constructs each grid at their values. A builder's `kernels().grids` holds, for each place within the builder that types a grid, the realized grid: its constructor, its coordinates in declared order and its finite points, with repeated points removed ([A builder](API/stage/04-builder.md) §5). Where the construction cannot establish the finite points and every required property, the entry is the refusal that says why, under `grid-requirement`, and no default is supplied: a coordinate that no factor names, a feasible factor written without `!Fibred`, which states a family of grids and no one grid, a feasible interval that is open or unbounded, and a fibre of several controls, whose joint sampling is not supported. At each state of a fibred grid the package places the declared count of evenly spaced points on the closed feasible interval, both endpoints included: with `B := {1, 2}`, `Γ_c(m) := [0, m]` and `n_c = 2`, the fibred grid of the table above, typed at a `!vfi` builder, is the four pairs (1, 0), (1, 1), (2, 0) and (2, 2). It is `!NonCartesian`, since it misses the combination (1, 2) of its projected values. The arrival builder of the buffer-stock stage, configured in §1, holds the realized grid of assets:

```python
for address, grid in stage.builder["dcsn", "arvl"].kernels().grids.items():
    print(address, grid)
```

```text
dcsn_to_arvl.evaluate !Cartesian on (k), 960 points: (0.001,), (0.021854014598540146,), (0.04270802919708029,), …, (20,)
```

### 3.3 The handler

A handler is the routine that carries a method out. Its entry names it by a quoted string of the form `<package>:<function>`, in the bracket, `handler : "cons-port:egm"`, or at file level, `dcsn_to_cntn.handler : "cons-port:transition_fwd"`. `"cons-port:egm"` is the function `egm` of the numerical code of the cons-port application, and `"asva:make_egm_1d"` a function of asva, the numerical toolkit installed beside the package ([Asva](../asva/index.md) §3). The package records the name and neither imports nor calls the function. A handler builds its numerical operator from three things: the record of the builder's kernels, which `kernels()` answers, for each operation of the builder its rule as a function with the wires it reads and writes ([A builder](API/stage/04-builder.md) §5); the grid at the place, whose realized points `kernels().grids` holds (§3.2); and the keyword arguments of the method word that the package does not read. A handler may be written with or without a method word; written alone, as for the forward builder `dcsn_to_cntn` above, it names the routine, and `stage.methods` prints it as the place's handler. Where a file names no handler, as the buffer-stock file names none, the word alone is typed, and the program that solves the model reads it from `stage.methods` and supplies the routine.

### 3.4 Representations and the data they read

A representation family is the numerical form of a stored function. The package registers three, none of which takes a keyword argument that the package reads ([Method types](reference/methods.md)):

- `!Linear`, continuous piecewise linear interpolation through strictly increasing nodes and the values aligned with them, which evaluates a first derivative that is constant between the nodes;
- `!pchip`, piecewise cubic Hermite interpolation with the shape-preserving slopes of PCHIP, which evaluates a first derivative that is continuous across the nodes and a second derivative between them;
- `!closed_form`, the function's complete authored expression, evaluated through the compiled kernel of that expression, which offers no derivative of its own, since nothing is differentiated automatically.

A family that a program registers through `register` of `bellman.stage.representations` is admitted at the same places and listed in the catalogue, and a stage already bound keeps the description of each family as it stood at binding.

A representation reads one of four data sources. The package decides the source from the place, in the following order, and `stage.methods[<place>].source` names it ([Methods](../bellman-calculus/06-Methods.md) §5):

1. `table`, an authored table: at the occurrence of an authored `evaluate(knots, values, x)` in a line, and at a `!node` line that defines its name by such a table alone, the representation reads the knots and the values the line supplies. No grid is required. An optional grid there discretizes the table's coordinate and has exactly the table's knots, compared exactly, with no sorting, resampling or tolerance, at configuration where both are known and otherwise before numerical preparation, where the obligation `table-grid-support` records it.
2. `pairs`, the selected policy pairs: at the closing Evaluation of a builder methodized with `!egm`, and at each object it stores, a family that accepts pairs reads the pairs of decision states and controls that the method computes, and a grid entry there is refused (`grid-coordinate`).
3. `expression`, a complete authored expression: at the Evaluation of an `!explicit` builder (§3.5), and at a line, a `!node` line or a declared function whose defining expression is complete, a family that accepts an expression reads it, and `!closed_form` refuses a grid entry (`grid-coordinate`).
4. `own nodes`, the family's own nodes: otherwise the family samples the function at the points of its own grid, the grid entry of the place or, where none is written, the default of §3.2.

`!Linear` and `!pchip` accept the table, the pairs and their own nodes, and `!closed_form` accepts the expression alone. A family that does not accept the data its place supplies is refused, and data that are missing or fail their check never select another source (`representation-source`): `!closed_form` is refused at an authored table and at a place that supplies no complete expression, and a family that accepts neither the pairs nor its own nodes is refused at the closing Evaluation of an `!egm` builder. Two cases read the place's data through the family's own nodes. A family that accepts its own nodes and not the pairs keeps its grid at that Evaluation and is sampled there from the pairs, a reconstruction that `stage.obligations()` lists as `pair-reconstruction`; and `!Linear` or `!pchip` typed where the place supplies an expression, such as the Evaluation of an `!explicit` builder, samples the expressed function on its own grid. Since `methodize` replaces the whole selection, a selection without `!egm` makes the same entry read its own nodes. Every representation also owes `evaluation-domain`: an expression is evaluated only where it is defined with its stated conditions, and an interpolant inside the interval of its nodes or through an identified extension. The package lists these obligations with their status and does not check `evaluation-domain` or `pair-reconstruction`.

### 3.5 Explicit solutions

Where the solution of a policy builder or a backward value builder is known in closed form, the methods file types `!explicit` at the builder and writes, in a block with the builder's id, one line `output = expression` for each output of the builder. In a perfect-foresight consumption stage whose stage file defines human wealth by the derived parameter `h := 1/(1 - Γ/R)` (§4), the methods file states the consumption function:

```bl
@methods: perfect_foresight

[id=policy, policy.method : !explicit] {
    c = (1 - (R*β)^(1/ρ)/R)*(m - 1 + h)    :: [id=consumption]
}
```

The line stands in place of the maximization at the operative level, as the lines of every solution method do, and `stage.declared` keeps the maximization as the statement of the choice (§5), as it keeps the value lines of a value builder that `!explicit` solves; the module `code/closed_form_check.py` of `applications/consumption-perfect-foresight-crra/` checks the closed form against these declared builders, reading the Bellman equation from the declared level. The line's compiled kernel evaluates the expression, which establishes an evaluator and no optimality. An expression may read the states and the controls of the builder's output perch, the parameters, the derived parameters and the names that earlier lines of the block define. The package refuses, under `explicit-solution`, `!explicit` at a forward builder, a line that reads a value input of the builder or its derivative, such as `V[>]` or `D_{a}V[>]`, a line that states a relation, a line that applies `argmax`, `solve` or `upper_env`, and a line that defines or reads a field at another perch, such as the candidate `c[>]` of the endogenous grid method; an output that no line defines is refused under `output-defined`. A block of this complete formula-only form typed with `!egm` or `!time_iteration` is refused by a refusal that names `!explicit` (`explicit-solution`).

The Evaluation of an `!explicit` builder at which no entry names a representation takes `!closed_form`, generated from the `!explicit` entry and not written in any file. `stage.methods` prints it as `policy.evaluate   !closed_form   generated from policy.method`, and the signature of the Evaluation, `stage.builder.policy.primitives["policy:Evaluation"].signature()`, as `method     !closed_form  generated from policy.method`, so that a generated selection is told apart from an authored one. An authored representation at the Evaluation, such as `!Linear` with a grid, replaces the generated one and samples the expression on its own nodes, and a selection without `!explicit` generates nothing.

## 4 Settings declared with their sets

A setting is a value a method reads: a bound or a count of a grid, the points of `!Points`, a node count, a tolerance, or a choice among finitely many words. A methods file declares each setting it reads at file level, in the form in which a stage file declares a parameter, with its set and a description:

```bl
n_a : ℕ              :: ["number of points of the savings grid"]
a_min : Xa           :: ["lower bound of the savings grid"]
```

A count is in `ℕ`, a tolerance in `ℝ₊₊`, and a bound of a grid in the set the stage declares for its coordinate, `Xa` for the savings and the assets of the buffer-stock stage, or in a literal set such as `ℝ₊`. A setting chosen among finitely many words is declared on the set of those words, as the tenure stage of the durables application declares the branch chosen where keeping and adjusting are worth the same, `tie_break : {keep, adjust}`. A grid factor names its bounds and its count as declared settings, and a keyword argument names a declared setting, so that every number stands in the settings file. A setting that a grid factor names without a declaration is refused (§3.2), a name declared twice in one file is refused (`declared-once`), and a name that two files declare differently is refused (`declared-twice`).

The values stand in the settings file, a YAML mapping under the key `settings`, which `configure` binds as `calibrate` binds the values of the parameters ([The binding verbs](API/stage/09-binding-verbs.md) §3). The settings file of the buffer-stock stage values the eight settings its methods file declares:

```yaml
settings:
  n_ψ_nodes: 7
  n_ξ_nodes: 7
  n_a: 960
  a_min: 0.001
  a_max: 20.0
  n_k: 960
  k_min: 0.001
  k_max: 20.0
```

`configure` refuses a value outside the declared set, naming the line of the methods file that declares the setting (`setting-outside-set`), and a declared setting the file does not value (`setting-unvalued`). One settings file may serve every stage of a model, so a key that no declaration of the stage names is not refused: `stage.settings` lists it with its value and with no set and no place, which is where a misspelled key shows. When two stages of one period declare one name in their methods files, the name is one setting of the period, with one value, as a parameter declared in two stages is one parameter (`period-parameter-agreement`). `stage.settings` lists every setting with its set, its value and the places that read it, and `stage.settings["n_a"]` answers one setting's record ([Parameters and settings](API/stage/06-par-and-settings.md) §2). A parameter, such as the risk aversion `ρ`, is declared in the stage file and defines the model; a setting is declared in the methods file and configures a method; and a finite set of alternatives the household chooses among belongs to the model and is declared in the stage file. A derived parameter is a constant written by `:=` from the declared parameters, such as human wealth `h := 1/(1 - Γ/R)` in a stage file or the marginal propensity to consume `κ := 1 - (R*β)^(1/ρ)/R` in a methods file: it is a parameter of the model and not a setting, its value is computed at calibration, and one that a methods file defines leaves the stage when its file leaves the selection ([Parameters and settings](API/stage/06-par-and-settings.md) §1.1).

## 5 The two levels

The lines a methods file adds to a block are read at two levels. At the **declared level**, `stage.declared`, the stage keeps the builders as the stage file states them: the policy builder of the buffer-stock stage holds the maximization. At the **operative level**, `stage.builder`, a builder whose method brings lines, such as `!egm`, holds those lines in place of the stage file's lines, and these are the builders the stage computes with. The card of the buffer-stock policy builder, the printed summary that `stage.builder.policy.denote()` answers, shows the maximization under `Declared` and the three lines of the method under `Operations`, with the source lines of both files ([Methods and places](API/stage/07-methods.md) §3). The stage records the condition under which the method's lines give the policy that the maximization defines, and `stage.obligations()` lists it under the name that the method's row of [Method types](reference/methods.md) gives it, `egm-eligibility` for the endogenous grid method: the continuation value is concave and continuously differentiable on (0, ∞) with a finite positive right derivative at 0. The package does not check it.

A derivative line written in the stage file stands at both levels. A derivative line the methods file adds stands in the operative builder alone, recorded at its Evaluation, since `stage.declared` holds the stage file's lines alone: the envelope condition that `cntn_to_dcsn` gains from the buffer-stock methods file stands on the card of `stage.builder["cntn", "dcsn"]` and not on the card of `stage.declared["cntn", "dcsn"]`. It is recorded as a stated derivative of the value, under the obligation `marginal-reading`, the author's assertion that the right side is the derivative, which the envelope conditions justify and the package does not check. A solution method that brings no lines, such as `!vfi`, leaves the declared lines in place. A line added to a block whose method component holds no solution method is read in the operative builder as a line of the block, so a second definition of a field there is refused (`defined-once`).

How the derivative of a value is read is fixed by the stage that writes the value: by a derivative line, whose values the representation at the builder's Evaluation stores beside the value's, or, where no line states it, by the representation of the value itself, where the method's row says which derivatives it evaluates. A stage that reads the value as its continuation value, and its derivative as `D_{a}V[>]`, receives the derivative so fixed and declares nothing about it ([Trellises](07-trellis.md) §2.1). Where the law of motion between two perches is the identity, the derivative passes through and no line is written; where it is not, the author writes the arrival derivative line with the law's factor, as the buffer-stock file writes `D_{k}V[<] = E_{ψ,ξ}(R * (Γ*ψ)^(-ρ) * D_{m}V)`. The package computes a derivative only where a line states it or a representation evaluates it.

## 6 Several methods files and the recipe

A stage file is used at several occurrences of a trellis, one for each period in which the trellis places it, and each occurrence takes the methods files its recipe names. The recipe, `spec.yml`, names the files a model is read from: for each stage its stage file and, for each kind of binding, a list of files ([The Bellman factory](08-bellman-factory.md) §3). A stage's methods list names its methods file for every occurrence, `methods: {all: [stages/cons/methods.bl]}`. The files of a list are unioned with the stage file in the order the list writes them, and the whole list is the occurrence's selection of methods. To compute some occurrences by another method, write a second methods file beside the first, `methods.<variant>.bl`, and name it in place of the first for those occurrences: this is a **replacing selection**. The cons-port application names `stages/cons/methods.bl`, the endogenous grid method on the policy builder, in its two recipes, and its trellis file `trellis.port-cons-vfi.yml` names `stages/cons/methods.vfi.bl`, value function iteration on the decision value builder, in its place ([Trellises](07-trellis.md) §3). A file named after another in one list adds its entries and lines to that file's.

The package forms the union of a stage file with its methods files by the following rules, none of which depends on the method words written:

1. A block of a methods file merges with the stage's block of the same id: its entries join the block's bracket, and its lines follow the block's lines. A line id names one line of its block, so that two blocks may each hold a line `marginal`, and a line id that both files write in one block is refused (`declared-twice`).
2. The nested blocks of a [branching](05-branching.md) stage merge by their labels under their parent block, and a label the parent lacks is refused (`label-not-in-parent`), so that no branch is added.
3. A block whose id the stage lacks is kept as a new block of the stage, and it is then constructed as a block of the stage file is, with its full signature.
4. A declaration, definition or law at file level is appended. A name written in both files is one item where the two are equal and is refused where they differ (`declared-twice`), and so is an entry written in both files.
5. A coordinate that a methods file writes in a block's signature is the stage's coordinate of the same name, with the stage's set kept; a differing set is refused (`type-conflict`).

The stage file unioned with no methods file is the stage file, and removing every item the methods files brought returns it: the stage file alone states the model ([Methods](../bellman-calculus/06-Methods.md) §8).

## 7 Loading and binding

A stage is specified by three bindings, each a verb of the stage object that adds its binding to the stage it is called on and returns that stage ([The binding verbs](API/stage/09-binding-verbs.md)):

| Verb | Source | What it binds |
|---|---|---|
| `calibrate` | a calibration file, YAML under the key `calibration`, or a mapping | a value for every parameter the stage file declares |
| `methodize` | the path of a methods file, or a list of paths applied in order | the methods, grids and handlers the files type, and the lines they add; a later call replaces the earlier selection |
| `configure` | a settings file, YAML under the key `settings`, or a mapping | a value for every setting the methods files declare |

```python
from bellman.stage import elaborate_stage, load_stage

stage = elaborate_stage(load_stage("applications/buffer-stock/declaration/stages/buffer_stock/buffer_stock.bl"))
specified = (stage.calibrate({"β": 0.96, "ρ": 2.0, "R": 1.03, "Γ": 1.02, "σ_ψ": 0.1, "σ_ξ": 0.1, "p_zero": 0.005})
             .methodize("applications/buffer-stock/declaration/stages/buffer_stock/methods.bl")
             .configure("applications/buffer-stock/declaration/settings/buffer_stock.yml"))
print(repr(specified))
```

```text
ElaboratedStage('buffer_stock', specified)
```

The recommended order is calibration, methodization and configuration: the parameter values complete the economic problem before the numerical choices are made, and the settings are then checked against the declarations and the methods that read them. `methodize` elaborates the stage anew from the stage file and its methods files together. The lines of a solution method and the derivative lines a methods file adds enter the operative level alone, a derivative line as a stated derivative of a value at its builder's Evaluation; `stage.declared` holds the stage file's lines alone, and no line of the stage file is changed or removed. `elaborate_stage(load_stage(stage_path, [methods_path]))` constructs the methodized stage from the two files at once, as §1 does. In a trellis, `assemble_trellis` applies the same bindings at every occurrence from the files the recipe names ([The Bellman factory](08-bellman-factory.md) §4).

Each binding is checked when it is made. Methodization refuses what §2 and §3 name: an unknown method word, a path that names no place, a word at a place of a kind it does not admit, a component typed twice, a grid factor that writes a number, names an undeclared setting or names no coordinate, a grid constructor at a place it may not stand at, an unknown or contradictory requirement, a representation whose family does not accept the data its place supplies and an `!explicit` block that breaks the rules of §3.5. Configuration refuses a value outside a declared set, a declared setting without a value, a name of a keyword argument without a value, a keyword argument's value outside the set its row names, a grid whose bounds, counts, nodes or points are out of order or outside their sets, a requirement that the bound values show to fail, and an optional grid beside an authored table whose points differ from the table's knots. Calibration refuses a missing parameter and binds no name the stage file does not declare. It refuses a value supplied for a derived parameter, whose value its definition gives, and a calibration at which a derived parameter has no finite real value, both under `derived-parameter` ([Parameters and settings](API/stage/06-par-and-settings.md) §1.1). Each refusal names the line of the file and the rule ([Refusals](reference/refusals.md)).

Four queries inspect the result and run nothing: `method_types["!egm"]`, the card of a method word in the catalogue, with the kinds of place it admits, the keyword arguments the package reads and the perch its grid lies on; `stage.places()`, the places of a stage with their kinds; `stage.methods`, each place with the word, the grid and the handler typed at it; and `stage.settings`, each setting with its set, its value and the places that read it ([Methods and places](API/stage/07-methods.md); [Parameters and settings](API/stage/06-par-and-settings.md)).

```python
from bellman.stage import method_types

print(method_types["!gauss_hermite"])
```

```text
METHOD !gauss-hermite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Admits
  operator E

Keywords
  n_<shock>, positive integer (required)

Grid
  none
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 8 Writing a methods file for your model

An economist who has written a stage file writes its methods file in these steps.

1. Save the file as `methods.bl` beside the stage file and open it with `@methods:` and the name the stage file declares ([Model directory layout](reference/model-directory-layout.md)). Name it in the list that `load_stage` takes, or in the stage's methods list in the recipe, since the package reads no methods file it is not given.
2. Declare at file level every setting the file reads, with its set: a count in `ℕ`, a bound in the set the stage declares for the coordinate, a tolerance in `ℝ₊₊`. Value each in the settings file, under the key `settings`.
3. Define at file level any function the method's lines call that the stage file does not define, such as the inverse of marginal utility, `𝑑𝑢𝑖𝑛𝑣(x : ℝ₊₊) := x^(-1/ρ)`, which the consumption stage of §2 defines in its methods file, and any derived parameter they read, such as `κ := 1 - (R*β)^(1/ρ)/R` (§4).
4. For the endogenous grid method, write a block with the id of the stage's policy block. In its bracket write `method : !egm` and the grid of savings on the continuation states, `grid : !Cartesian(a=(a_min, a_max, n_a))`. In its body write three lines: the candidate control at each saving, from the first-order condition inverted, with the discount factor where the stage file writes one, `c[>] = 𝑑𝑢𝑖𝑛𝑣(β*D_{a}V[>])`; the decision state at each saving, from the stage's law of motion solved for it, `m[>] = a + c[>]`; and the identification of the policy with the candidate, `c = c[>]`. Where the choice is constrained, write the constraint's clause on the candidate line, `c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0` ([Constraints](10-constraints.md) §4.3).
5. For value function iteration, write `cntn_to_dcsn.method : !vfi` at file level, since the method brings no line. Its grid lies on the decision states; where the handler compares candidate levels of the control, give the grid a feasible factor for the control, `cntn_to_dcsn.grid : !Cartesian(c=(Γ, n_c))`, as the cons-port application's file `methods.vfi.bl` does. The handler then carries out the maximization of the policy block. A feasible factor written without `!Fibred` states a family of grids of the control, one at each state; to declare one joint grid of states and feasible controls, which `kernels().grids` constructs, write `cntn_to_dcsn.grid : !Fibred(base=!Points(nodes=B), fibre=!Cartesian(c=(Γ_c, n_c)))` (§3.2).
6. For a builder whose solution is known in closed form, write a block with the builder's id, `method : !explicit` in its bracket and one line `output = expression` for each output (§3.5). Its Evaluation then takes `!closed_form` unless an entry types another representation there.
7. For each value builder whose derivative is read, write a block with the builder's id that holds its derivative line: the envelope condition of the decision value, `D_{m}V = 𝑑𝑢(c)`, which the arrival block of the same stage reads, and the derivative of the arrival value with the factor of the law of motion inside the expectation, which the policy builder of the period before reads as `D_{a}V[>]`. Where the law of motion between two perches is the identity, no line is written (§5).
8. Type a representation at each Evaluation whose function is read between its grid points: `evaluate.method : !Linear` with `evaluate.grid : !Cartesian(…)` on the states of its perch, one entry for the value and its stated derivative together, or one for each stored object, `evaluate[V[<]].method` and `evaluate[D_{k}V[<]].method`. Under `!egm` the consumption function takes `evaluate.method : !Linear` and no grid entry, since the representation reads the pairs the method computes (§3.4).
9. Give each expectation its quadrature, `E_ψ_ξ.method : !gauss_hermite(n_ψ=n_ψ_nodes, n_ξ=n_ξ_nodes)`, in the bracket of the block that holds it, and each forward builder a representation of the distribution it carries, `arvl_to_dcsn.method : !deterministic`, where the model is simulated.
10. Write each entry of a block to which the file adds no line at file level, with its full path, since a block with an empty body is refused.
11. Elaborate the stage with the file and read `stage.places()`, `stage.methods` and `stage.settings`; after configuration, read the card of the policy builder, `stage.builder.policy.denote()`, which prints the maximization under `Declared` and the method's lines under `Operations`.

The candidate lines of a solution method define a relation, a set of pairs of states and controls, from which the identification line reads the policy. Whether that relation defines one policy on the whole domain is the condition of [Appendix C](appendices/14-appendix-c-syntax-to-semantics.md) R10 and §4.6, and whether that policy is the maximizer is the condition `egm-eligibility` of §5; the stage records both, and the package checks neither.
