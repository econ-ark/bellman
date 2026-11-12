---
audience: user
type: theory
topic: [calculus]
---
# Abstract grammar

This page describes mathematical composition terms for stages, periods and trellises. #syntax #ffp

> [!summary]
> A composition term records which stage and connector operations are combined. This mathematical notation is distinct from the concrete `.bl` grammar, its temporary parser tree and the retained structures of a constructed stage. The period and trellis calculations below illustrate the distinction.

> [!info]- Relationship with other documents
> **Builds on** — [Stage composition](./07-stage-composition.md) and [Periods and the trellis](./08-periods-and-trellis.md) define the compatible compositions.
> **Formal account** — [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) treats specified terms and interpretations; [The stage term](./APPX-C-STAGE-TERM.md) gives the stage-level signature.
> **Used by** — [Stages](../Bellman-Sym/01-stage.md), [Field equations](../Bellman-Sym/03-field-equations.md), [Period Syntax](../Bellman-Sym/06-period.md), [Trellis Syntax](../Bellman-Sym/07-trellis.md) and [Methodization](../Bellman-Sym/04-methodization.md) state the authoring rules; Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) states the interpretation rules.

## 1 Two grammars

The **concrete grammar** specifies which source strings are well formed. The **abstract grammar** describes the structure of their expressions after punctuation is removed. Schmidt distinguishes the derivation tree from the string that abbreviates it.[^schmidt] For the current language, the declarations and arithmetic equations of `.bl` stage files and methods files are parsed, while supporting YAML records model composition and the values that calibration and configuration bind. The mathematical composition notation used here is a separate description of the resulting operations.

The syntax pages use **ASDL**, the Zephyr Abstract Syntax Description Language, to describe constructor positions and their types.[^asdl] An **ASDL field** is a named position in a constructor, distinct from an economic field. The symbols `?` and `*` denote an optional position and a list. These notations describe syntax structure; they do not make every mathematical diagram on this page a concrete parser constructor. An operator's method and grid components, written as typing entries of the operator's name, are described in [Methods](./06-Methods.md) §2.

The following is schematic mathematical composition notation, not the `.bl` abstract grammar or a loader schema. It suppresses documentation names and binding records to show the composition operands:

```text
model_term = TRELLIS(period* periods, connector* inter_connectors)
period     = PERIOD(stage_occurrence* stages, connector* connectors)
connector  = CONNECTOR(pair* pairs)
pair       = (identifier source, identifier target)
```

Here a stage occurrence supplies an already specified stage operation with its required inputs. Stage declarations, function bodies, arithmetic, local binders and branches have their own source structures; they are not terminal atoms in the concrete grammar. The current forms are recorded on Bellman-SYM's pages on stages and field equations. [The stage term](./APPX-C-STAGE-TERM.md) gives a mathematical inventory, not a competing `STAGE` parser production.

A connector records compatible field identifications. An empty explicit rename list gives an identity connection only when the source rules already determine matching boundaries; it cannot supply missing compatibility. The compositions below are restricted to chains with those identifications specified. General branching and the economic order of stages are not determined by the order of entries in an ASDL list. [Periods and the trellis](./08-periods-and-trellis.md) §§3–6 supplies the boundary conditions.

A source format can be changed without changing meaning only when its translation preserves the declared terms, binding and interpretation. A new file format is not automatically equivalent because it can store similar lists. Three objects therefore remain distinct: the source string, a mathematical term describing composition, and its interpretation in a specified algebra of operations.

## 2 Expressions are objects

Backus's [FFP systems](../wiki/ffp.md) use objects to represent functions systematically. Functional forms are represented by sequences whose first element identifies the form and whose remaining elements give its parameters.[^backus-131] The representation and evaluation functions are part of the description of the system.[^backus-1331] This provides a comparison with headed composition records; it does not prescribe the parser or runtime representation of Bellman-SYM.

[Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §§1–5 supplies the underlying definitions, the algebra of combining forms and the distinction between an FP object and an object in a category. The examples below apply that account to model composition.

> [!note]
> Backus's representation function $\rho$ and meaning function $\mu$ are his notation. This page uses $\Upsilon$ for the interpretation of its mathematical terms. Backus's $\rho$ is distinct from this project's numerical-construction map Ρ and from a utility-curvature parameter.

Consider the existing two-stage consumption–portfolio composition schematically. The current period authoring example of Bellman-SYM includes a separate discount stage; here its placement is left within the specified stage operations. Once their compatible boundaries and fixed policies have been supplied, a coarse object representation is

$$
P\equiv\langle\mathrm{PERIOD},\langle s_{\mathrm{cons}},s_{\mathrm{port}}\rangle,\langle C\rangle\rangle,
\qquad C\equiv\langle\mathrm{CONNECTOR},\langle\langle a,k\rangle\rangle\rangle.
$$

The symbols $s_{\mathrm{cons}}$ and $s_{\mathrm{port}}$ represent stage occurrences, and $\langle a,k\rangle$ identifies outgoing assets with incoming capital. The sequence is a mathematical encoding of these operands, not the actual YAML mapping. Its interpretation is

$$
\Upsilon(P)=\Upsilon(s_{\mathrm{cons}})\circ\varkappa^*\circ\Upsilon(s_{\mathrm{port}})
=\mathbb T_{[\mathrm{cons}],\pi}\circ\varkappa^*\circ\mathbb T_{[\mathrm{port}],\pi}.
$$

The map $\varkappa$ identifies the compatible boundary states, and its **pullback** acts on functions by $(\varkappa^*v)(x)=v(\varkappa(x))$. It implements the declared renaming, not a new economic transformation. Consumption precedes portfolio choice in economic time; the portfolio operator is applied first in backward calculation. Field dependencies and declared joins establish this order, not YAML list position.

This composition resembles Backus's **insert**, which applies a binary function repeatedly across a sequence.[^backus-insert] To use insert on representations of functions, one must specify an operation that constructs a representation of their composite. Backus's FFP allows forms represented by objects; it does not by itself define the calculus's composition rules. Here those rules are the displayed equations on compatible domains.

For a finite horizon of $H\ge2$ periods, numbered here in forward economic order, write

$$
N\equiv\langle\mathrm{TRELLIS},\langle P_0,\ldots,P_{H-1}\rangle,
\langle\chi_0,\ldots,\chi_{H-2}\rangle\rangle,
\qquad
\Upsilon(N)=\Upsilon(P_0)\circ\chi_0^*\circ\Upsilon(P_1)\circ\cdots\circ\chi_{H-2}^*\circ\Upsilon(P_{H-1}).
$$

This numbering differs from the application's backward-from-terminal index described in §1 of Bellman-SYM's Trellis Syntax page.

Each $\chi_i^*$ is the pullback of the compatible inter-period identification. For one period, there are no inter-period connectors. With terminal function $v_T$ in the last operator's domain, backward evaluation is

$$
\Upsilon(N)(v_T)=\Upsilon(P_0)\Bigl(\chi_0^*\bigl(\Upsilon(P_1)(\cdots\Upsilon(P_{H-1})(v_T)\cdots)\bigr)\Bigr).
$$

Every intermediate output must belong to the next input domain. Free parameters and policies are held fixed in these displays; an optimizing interpretation requires its separately defined operators. The calculation resembles evaluating a represented compound form from its constituent meanings, but Backus's metacomposition rule does not supply the economic identities or assumptions.[^backus-meta]

Backus's inner-product example combines summation, pairwise multiplication and transposition.[^backus-52] The comparison is structural:

| Role | Backus's inner product | Mathematical model composition |
|---|---|---|
| Constituent functions | $+$, $\times$, $\mathrm{Trans}$ | Stage operators and connector pullbacks |
| Combining forms | $/{+}$, $\alpha\times$, $\circ$ | Compatible composition at period and trellis levels |
| Whole expression | $\mathrm{IP}\equiv(/{+})\circ(\alpha\times)\circ\mathrm{Trans}$ | $P$ or $N$ as defined above |
| Application | $\mathrm{IP}:\langle x,y\rangle$ | $\Upsilon(N)(v_T)$ |

Here $/{+}$ sums a sequence, $\alpha\times$ multiplies corresponding entries and $\mathrm{Trans}$ transposes a pair of lists. Backus wrote this example in FP; representation of functions by objects is the additional FFP construction. The table is an analogy between compositions, not an identity of languages.

## 3 The model term

The mathematical nesting can be displayed as a tree. This schematic suppresses the internal equation structures:

```text
TRELLIS
├─ PERIOD P₀
│   ├─ stage occurrence s_cons
│   │   ├─ transitions and reward
│   │   ├─ conditional shock laws
│   │   └─ definitions, parameters and domains
│   ├─ stage occurrence s_port
│   └─ CONNECTOR
│       └─ field pair (a, k)
├─ inter-period connector χ₀
├─ PERIOD P₁
└─ …
```

**The stage entries have internal structure.** The tree suppresses it for the composition calculation; it is not a claim that arithmetic or local definitions are unparsed. Backus distinguishes primitive functions, defined functions and functional forms.[^backus-tri] This classification offers a comparison with supplied operations, local definitions and ways of combining operations. Parameters, field names and domains are other inputs, not automatically members of that function classification.

**The displayed tree suppresses builder symbols.** At this coarse level, $\Upsilon$ assigns each stage occurrence its specified backward operation and composes those operations through the connectors. In the finer signature of [The stage term](./APPX-C-STAGE-TERM.md), builders are themselves symbols. The uniqueness statement in [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) §§1–2 applies only after the signature, target operations and assignments to free inputs have been supplied. It does not infer missing economic equations from a stage header.

**The encoding resembles FFP representations.** A head and its operands describe a represented compound operation. The term remains distinct from its mathematical meaning and from whichever software structures retain interpreted equations.

<a id="4-what-the-tree-is-not"></a>

## 4 Source and retained structures

Arithmetic such as `R*k + y` is parsed into expression structure. Local function types and binders remain available to interpretation; substitution must respect scope. The source may author evaluation, optimization and implicit relations. Their meaning and applicable conditions come from the declared expression and the interpretation rules of Bellman-SYM's Appendix C, not an inference that all branches expose the same method operations.

In the specified construction, parser trees and source locations are temporary. The stage retains interpreted equations, definitions and typed diagrams. Periods and the trellis retain their outer records, with fresh objects for distinct occurrences; reuse of a module does not imply one shared mutable stage object or a retained whole-trellis syntax graph. These statements describe the construction specified for the language, not completion of every runtime component.

The mathematical signatures used here are **many-sorted**: each symbol has a rank, its declared input sorts and its output sort ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §3, D1). Their vocabulary is the specified signature under discussion. Adding a form requires extending that signature and its interpretation; defining a local function within the admitted language is a different act. Neither statement proves all the identities an extension might need.

