---
title: Appendix D — Kinds, sorts, and types
short_title: "Appendix D: Kinds and sorts"
status: drafted — Phase 1
central_source_for: the theory and the definitions of the type system that the package implements (AAS, 11 November 2026)
instruction_for_agents: "Decisions, amendments, specifications, the elaboration and other documents are to be made consistent with this appendix. A decision about types, such as how the declared domains of a parameter intersect, either follows from the definitions, results and formal system of this appendix and of the calculus, or revises this appendix in the same piece of work. Where another document disagrees with this appendix, bring that document into agreement with it, or put the disagreement to AAS."
tags:
  - bellman-calculus
  - type
  - universal-algebra
  - field
authors:
  - Akshay Shanker
audience: user
type: theory
topic:
  - calculus
  - types
---

# Appendix D — Kinds, sorts, and types

> [!summary]
> We state the type system of the calculus as one account. A type, such as `!ctrl @ ℝ₊₊`, classifies a field, a parameter or a setting by the conditions it writes, and the parameter lines of a file define one set of admissible parameter vectors. The state sorts and the transitions of a stage form a signature, and the models of the stage's declaration graph give each transition a stochastic kernel and two builders, one on tuples of representing functions and one on measures. Fields are classified by their values, roles, information and origins. A policy rule selects one policy; a maximizing rule requires a measurable maximizer. The backward builders evaluate every decision field at that policy.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md): the stage, its perches and its operators; [Fields, functions and types](./04-fields%2C%20functions%20and%20types.md): fields and their representing functions.
> **Used by** — Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the rules that give a file's text its meaning; [Stages](../Bellman-Sym/01-stage.md) §2 and [Symbols and conventions](../Bellman-Sym/reference/symbols-conventions.md) §9: what an author writes in a type; [Method types](../Bellman-Sym/reference/methods.md): the method words and the grid words; [Appendix E](./catalogues/index.md): the catalogues of the objects classified here.
> **See also** — [The stage term](./APPX-C-STAGE-TERM.md): the operator signature of a stage and its compositions; [Methods](./06-Methods.md): the method and the grid of an operator; [Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §§5 to 8: terms, calibration and the binding maps.

<a id="0-setup"></a>
<a id="the-account"></a>

## 1 The account

The type system of the calculus is **a classification of the declared quantities by predicate subtypes, and the free category of a dynamic program with its forward and backward models**. The first part says what a written type means: a **predicate subtype** is a subset that a condition picks out. The second part says what a stage means: its states and transitions form a graph, its models are functors out of free categories built on that graph, the models give each transition its builders, and the Bellman operator is formed from the builders.

In the words of the literature, the second part is a many-sorted signature in which every whole-builder symbol takes exactly one argument, which may be a tuple, with its meaning given by such functors (§6). Here **the account** means the definitions and the propositions of this appendix, and **the language** means what a stage file and a methods file may write.

Two names are avoided. A set that names a parameter is what the sources call type dependency (Jacobs 1999, §4.6, p. 273, and §11.1, pp. 648–649), but "dependent type theory" also has function types whose result type depends on the argument (Jacobs 1999, §10.1, pp. 584–585), and the system has none. "Order-sorted algebra" requires a declared order on the sorts (Goguen and Meseguer 1992, Definition 2.1), and here none is declared. "Categorical type system" is a fair informal name for the second part, and no source defines it.

The next table is an index: each row gives a word, its meaning in a few words and the place that defines it. Sections 2 to 6 define the words in order, and where a definition refers ahead, as §3 does to the role and perch classifiers of §5, it names the section. Each proposition of §7 is proved from definitions that precede its first use.

| Word | Meaning | Defined in |
|---|---|---|
| declaration | a line that introduces one name with its type | §2 |
| type | what a file writes after a typing colon | §2 |
| component | one part of a type | §2 |
| ambient set | a set of every value of one nature | §2 |
| signature | sorts, and symbols with ranks | D1 |
| rank | the source sorts and the target sort of a symbol | D1 |
| carrier | the set that interprets a kind or a sort | D2 |
| algebra | a carrier for each sort and a map for each symbol | D2, §6 |
| kind | a name for the set of all objects of one nature | D3 |
| sort | a name or a condition for a subset of a kind's carrier | D4 |
| classifier | a function from part of a kind's carrier into ordered values | D6 |
| class | the members whose value lies at or below a given value | D6 |
| declared set | where a declared quantity takes its values; an economist's "domain" | D6 |
| parameter | a name that the stage file declares with a set and no line writes | §4 |
| derived parameter | a name defined by `:=` from the parameters | §4 |
| admissible set | for the parameters, where every condition on them holds; with a methods file that defines derived parameters, the subset where their conditions hold too; for the settings, where every condition on them holds | §4 |
| calibration | a point of the admissible set of the parameters | §4 |
| implicit restriction | the condition that a definition puts on the parameters | §4 |
| setting | a name that a methods file declares with a set; a grid word and a method word name settings and write no number, and the value of a keyword argument of a method word is the name of a setting, a quoted string or a word with arguments of its own | §4 |
| family | an indexed collection, one member for each index | §4 |
| configuration | a point of the admissible set of the settings | §4 |
| field | a declared random quantity of a stage | §5 |
| shock | a field with a law | §5 |
| state of a perch | the tuple of state fields listed at that perch | §6 |
| state sort | the sort of the state of a perch | §6 |
| transition | a symbol between two state sorts, as a law of motion with its shock law | §6 |
| term | a path of symbols | §6 |
| declaration graph | the states of the perches and the edges between them | §6 |
| model | an object for each vertex and an arrow for each edge | §6 |
| well posed | said of a stage at a parameter vector and supplied tuple where its domain and policy conditions hold | §6 |
| builder | an operator that a model gives a transition; also the policy builder and the optimizing decision builder | §6 |
| occurrence | an operator at its place in a stage, one box of its semantic graph | §6 |
| label | a value of the method classifier or of the grid classifier | §6 |

<a id="sets-of-values"></a>

## 2 Sets of values

**Source forms.** A **stage file** states a stage in declarations and **blocks**, groups of equations under a **header** whose two **sides**, before and after its arrow `->`, list what the block reads and what it writes. A **methods file** adds the numerical methods of the stage ([Methods](./06-Methods.md) §1). A **type** is the expression that a file writes after a **typing colon**, and a **declaration** is a line that introduces one name and writes its type, as `c : !ctrl @ ℝ₊₊` does. The name, with what the files state about it, is a **declared quantity**.

The **components** of a type are its parts, written with `@` between them: sets, a **role word** such as `!ctrl`, or a **perch word** such as `!dcsn` (§5). In a methods file, the type of an operator's method or grid is a **method word** such as `!egm` or a **grid word** such as `!Cartesian`, with its arguments (§6).

A **law** is a probability distribution, which a file states in a line such as `y ~ LogNormal(μ_y, σ_y)`. A law may take a supplied constant (§5) as an argument, as `y(_age) ~ LogNormal(μ[_age], σ_y)`. The name `_age` is local to the right side. A forward use `y(age)` supplies the value and declared set of `age`; an unapplied law leaves that set unresolved.

**Ambient sets.** Every value lies in one **ambient set**: the numbers, the names of one finite set of names, the tuples of a product of ambient sets, or functions between specified measurable sets. The numbers form the extended real line $\bar{\mathbb{R}}=[-\infty,\infty]$, with $\mathbb{R}$, $\mathbb{R}_+=[0,\infty)$, $\mathbb{R}_{++}=(0,\infty)$, $\mathbb{Z}$ and $\mathbb{N}$ inside it. The language leaves open whether $0$ lies in $\mathbb{N}$, and an author who needs the bound writes it, as in `ℤ @ [1, inf)`.

**Set expressions.** A **set expression** is the text a file writes for a set. It may contain names, as the interval `(0, R)` contains `R`, and an **assignment** gives each such name a value. At each assignment at which its expressions have values, it denotes a subset of one ambient set, in one of these forms.

| Form | Example | The set it denotes |
|---|---|---|
| reserved set | `ℝ`, `ℝ₊`, `ℝ₊₊`, `ℤ`, `ℕ`, `ℝ̄` and others | a fixed set of numbers |
| named set | `Xm`, after `Xm := ℝ₊₊` | the set its definition writes |
| interval | `(0, R)`, `[1, inf)` | the numbers between its endpoints, each included or excluded as its bracket states |
| set of names | `{work, retire}` | the names listed |
| integer range | `{1, …, J}` | the integers from the first bound to the second |
| listed integers | `{1, 2}` | the distinct integers listed |
| product | `ℝ × ℝ₊` | the tuples with one coordinate in each factor |
| set of functions | `L_J → ℝ`, `Xa → ℝ` | the measurable functions from the declared source set to the declared target set; the source need not be finite |
| set with a bar | <code>H := {i : ℤ &#124; i &gt;= 0}</code>, in the definition of a named set | the members of the set after the colon that satisfy every condition after the bar |
| union | `(0,1) \/ (1, inf)` | the numbers in at least one of the sets |
| difference | `ℝ \ [0, 1]` | the numbers in the first set and outside the second |

**The algebra of subsets.** The subsets of one ambient set form a Boolean algebra: they are closed under intersection, union and complement (Jacobs 1999, §0.2, p. 12). The language writes the union of `A` and `B` as `A \/ B` and their relative difference as `A \ B`, among sets of numbers and only in the set of a parameter, of a derived parameter or of a setting (§§4 and 9). An intersection is written by listing sets as components of one type (§3), and the sign `@` is no form of a set expression. No sign stands for a complement, by choice: a difference names the set in which the complement is taken.

<a id="1-definitions"></a>

## 3 Basic definitions

**D1 (Signature).** A **signature** has a set of names called **sorts** and a set of names called **symbols**. Each symbol has a **rank**: its source sorts and its target sort. A symbol $o$ with the one source sort $t$ and the target sort $t'$ is written $o:t\to t'$. A signature may mark a symbol as a **decision symbol** and give it a set of **indices**, which identify its decision edges (§6). Without these indices this is a many-sorted signature (Goguen, Thatcher, Wagner and Wright 1977, §2, p. 70). Those authors call the source sorts with the target sort the type of the symbol; the word rank for them is that of Goguen and Meseguer (1992, Definition 2.1).

**D2 (Carrier).** A **carrier** is the set that interprets a name. A name, its carrier and a member of the carrier are three objects. An **algebra** of a signature in sets gives each sort $t$ a carrier $A_t$, each symbol of rank $t_1,\ldots,t_n\to t'$ that is no decision symbol a function $A_{t_1}\times\cdots\times A_{t_n}\to A_{t'}$, and each decision symbol one such function for each of its indices. §6 defines a category and states the same in one, where a carrier is an object of the category.

**D3 (Kind).** A **kind** is a name interpreted by a set, its carrier $K$, which holds every object of one nature. The account assigns each declared quantity, and each object that a stage constructs, to exactly one kind, and classifies it in that kind alone. No file states a kind. Each ambient set of §2 is the carrier of a kind of values. The account fixes nine further kinds where their members are defined: `Parameter` and `Setting` in §4, `Field` in §5, Step 1, `Function`, `Measure`, `Operator`, `Grid` and `Method` in §5, Step 6, and `FunctionTuple` in §6. A member of `FunctionTuple` is a finite tuple of representing functions. Two carriers may share a member: a function that a stage constructs on a finite set is also a member of an ambient set of functions (§2), and the account assigns it to `Function`.

**D4 (Membership).** Within a kind with carrier $K$, a **sort** $s$ is a name, or a written condition, interpreted by a subset $A_s\subseteq K$, its carrier (Meseguer 1998, §2, Definition 2). A subset given by a condition is a predicate subtype (Rushby, Owre and Shankar 1998, §II, pp. 709–710). The statement $x:s$ asserts that $x$ belongs to $A_s$. Every sort belongs to exactly one kind (Meseguer 1998, §2, Definition 1), and $x:s$ is formed only for an object $x$ already known to be of that kind, so objects are compared and classified inside one kind only. A set expression names a sort of values, whose carrier is the subset it denotes. A sort of a signature (D1) is a sort in this sense once its carrier lies in the carrier of one kind, as the carriers of §6 do.

**D5 (Order on sorts).** An order-sorted signature declares a subsort relation $s\le s'$ and interprets it by an inclusion $A_s\subseteq A_{s'}$ (Goguen and Meseguer 1992, Definitions 2.1 and 2.7). The account declares no order and derives a **preorder**, a reflexive and transitive relation, on the sorts of one kind: $s\le s'$ holds exactly when the condition of $s$ implies that of $s'$ in every stage and at every assignment, so that $A_s\subseteq A_{s'}$ at each.

**D6 (Classifier).** A **classifier** is a function $c$ from a stated part $\operatorname{dom}(c)$ of the carrier $K$ of a kind into a set $I$ of **values** with a preorder $\le$. Its **class** at a value $i$ is the set

$$
R_c[i]=\{x\in\operatorname{dom}(c):c(x)\le i\}.
$$

This condition on $x$ defines a sort of the kind, which $R_c[i]$ also names, and the classifier itself is no sort. Under the **discrete order**, in which $i\le j$ only when $i=j$, the class at $i$ is the **fiber** $c^{-1}(i)$, and the fibers are disjoint and cover $\operatorname{dom}(c)$. In a second case, each declared quantity $x$ has a **declared set** $D_x$, the set in which it takes its values, a subset of one ambient set. Let $I$ hold every subset of every ambient set, the empty set among them, ordered by inclusion. Each of the three kinds of declared quantities, `Field`, `Parameter` and `Setting`, has its own classifier of declared sets, $c(x)=D_x$ on its carrier. The greatest lower bound of $D_1$ and $D_2$ in $I$ is $D_1\cap D_2$, and the class of each at a subset $D$ is

$$
\mathrm{Dom}[D]=\{x\in\operatorname{dom}(c):D_x\subseteq D\}.
$$

A declared set is nonempty, since a quantity with an empty declared set denotes nothing. A set expression writes it, so $D_x$ and $\mathrm{Dom}[D]$ are taken at each assignment at which the declared sets have values and are nonempty. The conditions of §4 secure this for the parameters at every calibration and for the settings at every configuration, and for the fields it is the first condition of a well-posed stage (§6).

**D7 (Intersection sort).** For sorts $s$ and $s'$ of one kind, $s\wedge s'$ is the sort whose condition is the conjunction of their conditions, so that $A_{s\wedge s'}=A_s\cap A_{s'}$. It is their greatest lower bound in the preorder of D5, because a condition that implies both implies their conjunction.

**The sort a type names.** Each type component names a classifier class. A set $D$ names $\mathrm{Dom}[D]$ in the quantity's kind; a role word names a fiber; a perch word names an ordered class (§5).

The type names the intersection of these sorts (D7), and a declaration asserts that its declared quantity is a member of that sort (D4). A set expression thus names two sorts: a sort of values when it stands alone, and a sort of declared quantities as a component. P8 (§7), on the intersections and the unions of classes, has three consequences.

First, two components with the values $i$ and $j$ of one classifier name $R_c[i\wedge j]$ where $i$ and $j$ have a greatest lower bound $i\wedge j$, so two sets $D_1$ and $D_2$ in one type name $\mathrm{Dom}[D_1\cap D_2]$. Where the two sets have no common point this is $\mathrm{Dom}[\varnothing]$, which is empty because a declared set is nonempty, and the language refuses such a type where the written text shows it, as it refuses an interval whose written endpoints leave it empty.

Second, two components whose values have no common lower bound name an empty sort. Under the discrete order any two different values are such a pair, so the language refuses two different role words in one type. Perch values have the order of information (§5), so two perch words mathematically name the class of the earlier perch. The language nevertheless requires one perch word per listing.

Third, the union of $\mathrm{Dom}[D_1]$ and $\mathrm{Dom}[D_2]$ need not be $\mathrm{Dom}[D_1\cup D_2]$. With $D_1=(0,1]$ and $D_2=(1,2)$, a quantity with the declared set $(0,2)$ lies in $\mathrm{Dom}[D_1\cup D_2]$ and in neither $\mathrm{Dom}[D_1]$ nor $\mathrm{Dom}[D_2]$. A union is therefore formed among sets of values, inside the set expression, and never with a sign between components.

<a id="parameters-and-settings"></a>

## 4 Parameters and settings

**Parameters.** A **parameter** is a name that the stage file declares with a set, with no role word, no perch word and no law, that no block header lists, that no line of a block writes and that no line defines by `:=`. Number the parameters of a file $1,\ldots,n$, and let $\Theta_0$ be the product of their ambient sets. A parameter denotes one coordinate $\theta_j$ of a **parameter vector** $\theta\in\Theta_0$, an assignment in the sense of §2, and $\theta_p$ also denotes the coordinate of the parameter named `p`. A modular model reuses the declaration’s recorded calibration sources at every occurrence ([Modularity](./APPX-H-MODULARITY.md) §1). Age and other quantities that vary between repeated uses are field arguments; a fixed table or function may be read at age. The package also permits positional calibration in a nonmodular recipe.

**Derived parameters.** A **derived parameter** is a name defined by a line `q := e` without arguments, where `e` is a formula whose value is a number, written from parameters, derived parameters and numbers. It is a declared quantity, whose declared set $D$ is the set written on its definition, as in `q : D := e`, or $\mathbb{R}$ where none is written. The language refuses a cycle among definitions, so the name denotes a function $\theta\mapsto e(\theta)$ of the parameters, where the formula has a value. `Parameter` is the kind whose carrier holds the parameters and the derived parameters of a stage.

**The admissible set.** Each declaration of a parameter and each definition gives one condition on $\theta$. The declaration of parameter $j$ gives $\theta_j\in D_j(\theta)$, where $D_j$ is its declared set, the intersection of the sets that its type writes (§3). A definition `q := e` gives the condition that $e(\theta)$ has a value and lies in $D(\theta)$, where $D$ is the declared set of `q`. A condition holds at $\theta$ only if every expression in it has a value there. The **admissible set** $\Theta$ holds the vectors of $\Theta_0$ at which every condition holds, and a **calibration** is a point $\bar\theta$ of $\Theta$. The parameters of a file thus always have one joint admissible set (P9 and P10, §7).

**Implicit restrictions.** The condition of a definition is an **implicit restriction** on the parameters that its formula reads. A condition on several parameters is written in the declared set of one of them, as `Γ : (0, R)` writes $0<\theta_\Gamma<\theta_R$ (§8, case 2), or as an implicit restriction. With `α : ℝ` and `β : ℝ`, the line `q : (1, inf) := α*β` requires $\theta_\alpha\theta_\beta>1$, and a formula held at one value is written with a set of one member, as in `q : [1, 1] := e`.

**The formula of a definition.** The formula of a definition may call `log` and `exp`, each of one argument, and `min` and `max`, each of one argument or more, since the least and the greatest of finitely many numbers are numbers. It may also be written **by cases**, as `if c then e₁ else e₂`: the test `c` compares two formulas by one of $<$, $\le$, $=$, $\ge$ and $>$, and each of the two branches `e₁` and `e₂` is a formula, a further formula by cases, or an infinity, written `inf` or `-inf`. A formula by cases is one expression. Its value at $\theta$ is the value of the branch that the test chooses there, $e_1(\theta)$ where `c` holds at $\theta$ and $e_2(\theta)$ where it does not, and it has a value at $\theta$ where the two sides of the test and the chosen branch have one. The sentence of the admissible set, that a condition holds at $\theta$ only if every expression in it has a value there, is therefore not read as requiring a value of the branch that the test does not choose. A branch written as an infinity has that infinity as its value, which is a number, because the numbers form the extended real line (§2). An infinity is a value of a derived parameter only where its declared set holds it, because the condition of a definition requires $e(\theta)\in D(\theta)$: $\mathbb{R}$, the declared set of a definition that writes none, holds neither infinity.

**Settings.** A methods file $m$ may define derived parameters ([Methods](./06-Methods.md) §6), and $\Theta'_m\subseteq\Theta$, the **admissible set** of the stage with the methods file $m$, holds the $\theta$ at which their conditions hold too. A **setting** is a name that a methods file declares with a set and that no line defines, as in `n_a : ℕ`. A grid word names settings for its bounds and its counts. A bound may also be the sum of a supplied constant and a setting, as `L + extra_grid`; this selects a grid at each supplied `L`.

The value of a keyword argument of a method word, an argument written `key=value`, is the name of a setting, a quoted string or a word with arguments of its own ([Methods](./06-Methods.md) §§4 and 5). Neither word writes a literal numerical setting. Configuration supplies settings, while continuation input supplies any constant named by a grid. The latter is not a calibration or a setting.

The conditions on the settings are their declared sets, which may name parameters, and the conditions that each word puts on its arguments, such as a count of at least two. A condition that a grid word puts on a bound that reads a supplied constant (§5), that the bounds stand in order inside the declared set of the coordinate, is no condition on the settings alone: it holds or fails at each supplied value, and it is judged where the grid is constructed at that value. With $\Xi_0$ the product of the ambient sets of the settings, their admissible set is a **family** $\Xi_m(\theta)\subseteq\Xi_0$, one set for each $\theta\in\Theta'_m$, and a **configuration** is a point $\xi$ of $\Xi_m(\bar\theta)$ at a calibration $\bar\theta\in\Theta'_m$. `Setting` is the kind whose carrier holds the settings of a methods file.

<a id="2-the-field-type-system-step-by-step"></a>

## 5 Fields and the objects of a stage

A **perch** is one of the three information sets of a stage, arrival, decision and continuation, written $\prec$, $\sim$ and $\succ$, each a $\sigma$-algebra called the **information of the perch** ([Stages and perches](./03-Stages%20and%20perches.md) §3).

**Step 1 (The kind of fields).** A **field** is a declared random quantity of a stage. Let $F$ be the set of the fields that a stage declares, and let `Field` be the kind with carrier $F$. A **shock** is a field with a law, and $F_{\mathrm{loc}}\subseteq F$ is the set of the fields other than shocks. A field in $F_{\mathrm{loc}}$ denotes a random variable with values in its declared set, measurable with respect to the information of its perch, and a shock denotes a random variable with its declared law.

**Step 2 (The classifiers).** The role classifier is defined on $F$. Its values are state, control, value, shock and multiplier, with the discrete order. A multiplier belongs to a constraint. The perch classifier is defined on $F_{\mathrm{loc}}$:

$$
\mathrm{perch}:F_{\mathrm{loc}}\to\{\prec\le\sim\le\succ\}.
$$

It gives the earliest perch from which a field is known. A **listing** is one appearance of a field's name on a side of a block header. Each listing of a state or value stands at the perch of its header side, or of its mark `[<]`, `[~]` or `[>]` where the side has no perch word. A word and mark on one listing must agree. One listing is excepted from both sentences: a constant that the stage takes in at its continuation perch, listed among the inputs of a forward block, stands at the continuation perch whatever the perch word of that side, as `age[>]` does on the decision side of `dcsn_to_cntn`. A forward block lists no value-type field that a backward block of the same stage writes: the builder of that backward block composes with the forward block's law (§6), and it would then read the field that it defines. A field may be known earlier than its listing.

Two bare listings of one name on opposite sides of a block denote one **kept field** when the output writes no mark or set and no equation defines it. The header then keeps that field unchanged. Otherwise, the listings denote distinct fields. A control has the decision perch as its classification; a shock has no perch classification. For the dependence of another field, however, the action as a coordinate of the history counts as chosen after decision.

The **dependence** of a state or value-type field is the set of state coordinates that its value and domain may read. Forward equations determine the **origins** of a state: arrival coordinates, shocks and the choice. A value-type field has the origins of its dependence. The origins classifier takes subsets of these origins, ordered by inclusion. A field is known from continuation if its origins include the choice or a post-decision shock; from decision if they otherwise include a pre-decision shock; and from arrival otherwise. The **dependence judgment** derives, for the right side of an equation at a perch, the set of names on which it depends. It replaces a field listed at the next perch by what the forward equations of the state coordinates in its dependence read, the shocks of an expectation by what their laws read, and the control by the decision state coordinates where the equation is evaluated at a policy; a formula by cases depends on what its comparison and both branches depend on. An equation satisfies the judgment when the state coordinates so derived lie in the dependence of the field that it defines, which is empty for a constant. A kept field, which no equation defines, satisfies it when the forward block between the same perches keeps every state coordinate of its dependence. P12 states the conditions under which the judgment is sound.

The declared-set classifier gives a field $f$ its set $D_f$, intersecting the sets written at its declaration and listings. It may depend on parameters. Where one block writes a field on one set and another reads it on another, the written set must lie in the read set. This directed condition is additional to intersection: a field written on $\mathbb R_{++}$ may be read on $\mathbb R_+$, but the reverse is refused. Connections compare their paired fields in the same direction (§6).

The **constancy classifier**, on state and value-type fields, has the ordered values constant ≤ general. Its constant class consists of fields with empty dependence in both their value and their domain. A **constant** is thus the same at every state of its perch. The word `!cnst` names this class, as in `L : (-inf, ξ_min] @ !vlu @ !cnst`. Constancy is independent of the declared set: the value may be a number, a table or a measurable function on a continuous set. The language admits the word `!cnst` on a value-type field alone and refuses it on a field of another role, as on a state.

**Step 3 (The component sorts).** For a perch $p$, $\mathrm{PerchField}[p]$ names the class $\{f:\mathrm{perch}(f)\le p\}$. The resulting sorts are nested:

$$
\mathrm{ArrivalField}\subseteq\mathrm{DecisionField}\subseteq\mathrm{ContinuationField}.
$$

For a role $r$, $\mathrm{RoleField}[r]$ names the fiber $\mathrm{role}^{-1}(r)$. The five role sorts are `StateField`, `ControlField`, `ValueField`, `ShockField` and `MultiplierField`. A role word names one of these; a perch word names the class at that perch; `!cnst` names `ConstantField`. A header's perch word classifies its listed states and values, not its controls or shocks. A law supplies the shock role, and a multiplier's equation supplies its role. Any other field with no role word is a state.

A fixed function-valued constant has empty dependence. Its evaluation `f(a)` has the dependence of `a` and is measurable wherever the fixed function and its argument are measurable. This asserts no joint measurability over the whole set of function values.

**Step 4 (The order by declared set).** Since $\mathbb{R}_{++}\subseteq\mathbb{R}_+\subseteq\mathbb{R}$, P3 gives $\mathrm{Dom}[\mathbb{R}_{++}]\subseteq\mathrm{Dom}[\mathbb{R}_+]\subseteq\mathrm{Dom}[\mathbb{R}]$. These inclusions follow from the conditions of the sorts (D5), and no declaration states them.

**Step 5 (Combined field sorts).** For a perch $p$, a role $r$ and a set $D$,

$$
\mathsf{Field}[p,r,D]
:=\mathrm{PerchField}[p]\wedge\mathrm{RoleField}[r]\wedge\mathrm{Dom}[D]
$$

is the intersection sort of D7. A field $f$ with perch $p$, role $r$ and declared set $D_f$ is a member of $\mathsf{Field}[p,r,D_f]$, the least of these sorts that contains it (P4, §7); for a shock the perch factor is absent. The type written at one place of $f$ names a sort that contains this one: `c : !ctrl @ ℝ₊₊` names $\mathrm{ControlField}\wedge\mathrm{Dom}[\mathbb{R}_{++}]$ (§8, case 1), and Step 2 places `c` at the decision perch.

**Step 6 (The objects of a stage).** Following [Stages and perches](./03-Stages%20and%20perches.md) §1.1, write $\mathsf{A}$ for the action space of a stage, $\Gamma$ for its **feasibility correspondence**, which gives each point $x$ of the decision state space (§6) the set $\Gamma(x)\subseteq\mathsf{A}$ of feasible actions, and $(\mathsf{Z}_\zeta,\mu_\zeta)$ and $(\mathsf{Z}_\eta,\mu_\eta)$ for the shock spaces with their laws, before and after the decision. A **feasible pair** is such a point $x$ with an action $a\in\Gamma(x)$. The **laws of motion** are $g_\prec$ and $g_\succ$. The first sends an arrival state and shock $\zeta$ into the decision state space. The second gives a continuation state at each pair and shock where its equations are defined and satisfy the continuation declared sets. The index set in §6 uses precisely these forward conditions.

For the scalar specialization below, the **aggregators** $G_\prec$ and $G_\succ$ are pointwise maps into the **value line** $\mathsf L$, the declared set of the value field. The map $G_\succ(w,x,a,\eta)$ combines a continuation value $w$ with a feasible pair and shock. The map $G_\prec(w,x_\prec,\zeta)$ combines it with an arrival state and shock.

The running example is the buffer-stock stage of the [illustrative example](./02-Illustrative%20example.md) §2: assets on arrival $k$, income $y$, resources $m=Rk+y$, consumption $c$ and assets after consumption $a=m-c$, with gross return $R$, utility $u$ and discount factor $\beta$. In it, $g_\prec(k,y)=Rk+y$, $g_\succ(m,c)=m-c$, $G_\succ(w,m,c)=u(c)+\beta w$ and $G_\prec(w,k,y)=w$. Five kinds hold the objects that a stage constructs: `Function`, `Measure`, `Operator`, `Grid` and `Method`. The table lists each object of the account.

| Object | Kind | Meaning | Declaration | Type, sort or rank |
|---|---|---|---|---|
| field | `Field` | a random variable at a perch (Step 1) | a listing on a header side, `(m : Xm) : !dcsn`; for a multiplier, a line of a block's body | role, declared set, earliest perch and origins; optional constancy (Step 2) |
| shock | `Field` | a random variable with its declared law | `y : Y` with `y ~ LogNormal(μ_y, σ_y)` | a set; its law is stated on a line of its own |
| parameter | `Parameter` | one coordinate of the parameter vector | `β : (0,1)` | sets |
| derived parameter | `Parameter` | a function of the parameter vector | `q : (0,1) := (β*R)^(1/ρ)/R` | its declared set: the set written on its definition, or $\mathbb{R}$ where none is written (§4) |
| setting | `Setting` | a value that a method or a grid reads | `n_a : ℕ` in a methods file | a set |
| function | `Function` | a map between sets, such as a law of motion, a value function or a policy | `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`; none for a value function or a policy | the sets of its arguments; for a value function or a policy, a sort of the operator signature (§6) |
| measure | `Measure` | a finite measure on the state space of a perch; a probability measure is one of mass one (§6) | none | a sort of the operator signature (§6) |
| operator | `Operator` | a partial map on representing-function tuples or measures, at each admissible calibration and any supplied forward constant; the member of `Operator` is the occurrence that denotes it (§6) | a block, `[id=cntn_to_dcsn, … -> …] { … }`, for a builder, and a line of it for each operation | its rank (§6), and in a methods file its method label and its grid label |
| grid | `Grid` | a finite subset, with its inclusion, of the domain of a function that an operator stores or evaluates, which may be the set of feasible pairs ([Methods](./06-Methods.md) §5) | none; a grid word names one at a configuration and at any supplied constant it reads | none |
| method | `Method` | the rule by which an operator is computed | none; a method word names one | none |
| perch | no kind: a value of the perch classifier | an information set | a perch word or a perch mark (Step 3) | none |

**The grids form a kind of their own.** A grid is a member of the carrier of `Grid` and is no sort. Its points lie in the domain of a function, but it is a member of no sort of another kind (D4), and its inclusion in the domain states no order between sorts (D5). A function given only on a grid is a function on the domain only through a method that extends it, such as an interpolant ([Methods](./06-Methods.md) §5). A discrete set that a stage declares, such as a set of housing sizes, is the declared set of a field and no grid.

<a id="signature-versions-and-operators"></a>

## 6 The operators of a stage

A second construction gives a stage two signatures in the sense of D1.

The running example is the buffer-stock stage of §5, Step 6.

**The state of a perch.** The **state of a perch** is the tuple of the state fields listed at the perch. A kept state may therefore be a coordinate at several perches. A constant value-type field is not a state coordinate. A **joint restriction** is a condition that a stage states on several of those fields together. The **state sort** of the perch is the sort of the tuples whose coordinate for each of those fields lies in every set written for the field (§5, Step 2) and which satisfy every joint restriction. Where each field has one written set and the stage states no joint restriction, the product of those set expressions names the state sort.

The carrier of the state sort at $\theta$ is the **state space** $\mathsf{X}_p$ of the perch $p$: the product of the declared sets of those fields, or the subset of that product on which every joint restriction holds ([Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) §2).

The state, action and shock spaces of a stage are taken with the measurable structure of [Stages and perches](./03-Stages%20and%20perches.md) §1.1. In the example, suppose the stage names its sets, `Xa := ℝ₊` for assets and `Xm := ℝ₊₊` for resources. Then the states $k$ and $a$ have the state sort `Xa`, and the state $m$ has `Xm`.

**The state signature.** The state signature has the state sorts as its sorts and the two transitions as its symbols. The arrival transition uses $g_\prec$ and its shock law. The decision transition uses $g_\succ$, its shock law and the action. Its **index set** is

$$
\Pi=\{(E,\pi):E\subseteq\mathsf X_\sim\text{ measurable},\
\pi:E\to\mathsf A\text{ measurable},\
g_\succ(x,\pi(x),\eta)\in\mathsf X_\succ\text{ almost surely for every }x\in E\}.
$$

The decision forward block alone determines this set. A tuple of continuation fields does not redefine it unless a forward line or its shock law reads a supplied constant. In that case the index set is formed at that value too. An index is a **policy of the stage** at a supplied tuple when its domain is the admissible decision set and its chosen action has choice value above $-\infty$ there, as defined below. A block's policy rule may be maximizing, implicit or explicit.

A forward block consists of its header and equations. Its header alone specifies a kept coordinate. A stage is **degenerate** between two perches when it has neither the forward nor the backward block between them. Those perches are then one perch, with no intervening edge. For example, a stage with only the decision transition has its arrival and decision perch identified.

**Terms and the free category.** A **directed graph** has vertices and edges, each edge with a source and a target. The **graph of a signature** whose symbols have one source sort each has the sorts as vertices and the symbols as edges, and its **graph with indices** replaces the edge of each decision symbol $o$ by one edge $(o,\pi)$ for each index $\pi$ of $o$. A **path** is a finite sequence of edges, the target of each being the source of the next, or the empty path at a vertex, and a **term** is a path in the graph with indices. A **category** has objects, arrows between them, an identity arrow at each object, and an associative composition for which the identities are units. The **free category** of a directed graph has the vertices as objects, the paths as arrows, the joining of paths as composition and the empty paths as identities (Riehl 2016, Example 4.1.13); that of a signature is the free category of its graph with indices. A **functor** sends objects to objects and arrows to arrows and preserves sources, targets, identities and composition.

**The declaration graph.** A **declaration graph** is a directed graph whose vertices are states of perches, with a **typing** that sends each vertex to a state sort and each edge to a transition whose rank runs from the sort of the edge's source to that of its target. An edge is a **decision edge** when its transition is a decision symbol, and the **graph with indices** of a declaration graph replaces each decision edge $e$ by one edge $(e,\pi)$ for each index $\pi$ of its transition. The declaration graph of a stage is the path from its arrival state through its decision state to its continuation state, with the edges $e_\prec$ and $e_\succ$ of the indexing path of [The stage term](./APPX-C-STAGE-TERM.md) §2, the path that joins the three perch indices. Its typing sends $e_\prec$ to the arrival transition and $e_\succ$ to the decision transition, so $e_\succ$ is its decision edge. A shock is integrated into the kernel of its edge (the models of a stage, below) and a control is the value of a policy, so neither is a vertex; the file declares both as fields because its equations name them. Two vertices may have one sort: the declaration graph $k\to m\to a$ of the example has three vertices, and the graph of its state signature has two.

**Algebras and models.** An algebra of a signature in a category gives each sort an object, its carrier, and each edge of the graph with indices an arrow from the carrier of its source to that of its target, as D2 does in sets. A **model** of a declaration graph does the same for its vertices and for the edges of its graph with indices, and by P11 each is one functor out of a free category. The typing turns an algebra into a model: a vertex receives the carrier of its sort, and an edge the arrow of its transition at the same index.

**Representing-function tuples.** A representing function is written on the states that its field depends on. For each value-type field $f$ listed at $p$, let $\mathsf X_{p,f}$ be the product of the sets of the state coordinates in the dependence of $f$ (§5), and let $\mathrm{pr}_f:\mathsf X_p\to\mathsf X_{p,f}$ be the projection. Choose a set $\mathsf V_{p,f}$ of measurable functions from measurable subsets of $\mathsf X_{p,f}$ into the declared set of $f$. A function $v\in\mathsf V_{p,f}$ represents the field at the state $x$ by $v(\mathrm{pr}_f(x))$. For example, with the arrival states $m$ and $l$, a value that reads $m$ alone has the type $\mathsf X_m\to\mathbb R$, and not $\mathsf X_m\times\mathsf X_l\to\mathbb R$. A constant has empty dependence: $\mathsf X_{p,f}$ is then the set with one element, and the representing function is one element of the declared set. The product

$$
\mathsf B_p=\prod_f\mathsf V_{p,f}
$$

is the carrier of a sort $\mathtt B_p$ of kind `FunctionTuple` (D3). Each coordinate supplies one field's representing function. In the one-field case this reduces to the value-function space $\mathsf V_p$ used in the scalar examples. Ordinary set products form these tuples; no categorical product in the category of all partial maps is asserted. A constant has state-independent value and domain. A kept field must depend only on coordinates that the corresponding forward block keeps.

Representing functions $f_p$ and $f_q$ at successive perches represent one unchanged field when $f_q(g(x,z,a))=f_p(x)$, or neither side has a value, on every required state, shock and action. For the maximizing problem below, required actions have choice value above $-\infty$. This pointwise condition applies to any declared value set. For scalar fields it also implies the corresponding expectation identity wherever that expectation exists. Keeping a field does not itself require expectation.

The **domain** of a field is the domain of its representing function, a subset of $\mathsf X_{p,f}$. Where the fields of a perch are compared or combined, each domain is read in $\mathsf X_p$ as its preimage under $\mathrm{pr}_f$. For a scalar extended-real field, its **effective domain** is the set where its representing function exceeds $-\infty$. These notions differ: a real-valued partial function and its extension by $-\infty$ have corresponding effective domains, but different declared sets. A connection still compares those sets.

**Admissible states.** Fix a continuation tuple $w\in\mathsf B_\succ$. The discussion in this paragraph concerns a maximizing policy rule. The **maximized field** is the unique decision field whose equation has the policy objective as its right side. Let $\mathsf D_\succ$ be the common domain of the tuple's fields, using the effective domain for the continuation field corresponding to the maximized field when it admits $-\infty$.

The **choice value** $Q_w(x,a)$ is that objective at a feasible action whose continuation state lies in $\mathsf D_\succ$ almost surely. It is $-\infty$ otherwise. On the former pairs, assume each expectation is defined and the resulting choice value is below $+\infty$. The **admissible decision set** and **admissible arrival set** are

$$
\mathsf D_\sim=\{x:\sup_a Q_w(x,a)>-\infty\},
\qquad
\mathsf D_\prec=\{x_\prec:g_\prec(x_\prec,\zeta)\in\mathsf D_\sim\text{ a.s., and the arrival value integral is finite}\}.
$$

The authored feasibility correspondence remains $\Gamma$; it may read supplied fields, and it is empty where such a required value is absent. It is not defined by $Q_w>-\infty$. A feasible action may have value $-\infty$, and if every feasible action has that value, every one attains the supremum. The domain and soundness results here assume that no feasible action has choice value $-\infty$; they make no assertion about that other case.

**A well-posed stage.** For the maximizing problem just defined, the stage is **well posed** at a parameter vector and supplied tuple under the following conditions.

1. Every declared field set has a value and is nonempty.
2. The three admissible state sets are measurable and nonempty, and a measurable policy selects actions with $Q_w(x,\pi(x))>-\infty$ throughout $\mathsf D_\sim$.
3. The arrival law of motion and each decision forward line that reads no control give values in their declared sets almost surely. Every law of motion is measurable on its stated domain.
4. The backward equations at the policy have defined integrals and give representing functions in the chosen coordinate spaces.

A maximizing policy rule additionally requires a measurable maximizer. Nonempty domains alone establish neither attainment nor measurable selection. For an implicit or explicit rule, use the domains of its equations and require a measurable feasible selected policy there. An implicit rule needs a uniquely determined policy or a stated measurable selection from its solutions. The package records these mathematical requirements; supplying a callable does not prove them.

**The models of a stage.** A **stochastic kernel** $\kappa$ from $X$ to $Y$ assigns a probability measure $\kappa(x,\cdot)$ to each $x$, measurably in $x$. Kernels on entire measurable spaces compose by integration and form a category (Fritz 2020, §4). For a kernel defined on a specified measurable subset $E\subseteq X$, a following kernel on $F\subseteq Y$ may be composed on a specified measurable subset of $E$ where $\kappa(x,F)=1$. This is **partially defined composition**. No largest measurable source set or unrestricted category of partial kernels is asserted. A functorial interpretation of all forward paths requires source sets closed under the chosen compositions.

The **forward model** interprets the arrival edge by the law of $g_\prec(x,\zeta)$ and a decision edge at $\pi$ by the law of $g_\succ(x,\pi(x),\eta)$. The **model of laws** interprets a perch by the set $\mathsf M_p$ of finite measures on $\mathsf X_p$. A kernel on $E$ gives the partial map

$$
\mu\longmapsto\int_E\kappa(x,\cdot)\,\mu(\mathrm dx),
\qquad \mu(X\setminus E)=0.
$$

It preserves mass where defined, hence sends probability laws to probability laws. Compositions require the corresponding support conditions.

The **backward model** interprets the reversed declaration graph in sets and partial maps. A partial map has a specified domain, and the domain of a composite is the first domain intersected with the preimage of the second (Riehl, §1.3, p. 22). It sends perch $p$ to $\mathsf B_p$, the arrival edge to $\mathbb T_\prec:\mathsf B_\sim\rightharpoonup\mathsf B_\prec$, and the decision edge at $\pi$ to $\mathbb T_{\succ,\pi}:\mathsf B_\succ\rightharpoonup\mathsf B_\sim$. Each backward equation gives its coordinate's representing function; every decision equation is read at the same action $\pi(x)$. The map is defined only where all its required coordinates have values and the resulting tuple belongs to the target carrier. By P11 these edge maps extend uniquely to a functor on the opposite free category.

**Kernels at supplied constants.** A forward line or shock law that reads a constant selects a kernel at the supplied value. The forward model and the model of laws are therefore families over those values and the calibration. The backward tuple already contains the constant; its equations use the selected kernel.

A forward map on pairs also requires a specified update of the constant. For age, an authored update $a\mapsto a+1$ gives $(a,\mu)\mapsto(a+1,\mathbb M_a\mu)$. A general backward update need not have an inverse.

At fixed policies and supplied constants, the push-forward and transition expectation satisfy $\langle\mathbb M_a\mu,f\rangle=\langle\mu,E_af\rangle$ for $f$ integrable under $\mathbb M_a\mu$. For a finite horizon with bounded rewards and terminal value, let $v_a=r_a+\beta_aE_av_{a+1}$, $\mu_{a+1}=\mathbb M_a\mu_a$, $b_0=1$ and $b_{a+1}=b_a\beta_a$, with finite nonnegative discounts. Then

$$
\sum_{k<a}b_k\langle\mu_k,r_k\rangle+b_a\langle\mu_a,v_a\rangle
$$

is independent of $a$: replacing its last term by the recursion gives the expression at $a+1$. This pairs transition expectation with push-forward. Reward aggregation and policy selection are additional operations; the Bellman operator is not this adjoint.

**Builders and the operator signature.** The four edge builders are $\mathbb T_\prec$, $\mathbb T_{\succ,\pi}$, $\mathbb M_\prec$ and $\mathbb M_{\succ,\pi}$. The **policy builder** is a partial operator $\mathsf B_\succ\rightharpoonup\Pi$ returning the one policy $\pi_w$ defined by the authored rule. It is the image of no edge. A maximizing rule selects a measurable maximizer of $Q_w$; other rules need not maximize.

The **decision builder at the selected policy** is $w\mapsto\mathbb T_{\succ,\pi_w}w$. Where the policy rule maximizes, call it the **optimizing decision builder** $\mathbb T_\succ$. Its maximized coordinate is $x\mapsto\sup_{a\in\Gamma(x)}Q_w(x,a)$, and every other coordinate is its authored equation at $\pi_w(x)$. There is no separate maximization of the other fields. Thus

$$
\mathbb T_\succ w=\mathbb T_{\succ,\pi_w}w
$$

where the required maximizer and resulting tuple exist. For an implicit or explicit policy rule the same evaluation at $\pi_w$ defines the selected-policy builder, without a claim of optimality.

The **operator signature** has sorts $\mathtt B_p$ of `FunctionTuple`, sorts $\mathtt M_p$ of `Measure`, and a policy sort of `Function` with carrier $\Pi$. Its symbols are the edge builders and the policy builder, together with selected-policy evaluation. Their ranks follow their displayed sources and targets. These are partial operators; a composed term is defined only where each successive operation is defined. The scalar value-function signature in the examples is their one-field specialization.

**The operators of a stage.** At a fixed policy the backward stage operator and the forward stage operator are

$$
\mathbb T_\pi=\mathbb T_\prec\circ\mathbb T_{\succ,\pi},
\qquad
\mathbb M_\pi=\mathbb M_{\succ,\pi}\circ\mathbb M_\prec.
$$

They interpret the corresponding paths where their compositions are defined. Under a maximizing policy rule, the **Bellman operator** is $\mathbb T=\mathbb T_\prec\circ\mathbb T_\succ$. At a tuple $w$ with selected maximizer $\pi_w$, it equals $\mathbb T_{\pi_w}w$. It is not the interpretation of one fixed path: policy selection is formed outside the fixed-index models. A stage with an implicit or explicit rule instead gives the stage operator at its selected policy.

For the scalar buffer-stock example,

$$
(\mathbb T_{\succ,\pi}v)(m)=u(\pi(m))+\beta v(m-\pi(m)),
\qquad
(\mathbb T_\prec v)(k)=\mathbb E_y[v(Rk+y)].
$$

Additional fields are additional tuple coordinates, with their own equations and domains.

**Operations inside a builder.** A builder composes operations such as pullback, aggregation, expectation and evaluation. A **semgraph** records these operations as boxes and their inputs and outputs as wires. An operation may read several tuple coordinates or read one twice. For total operations on stated carriers, a signature with such products has its usual finite-product term interpretation (Jacobs 1999, §2.2, Theorem 2.2.5). This does not assert a categorical-product interpretation for arbitrary partial maps. A partial expression is evaluated where its required components and operations have values; a formula by cases evaluates only its selected branch. Kernels on product spaces likewise require a specified joint law: their marginals alone do not determine that law.

**Methods and grids.** An **occurrence** is an operator at its place in the stage: one box of the semantic graph of the stage and a member of the carrier of `Operator`, which denotes a partial map on representing-function tuples or measures. Supplied constants may select the forward map. It is a builder, named by the identifier of its block, as `policy` names the policy builder, or an operation inside a builder. The method and the grid are two classifiers of `Operator` (D6), defined on the occurrences, and their values are **labels**, with the discrete order.

A **typing entry** of a methods file, whose type is a method word or a grid word, places one occurrence in a class and declares no object: `policy.method : !egm` asserts that the occurrence `policy` has the method label `!egm`. The pair of the two values is the label of the occurrence. A classifier whose entries do not name an occurrence gives it a value that names nothing, and the pair of two such values is the **identity label** ([Methods](./06-Methods.md) §2 states one exception).

A label changes no rank, and erasing the labels of a term returns the term ([Methods](./06-Methods.md) §§3 and 8). A method word names a member of `Method`. A grid word names a member of `Grid` at a configuration and at any supplied constant it reads. The labels admitted at an occurrence are those of its operation kind ([Methods](./06-Methods.md) §4), a value of a third classifier and no kind in the sense of D3.

The language also admits a method, with a grid where the method reads one, at two further places ([Methods](./06-Methods.md) §§4 and 5). The first is a **line with an identifier**, a line of a block to which the author gives a name, as `InvEuler` in [Methods](./06-Methods.md) §9. The account takes the computation that such a line states as an operator at its place and a member of `Operator`, and the two classifiers are defined on it as on an occurrence.

The second is a **declared function**, a member of `Function` that a line of a file defines, as `𝑢` in the table of §5, Step 6. A declared function is no occurrence, and a classifier is defined on part of one kind (D6), so two further classifiers, defined on the declared functions, give the method and the grid of a declared function. Their values lie among the same labels, with the same identity label.

**The versions of a stage.** A stage is **bound** by calibration, methodization and configuration. A **version** here describes the stage at given bindings; it does not imply a copied object ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §7). The wiki calls the stage as constructed the [symbolic stage](../wiki/symbolic_stage.md) and the stage with the three bindings the [specified stage](../wiki/specified_stage.md). Stage bindings admit calibration before or after methodization. The trellis factory uses calibration, methodization and configuration in that order ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §7). The **reference approximation** of an operator is the numerical algorithm that its term determines once every setting has a value ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §8).