Branching also requires its own interpretation. A finite choice compares complete feasible branch values; an exogenous branch uses the declared conditional probabilities. Evaluating all feasible branch values and then maximizing is generally different from evaluating a single branch selected by a pre-existing predicate. Ties and measurable policy selection retain the qualifications in [Branching](./09-branching.md).

## 5 The typing entries of a methods file

A methods file adds to a stage file the numerical choices of its operators without changing the model's equations: a **typing entry** types one component of an operator by the path of that component, `policy.method : !egm(tol=tol_v)` for the method and `policy.grid : !Cartesian(a=(a_min, a_max, n_a))` for the grid, the discretized domain on which the operator's function is represented, written with one of the three grid words `!Cartesian`, `!Points` and `!Fibred`; a **handler binding**, `policy.handler : "cons-port:egm"`, names the program that realizes the operator. An entry stands inside a block's header, in the groups that `|` opens after the block's own entries, or at file level with the full path. A typing entry assigns the method or the grid component of one operator's signature, so that the operator is realized by that method on that grid while the model's equations are unchanged, and a handler binding names the program that realizes it ([the handler](../wiki/handler.md)); this section records the constructors the entries parse to, in the house dialect of the ASDL notation, with the grammar that owns each line: `(core)` for a form that dyno's own files could carry, `(stage)` for a form that belongs to the typing layer of Bellman-SYM.