| Version | Bindings | The Bellman operator | The forward operator at a policy |
|---|---|---|---|
| as constructed | nothing | the operators $\mathbb{T}=\mathbb{T}_\prec\circ\mathbb{T}_\succ$, at each admissible calibration, acting on the supplied fields | the operators $\mathbb{M}_\pi=\mathbb{M}_{\succ,\pi}\circ\mathbb{M}_\prec$, at each admissible calibration, supplied forward constant and policy |
| calibrated | a calibration $\bar\theta\in\Theta$ | the operator $\mathbb{T}$ at $\bar\theta$ | the family of operators $\mathbb{M}_\pi$ at $\bar\theta$, selected by supplied constants and policy |
| methodized | a methods file $m$ that types a method at one place at least, with $\bar\theta\in\Theta'_m$: a label on each occurrence | the same operator; where a method supplies the lines by which a builder is computed, those lines denote the declared builder under the condition that the stage lists ([Methods](./06-Methods.md) §9) | the same operator |
| configured | a configuration $\xi\in\Xi_m(\bar\theta)$ | the same operator; its term now determines the reference approximation $\widehat{\mathbb{T}}=\widehat{\mathbb{T}}_\prec\circ\widehat{\mathbb{T}}_\succ$, a composite where the numerical output of the approximate optimizing decision builder is a valid input of the approximate arrival builder | the same operator; at a supplied policy its term determines its reference approximation |

The computed operators also need **handlers**, the programs that compute the methods, which are no part of a term and are named by entries that type nothing ([Methods](./06-Methods.md) §7). A stage is methodized when its methods file types a method at one place at least, that is, when one of its typing entries has a method word as its type, at an occurrence, at a line with an identifier or at a declared function. A methods file that types grids alone, names handlers alone, or does both leaves the stage at the version it had. No row asserts that an approximation is close to the operator it approximates ([Semi-conjugacy](./10-semi-conjugacy.md) §3).

**Periods and the trellis.** A **period** contains stages joined by connections. A **trellis** is a diagram of periods joined by connections ([Periods and the trellis](./08-periods-and-trellis.md)). A period's parameter vector has one coordinate for each declared parameter name; two stages of that period declaring the same name share that coordinate. Their declared sets must agree wherever the language can decide agreement. The admissible parameter set imposes all their conditions. In a general trellis, the same name in different periods gives separate coordinates. A modular model instead reuses each declaration's recorded calibration sources and operator family as [Modularity](./APPX-H-MODULARITY.md) defines. Methods and settings are outside that condition; the package permits nonmodular positional bindings.

A connection adds an edge from the earlier stage's continuation state to the later stage's arrival state. It pairs state coordinates to define a map $\varphi$ in that direction and pairs value-type fields in the backward direction. A supplied field's declared set must lie in its recipient's set. Its dependence must also satisfy what the recipient requires; in particular, a constant requirement needs a constant supplier. The connection still uses the later stage's arrival perch when that perch is identified with decision in a degenerate stage.