The representation words `!Linear`, `!pchip` and `!closed_form`, each of which states the numerical form of a function ([Methods](./06-Methods.md) §4), and the word of the explicit solution method, `!explicit`, are method words like `!egm`, written in a typing entry of the method component, `policy.evaluate.method : !Linear` or `policy.method : !explicit`. The lines of `!explicit`, which give each output of the builder by a formula, stand in a block of the methods file whose id is the builder's, as the lines of `!egm` do (§5 of Bellman-SYM's page on methodization). A [derived parameter](../wiki/parameters.md), a name that a definition without arguments defines from parameters, derived parameters and numbers, `h := 1/(1 - Γ/R)`, is written in a stage file or a methods file with the definition form `:=` that a stage file already uses. Its definition may declare a set, `q : (0,1) := (β*R)^(1/ρ)/R`, and the line is then a declaration that carries a value. A derived parameter that a methods file defines adds a condition on the parameters, that its value exists and lies in its declared set, which is $\mathbb R$ where none is written. For a stage methodized by that file, the admissible set of the parameters is the set of the parameter vectors at which these conditions hold as well as those of the stage file ([Kinds and sorts](./APPX-D-KINDS-AND-SORTS.md) §4). None of these forms adds a constructor: a method word is held by the `Method` component of the box below, the block is the host's `Block`, and the definition of a derived parameter is the host's `Assignment`, or, with a declared set, the host's `Declaration` with its `value`.

> [!ast]- Abstract grammar: the typing entries
> The host constructors keep their profiles; the lines below are added as alternatives of existing sorts (`+=`) or as new sorts. `Declaration` is the host's, reused: a typing entry is a `Declaration` whose subject is a `Path` and whose one component is the `Method` or the `Grid`.
>
> ```asdl
> entry      += Tagged(word tag)                               -- (core)  a tag with keyword arguments
> word        = Word(identifier name, keyword* arguments)       -- (core)  a name with its keyword arguments
> keyword     = Keyword(identifier key, argument value)         -- (core)
> argument    = Name(identifier name)                           -- (core)  the name of a setting
>             | Literal(number value)                           -- (core)
>             | Quoted(string text)                             -- (core)
>             | Values(argument* items)                         -- (core)  a tuple of values
>             | Nested(word word)                               -- (core)  a word with arguments of its own
> subject    += Path(segment* segments)                         -- (stage) the path of a component
> segment     = Segment(identifier name, selector* selectors)   -- (stage) a name with its selectors
> selector   += Term(expr at)                                   -- (stage) a term as a selector
> typer      += Handler(subject subject, string program)        -- (stage) the handler binding
> classifier += Method(word m)                                  -- (stage) the method component
> classifier += Grid(grid g)                                    -- (stage) the grid component
> grid        = Cartesian(factor* factors, identifier* require) -- (stage) at most one factor per coordinate
>             | PointGrid(identifier? nodes, identifier* require)   -- (stage) !Points: the declared points, or none for the empty grid
>             | Fibred(grid base, grid fibre, identifier* require)  -- (stage) each base state with its control's feasible points
> factor      = Spaced(identifier coordinate, argument lower, argument upper,
>                      argument count, word? spacing)           -- (stage) bounds, a count, a spacing word
>             | Listed(identifier coordinate, identifier nodes) -- (stage) a node set, or the operator whose nodes the coordinate takes
>             | Feasible(identifier coordinate, identifier set, argument count)   -- (stage) a control's feasible set with a count
> ```
>
> The requirements the notation cannot state are part of well-formedness instead: a path has at least one segment and its last segment names the component, `method`, `grid` or `handler`; a word's arguments are keyed once each; a `Cartesian` grid has at least one factor and names no coordinate twice, and the order of its factors carries no meaning; a bound or a count of a factor is written as a name or a number, and binding admits only the name of a setting a methods file declares; a spacing is a word, with or without arguments; a `PointGrid` without `nodes`, as `!Points` alone writes it, is the empty grid; `require` lists the predicate words written after it, one `!`-word or a tuple of them, each without arguments, by name and in written order, and in `!Cartesian` a `require=` value of any other shape is the factor of a coordinate named `require`.
>
> **Keys.** `segments` are the names from the block to the component, each with the selectors that name the object an Evaluation stores (`evaluate[V]`, `evaluate[D_{k}V[<]]`); `m` is the method word with its keyword arguments, read by the catalogue of methods; `g` is the grid; `program` is the handler's name as the quoted string writes it; `factors` are the factors of a `!Cartesian` grid, each keyed by the coordinate it covers; the `nodes` of a `PointGrid` is the name of the declared points; `base` is the grid of the states and `fibre` the grid of the control at each of them; `require` holds the names of the predicate words written after it, among `!Empty`, `!Cartesian`, `!NonCartesian` and `!UniformCartesian`. Of these ASDL fields, the `nodes` of a `PointGrid`, `base`, `fibre` and `require` are also written as the keyword arguments of the grid words, `!Points(nodes=P)`, `!Fibred(base=…, fibre=…)` and `require=!UniformCartesian`; the others are not keys to write in a file.
>
> **Head.** Inside a header, an entry is one entry of the block's annotation, whatever group it is written in; at file level it is a declaration whose subject is a dotted path. The `!` marks a word, the dot joins the segments of a path, `=` joins a keyword to its value, and a quoted string names a handler.
>
> **Denotes.** The method and the grid are the classifier components of the operator's signature, read by the numerical semantics and by nothing in the exact semantics; the handler is a binding beside the term. A grid denotes a finite set of points of the domain of its place: for `Cartesian`, the product of one node set per coordinate; for `PointGrid`, the finite support of the declared points, empty when none are named; for `Fibred`, the pairs of each base state with the grid points of the control's feasible set at that state. A predicate word of `require` is a condition on that set and no component of the signature. [Methods](./06-Methods.md) gives the account, the grid in §5.
>
> **Status.** The grammar parses these entries and lowers them to the constructors above. A grid is one outer grid word, `!Cartesian`, `!Points` or `!Fibred`; the words `!TensorUnion`, `!Image` and `!Smolyak` are reserved by name for grids that are not built, and the loading code refuses them, as it refuses any other word. Which words are admitted at which operator, at which places each grid word may stand, which keywords each reads, whether a factor's name is a node set or an expectation operator, whether the `base` of `!Fibred` is `!Points` or a `!Cartesian` term without feasible-control factors and its `fibre` a `!Cartesian` term of feasible-control factors, and whether each predicate word is known and consistent with the others are judged when the entries bind, not by this grammar box.