Where the coordinate pairing satisfies the later state's joint restrictions, the forward connection is the deterministic kernel at $\varphi(x)$. The backward connection takes each supplied representing function $f$ to $f\circ\varphi$, defined on the preimage of its domain, or keeps a supplied constant. All required fields must be paired. The initial joint arrival law must give the first period's admissible arrival set mass one; separate coordinate conditions do not establish that joint condition. The terminal tuple is supplied when the model is realized, outside its trellis declaration.

**Repeated periods.** Let $Q$ be a period's declaration graph with its connection to itself added. Forgetting occurrence positions maps a finite trellis of $N$ alike periods into $Q$. Its path contains $N$ period paths and $N-1$ internal connections. At common assignments, including any supplied constants read by forward lines or laws, a model of $Q$ interprets this path by the composite of its assigned arrows (P11).

Repeated modular declarations share the family of operators. Different age inputs may select different forward kernels from that family; they need not give one fixed forward model. Backward fields remain arguments of the partial maps. At selected maximizing policies, the fixed-policy composite agrees with the backward recursion wherever all operations are defined.

The period map $\Phi$ of [Periods and the trellis](./08-periods-and-trellis.md) includes the connection to the earlier period. Thus $\Phi^N$ includes one additional connection at the earlier end. Its comparison with the finite-path interpretation requires that connection and the same domain. Policy choices generally depend on the input of $\Phi^N$, so no single fixed-index path is asserted.

<a id="3-propositions"></a>

Repeated occurrences may be constrained to use one parameter assignment for their common declaration. [Modularity](./APPX-H-MODULARITY.md) defines this restriction together with equality of the declared operator interpretations.

## 7 Propositions

**P1 (Partitions on the stated domains).** The role classifier partitions $F$, and the fibers of the perch classifier partition $F_{\mathrm{loc}}$: each classifier gives each member of its domain exactly one value. Its ordered classes need not be disjoint. ∎

**P2 (No inhabited common subsort of disjoint fibers).** Let $i\ne j$ be values of one classifier $c$ with the discrete order. Then $R_c[i]\cap R_c[j]=\varnothing$, because a common member $x$ would have $c(x)=i$ and $c(x)=j$, and a sort $s$ below both fibers has $A_s=\varnothing$ (D5). ∎

> **Corollary.** An inhabited sort cannot lie below two distinct role fibers. The perch classes are nested. The value fields known from perch $p$ or earlier form $\mathrm{ValueField}\wedge\mathrm{PerchField}[p]$, a set of declared quantities and not the value space $\mathsf{V}_p$.

**P3 (Class inclusions by declared set).** If $D\subseteq D'$, then $\mathrm{Dom}[D]\subseteq\mathrm{Dom}[D']$, because $D_x\subseteq D$ gives $D_x\subseteq D'$. The inclusion is strict exactly when some $x$ lies in $\mathrm{Dom}[D']\setminus\mathrm{Dom}[D]$. ∎