<a id="see-also"></a>

## 6 Related documents

- [FFP](../wiki/ffp.md), [functional form](../wiki/functional_form.md), and [ASDL](../wiki/asdl.md) define the programming-language terms.
- [Semantics](./APPX-A-SEMANTICS.md) relates interpreted equations to numerical methods.
- [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) states the conditions for unique interpretation and exact refinement.
- [The stage term](./APPX-C-STAGE-TERM.md) gives the finer mathematical signature.

[^schmidt]: D. A. Schmidt, *Denotational Semantics: A Methodology for Language Development*, Allyn and Bacon, 1986, ch. 1, opening discussion, p. 8: "the derivation trees are the real sentences of a language, and strings of symbols are just abbreviations for the [trees]."
[^asdl]: D. C. Wang, A. W. Appel, J. L. Korn, and C. S. Serra, "The Zephyr Abstract Syntax Description Language," *Proceedings of the USENIX Conference on Domain-Specific Languages*, 1997.
[^backus-131]: J. Backus, "Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs," *Communications of the ACM* 21(8), 1978, §13.1, p. 631.
[^backus-1331]: Backus (1978), §13.3.1, p. 632.
[^backus-meta]: Backus (1978), §13.3.2, p. 632: $(\rho \langle x_1, \ldots, x_n \rangle)\!:\!y \equiv (\rho x_1)\!:\!\langle\langle x_1, \ldots, x_n\rangle, y\rangle$.
[^backus-insert]: Backus (1978), §11.2.4, p. 621: $/f\!:\!x \equiv x{=}\langle x_1\rangle \to x_1;\; x{=}\langle x_1, \ldots, x_n\rangle \,\&\, n \geq 2 \to f\!:\!\langle x_1, /f\!:\!\langle x_2, \ldots, x_n\rangle\rangle;\; \bot$.
[^backus-52]: Backus (1978), §5.2, p. 616.
[^backus-tri]: Backus (1978), §11.2.3, p. 620: every function in $F$ is primitive, defined, or a functional form.