**P4 (Combined constraints).** The carrier of $\mathsf{Field}[p,r,D]$ is

$$
\{f\in F_{\mathrm{loc}}:\mathrm{perch}(f)\le p,\ \mathrm{role}(f)=r,\ D_f\subseteq D\}.
$$

For a field $f$, the choices $p=\mathrm{perch}(f)$, $r=\mathrm{role}(f)$ and $D=D_f$ give the least such carrier containing it. Any admitting perch is at least $p$, and any admitting declared set contains $D_f$. The classifiers need not be independent. ∎

**P5 (Arrival is a subsort of the sort of all fields).** The condition of `ArrivalField` implies the condition that every member of $F$ satisfies, so by D5 the sort lies below the sort interpreted by $F$, and no declared inclusion is needed. ∎

**P6 (A field and its representative are distinct objects).** Let $\mathrm{V}_\succ$ be a value field at continuation information with the declared set $\mathsf{L}$, a random variable with values in $\mathsf{L}$. When it is measurable with respect to $\sigma(\mathrm{X}_\succ)$, the information generated by the continuation state $\mathrm{X}_\succ$, it has a measurable representing function $v_\succ$ on its stated measurable domain in $\mathsf X_\succ$ with $\mathrm{V}_\succ=v_\succ(\mathrm{X}_\succ)$ almost surely ([Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) §1.2). Where the field depends on some coordinates of the state alone, $v_\succ=v\circ\mathrm{pr}_f$ for the function $v$ of §6 on those coordinates. The state is assumed to lie in that domain almost surely. The representation implies no square integrability and fixes no values of $v_\succ$ outside the law of the state. For a non-scalar field this factorization requires a codomain for which the measurable factorization theorem applies; function-valued constants are treated at fixed supplied functions. ∎

**P7 (Measures form a kind of their own).** `Measure` is one of the kinds that the account fixes (D3), so by D4 no sort of measures is compared with a sort of another kind. This follows from the choice of the kinds, not from a claim that measures cannot be represented as functions. The forward builders pair with the integrals of functions against the kernels, the transition expectations of [Stages and perches](./03-Stages%20and%20perches.md) §2.7, and not with the backward builders, which also apply the aggregators. ∎

**P8 (Classes).** Let $c$ be a classifier with values in $I$, and let $i,j\in I$. (a) If $i\le j$, then $R_c[i]\subseteq R_c[j]$. (b) If $i$ and $j$ have a greatest lower bound $i\wedge j$, then $R_c[i]\cap R_c[j]=R_c[i\wedge j]$. (c) If $i$ and $j$ have no common lower bound, then $R_c[i]\cap R_c[j]=\varnothing$. (d) If $\ell$ is an upper bound of $i$ and $j$, then $R_c[i]\cup R_c[j]\subseteq R_c[\ell]$, and for a least upper bound $\ell=i\vee j$ the inclusion is strict exactly when some $x\in\operatorname{dom}(c)$ has $c(x)\le i\vee j$ with neither $c(x)\le i$ nor $c(x)\le j$.

Part (a) holds because $\le$ is transitive. For (b), $c(x)\le i$ and $c(x)\le j$ hold together exactly when $c(x)$ is a lower bound of $i$ and $j$, which is the condition $c(x)\le i\wedge j$. For (c), a member $x$ of both classes would make $c(x)$ a common lower bound of $i$ and $j$. For (d), the inclusion follows from (a), and $x$ lies in $R_c[i\vee j]$ and in neither $R_c[i]$ nor $R_c[j]$ exactly under the stated condition. P3 is part (a) for the order of inclusion, and P2 is part (c) for the discrete order. ∎

**P9 (The admissible set, one coordinate at a time).** Number the parameters in any order and expand the definitions. Attach each condition to the last parameter that it names, and a condition that names none to the first. Let $D'_j(\theta_1,\ldots,\theta_{j-1})$ be the set of the values $t$ of parameter $j$ at which every condition attached to it holds at $(\theta_1,\ldots,\theta_{j-1},t)$. Then

$$
\Theta=\{\theta\in\Theta_0:\theta_j\in D'_j(\theta_1,\ldots,\theta_{j-1})\ \text{for every } j\},
$$

the **iterated dependent sum** of the sets $D'_j$: the vectors built one coordinate at a time, each from a set that depends on the earlier coordinates (Jacobs 1999, §0.2, p. 16, and §10.3, p. 602). If each declared set $D_j$ names only the parameters before $j$, then $D'_j\subseteq D_j$. If no set names a parameter and no definition's condition excludes a point of the product of the declared sets, $\Theta$ is that product.

By §4, $\Theta$ holds the vectors at which every condition holds. A condition depends only on the coordinates that it names, none later than the one it is attached to, so the conditions attached to parameter $j$ hold or fail at $(\theta_1,\ldots,\theta_j)$ alone, and grouping the conditions by $j$ gives the display. If $D_j$ names only earlier parameters, the declaration of parameter $j$ is attached to $j$ and is one of the conditions that define $D'_j$. If no set names a parameter, the declarations hold exactly on the product of the declared sets, where by supposition every definition's condition holds. ∎

**P10 (Conditions intersect).** With the list of parameters fixed, each condition defines a subset of $\Theta_0$, and $\Theta$ is the intersection of these subsets (§4). Hence the order of the lines does not matter, a condition implied by the others changes nothing, and conditions that contradict each other leave $\Theta$ empty, so that no calibration exists. ∎

When two parameter sets name each other, the display of P9 and P10 still hold, and only the inclusion of $D'_j$ in $D_j$ is lost.

**P11 (Functors out of a free category).** Let $Q$ be a directed graph and $\mathsf{C}$ a category. Let $\chi$ give each vertex $j$ of $Q$ an object $\chi(j)$ of $\mathsf{C}$ and each edge $e$ from $j$ to $i$ an arrow $\chi(e):\chi(j)\to\chi(i)$. Then exactly one functor from the free category of $Q$ to $\mathsf{C}$ agrees with $\chi$ on the vertices and on the edges, each edge taken as a path of one edge.

A functor $H$ that agrees with $\chi$ sends the path $e_1,\ldots,e_n$ to $\chi(e_n)\circ\cdots\circ\chi(e_1)$, because it preserves composites, and the empty path at $j$ to the identity of $\chi(j)$, because it preserves identities; so at most one exists. Conversely, these two formulas define a functor: the composite is defined because the target of each edge is the source of the next, and the join of two paths goes to the composite of their images because composition in $\mathsf{C}$ is associative and each identity is a unit (Riehl 2016, Example 4.1.13). ∎

**P12 (Soundness of field dependence).** Consider an unbranched stage with both forward blocks, at fixed parameters and supplied constants. Assume its maximizing problem has no feasible action of choice value $-\infty$. Suppose that:

1. Every supplied field and derivative read by a line has a measurable representing function, with measurable domain, on its declared dependence.
2. Every line is jointly measurable in its remaining arguments and has values throughout their declared sets.
3. The arrival transition and each decision forward equation independent of the control lie in their declared sets almost surely.
4. Every integral is finite wherever its integrand has a value almost surely.

If every equation and kept field satisfies the dependence judgment, every value-type field has the claimed representing function at every policy of the stage.

The judgment substitutes a later field's dependence through its authored forward equations. Expectation replaces integrated shocks by the dependence of their laws; policy evaluation replaces the choice by the decision state's coordinates. Ordinary composition preserves measurability. A kept field uses only kept coordinates; a constant has no state dependence. In a formula by cases, the dependence is the union of comparison and branch dependencies, but the domain requires values only of the comparison and selected branch. Measurable restriction and selection preserve measurability there. Applying these rules in the finite order of the equations proves the claim. Repeating the argument backward proves it for a period with compatible connections and admissible terminal data. A maximizing recursion also requires the measurable maximizers and output-set conditions stated in §6. ∎

<a id="worked-cases"></a>

## 8 Worked cases

1. `c : !ctrl @ ℝ₊₊`, for a name that a block header lists. The name is a field. The component `!ctrl` names the sort `ControlField`, and `ℝ₊₊` names $\mathrm{Dom}[\mathbb{R}_{++}]$ (§5, Step 3). The type names their intersection (D7), the line asserts that `c` is a member of it (D4), and `c` is at the decision perch wherever a header lists it.
2. `Γ : (0, R)`, where `Γ` is a growth factor and not the feasible correspondence of §5. The name is a parameter, and the line gives the condition $\theta_\Gamma\in(0,\theta_R)$. With `R : ℝ₊₊` numbered first, P9 gives the pairs with $\theta_R\in\mathbb{R}_{++}$ and $0<\theta_\Gamma<\theta_R$.
3. `β : ℝ₊₊ @ (0, ρ)`. Two sets in one type name $\mathrm{Dom}[\mathbb{R}_{++}\cap(0,\theta_\rho)]$ at each $\theta$ (§3), and the line gives the one condition $0<\theta_\beta<\theta_\rho$.
4. `q : (0,1) := (β*R)^(1/ρ)/R`. The line defines `q` and requires $(\theta_\beta\theta_R)^{1/\theta_\rho}/\theta_R$ to have a value in $(0,1)$, an implicit restriction on `β`, `R` and `ρ` (§4). Suppose the file also declares `R : ℝ₊₊`, `ρ : (1, inf)` and `β : (0,1) @ (0, R^(ρ-1))`. Given finite $\theta_R>0$, $\theta_\rho>1$ and $\theta_\beta>0$, the condition on `q` is equivalent to $\theta_\beta<\theta_R^{\theta_\rho-1}$, the second component of the type of `β`, so beside that line it changes nothing (P10). The converse fails: the condition on `q` does not imply $\theta_\beta<1$, since $\theta_R=1.04$, $\theta_\rho=2$ and $\theta_\beta=1.02$ give `q` near $0.990$.
5. `q := 1`. The line is a definition and restricts nothing: `q` is the constant 1, its condition $1\in\mathbb{R}$ always holds, and $\Theta$ is unchanged.
6. `ρ : (0,1) \/ (1, inf)`. The set expression denotes the union of two intervals, the line gives the condition $\theta_\rho\in(0,1)\cup(1,\infty)$, and the language admits the union because the name is a parameter (§2).
7. `n_a : ℕ` in a methods file, read by `policy.grid : !Cartesian(a=(a_min, a_max, n_a))`. The name is a setting. Its line requires its value to lie in $\mathbb{N}$, and the grid word adds conditions on $\Xi_m(\theta)$: a count of at least two, and bounds in order inside the declared set of the coordinate `a` ([Methods](./06-Methods.md) §5).
8. `policy.method : !egm`, with the grid of case 7. The entry declares no object. It types the occurrence `policy`, the policy builder, whose rank runs from $\mathtt B_\succ$ to the sort of policies (§6): its method label is `!egm`, its grid label is the grid word, and neither changes the rank.
9. `q : ℝ_{+∞} := if α > 0 then 1/α else inf`, with `α : ℝ₊`. The formula has value $1/\alpha$ where $\alpha>0$ and $\infty$ at zero. The unselected quotient is not evaluated. Its declared set admits both results, while an omitted declared set would mean $\mathbb R$ and exclude the infinite branch. This example concerns arithmetic by cases, not an economic restriction.

<a id="4-worked-example--buffer-stock"></a>

**The buffer-stock stage.** The table gives the sort of each field of the buffer-stock stage of §5, Step 6, as [Field types](./catalogues/fields.md) §2 lists the fields.

| Field | Sort |
|---|---|
| $k$, assets on arrival | $\mathrm{ArrivalField}\wedge\mathrm{StateField}\wedge\mathrm{Dom}[\mathbb{R}_+]$ |
| $y$, income | $\mathrm{ShockField}\wedge\mathrm{Dom}[\mathsf{Z}_\zeta]$, with $\mathsf{Z}_\zeta\subseteq\mathbb{R}_{++}$ |
| $m$, resources | $\mathrm{DecisionField}\wedge\mathrm{StateField}\wedge\mathrm{Dom}[\mathbb{R}_{++}]$ |
| $c$, consumption | $\mathrm{DecisionField}\wedge\mathrm{ControlField}\wedge\mathrm{Dom}[\mathbb{R}_{++}]$ |
| $a$, assets after consumption | $\mathrm{ContinuationField}\wedge\mathrm{StateField}\wedge\mathrm{Dom}[\mathbb{R}_+]$ |
| $\mathrm{V}_\succ$, continuation value | $\mathrm{ContinuationField}\wedge\mathrm{ValueField}\wedge\mathrm{Dom}[\mathsf{L}]$ |

Under the assumptions of P6, the value field $\mathrm{V}_\succ$ has a measurable representing function $v_\succ$, which lies in the value space $\mathsf{V}_\succ$ only where that space is chosen to hold it (§6). The utility function is $u:\mathbb{R}_{++}\to\mathbb{R}$. The constraint $c\le m$ and the integrability conditions of the example remain additional to these sorts.

<a id="5-remarks-and-open-questions"></a>

## 9 Remarks and open questions

- A parameter's or a setting's set that names a field has no meaning in the account, because the conditions of §4 are conditions on the parameter vector and on the settings alone, and the language refuses such a line. An endpoint that integrates a shock against its declared law is a function of $\theta$ and is admitted. A parameter's set that names a setting has no meaning in the account either.
- The perch values are ordered by information (§5). Their classes are nested, although a listing writes one perch word. Origins determine the earliest perch of a state or value-type field.
- The language admits fewer types than the account gives a meaning to. A union or a difference is not written after `:=`. It is refused in the set of a field, of a shock or of a function's argument, because a grid is checked at its two bounds, and two bounds inside a set with a gap do not place the points between them inside the set.
- Arithmetic in a block admits the extended-real operations whose results are determined: for finite $x$, $x+\infty=\infty$; for $k>0$, $k\infty=\infty$; and for $p>0$, $\infty^{-p}=0$. The first two rules hold likewise with $-\infty$: for finite $x$, $x-\infty=-\infty$, and for $k>0$, $k(-\infty)=-\infty$. A negative power of $-\infty$ has no value. Expressions such as $\infty-\infty$ and $0\infty$ have no value. An unselected case branch is not evaluated. This rule does not extend arithmetic with infinities to a declared-set bound or a declared function with a finite argument domain.
- A zero consumption computed at an EGM interpolation endpoint is a limiting value of the representation; it does not change the positive declared set of the control.
- §6 is stated for a stage with both transitions and without branches ([Branching](./09-branching.md) §1). The form of the choice value with a second map outside the integral, which an Epstein–Zin certainty equivalent needs ([Stages and perches](./03-Stages%20and%20perches.md) §2.3a), is not yet stated in the account. #todo
- The policy builder returns one policy, as §6 defines. A maximizing rule selects a measurable maximizer; an explicit or implicit rule need not maximize. Every other decision field is evaluated at that same policy. The existence of a supremum alone does not supply a policy.

<a id="6-sources"></a>

## 10 Sources

- Fritz, T. (2020). A synthetic approach to Markov kernels, conditional independence and theorems on sufficient statistics. *Advances in Mathematics* 370, 107239. Read in the arXiv version, arXiv:1908.07021.
- Goguen, J. A., and Meseguer, J. (1992). Order-sorted algebra I: equational deduction for multiple inheritance, overloading, exceptions and partial operations. *Theoretical Computer Science* 105(2), 217–273. Definitions 2.1 and 2.7 are those of the version read, Technical Monograph PRG-80, Oxford University Computing Laboratory, December 1989.
- Goguen, J. A., Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1977). Initial algebra semantics and continuous algebras. *Journal of the ACM* 24(1), 68–95.
- Jacobs, B. (1999). *Categorical Logic and Type Theory*. Studies in Logic and the Foundations of Mathematics 141. Elsevier.
- Meseguer, J. (1998). Membership algebra as a logical framework for equational specification. In *Recent Trends in Algebraic Development Techniques (WADT 1997)*, Lecture Notes in Computer Science 1376, 18–61. Read in the author's version, without the printed page numbers.
- Riehl, E. (2016). *Category Theory in Context*. Dover. Read in the author's second edition.
- Rushby, J., Owre, S., and Shankar, N. (1998). Subtypes for specifications: predicate subtyping in PVS. *IEEE Transactions on Software Engineering* 24(9), 709–720.
