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
> We state the type system of the calculus as one account. A type, such as `!ctrl @ ℝ₊₊`, classifies a field, a parameter or a setting by the conditions it writes, and the parameter lines of a file define one set of admissible parameter vectors. The state sorts and the transitions of a stage form a signature, and the models of the stage's declaration graph give each transition a stochastic kernel and two builders, one on value functions and one on measures. The Bellman operator applies the arrival builder after the optimizing decision builder, which takes a supremum over the feasible actions. Where the policy that the policy builder gives is a maximizer, the optimizing decision builder equals the decision builder at that policy.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md): the stage, its perches and its operators; [Fields, functions and types](./04-fields%2C%20functions%20and%20types.md): fields and their representing functions.
> **Used by** — Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md): the rules that give a file's text its meaning; [Stages](../Bellman-Sym/01-stage.md) §2 and [Symbols and conventions](../Bellman-Sym/reference/symbols-conventions.md) §9: what an author writes in a type; [Method types](../Bellman-Sym/reference/methods.md): the method words and the grid words; [Appendix E](./catalogues/index.md): the catalogues of the objects classified here.
> **See also** — [The stage term](./APPX-C-STAGE-TERM.md): the operator signature of a stage and its compositions; [Methods](./06-Methods.md): the method and the grid of an operator; [Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §§5 to 8: terms, calibration and the binding maps.

<a id="0-setup"></a>
<a id="the-account"></a>

## 1 The account

The type system of the calculus is **a classification of the declared quantities by predicate subtypes, and the free category of a dynamic program with its forward and backward models**. The first part says what a written type means: a **predicate subtype** is a subset that a condition picks out. The second part says what a stage means: its states and transitions form a graph, its models are functors out of free categories built on that graph, the models give each transition its builders, and the Bellman operator is formed from the builders. In the words of the literature, the second part is a many-sorted signature in which every symbol takes exactly one argument, with its meaning given by such functors (§6). Here **the account** means the definitions and the propositions of this appendix, and **the language** means what a stage file and a methods file may write.

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
| setting | a name that a methods file declares with a set; a grid word names settings, and the value of a keyword argument of a method word is the name of a setting, a number, a quoted string or a word with arguments of its own | §4 |
| family | an indexed collection, one member for each index | §4 |
| configuration | a point of the admissible set of the settings | §4 |
| field | a declared random quantity of a stage | §5 |
| shock | a field with a law | §5 |
| state of a perch | the tuple of the state fields at a perch | §6 |
| state sort | the sort of the state of a perch | §6 |
| transition | a symbol between two state sorts, as a law of motion with its shock law | §6 |
| term | a path of symbols | §6 |
| declaration graph | the states of the perches and the edges between them | §6 |
| model | an object for each vertex and an arrow for each edge | §6 |
| well posed | said of a stage, with its value spaces, where four conditions hold | §6 |
| builder | an operator that a model gives a transition; also the policy builder and the optimizing decision builder | §6 |
| occurrence | an operator at its place in a stage, one box of its semantic graph | §6 |
| label | a value of the method classifier or of the grid classifier | §6 |

<a id="sets-of-values"></a>

## 2 Sets of values

**What a file writes.** A **stage file** states a stage in declarations and **blocks**, groups of equations under a **header** whose two **sides**, before and after its arrow `->`, list what the block reads and what it writes. A **methods file** adds the numerical methods of the stage ([Methods](./06-Methods.md) §1). A **type** is the expression that a file writes after a **typing colon**, and a **declaration** is a line that introduces one name and writes its type, as `c : !ctrl @ ℝ₊₊` does. The name, with what the files state about it, is a **declared quantity**. The **components** of a type are its parts, written with `@` between them: sets, a **role word** such as `!ctrl`, or a **perch word** such as `!dcsn` (§5). In a methods file, the type of an operator's method or grid is a **method word** such as `!egm` or a **grid word** such as `!Cartesian`, with its arguments (§6). A **law** is a probability distribution, which a file states in a line such as `y ~ LogNormal(μ_y, σ_y)`.

**Ambient sets.** Every value lies in one **ambient set**: the numbers, the names of one finite set of names, the tuples of a product of ambient sets, or the functions from a finite index set to an ambient set. The numbers form the extended real line $\bar{\mathbb{R}}=[-\infty,\infty]$, with $\mathbb{R}$, $\mathbb{R}_+=[0,\infty)$, $\mathbb{R}_{++}=(0,\infty)$, $\mathbb{Z}$ and $\mathbb{N}$ inside it. The language leaves open whether $0$ lies in $\mathbb{N}$, and an author who needs the bound writes it, as in `ℤ @ [1, inf)`.

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
| set of functions | `L_J → ℝ` | the functions from a finite index set to a set |
| set with a bar | <code>H := {i : ℤ &#124; i &gt;= 0}</code>, in the definition of a named set | the members of the set after the colon that satisfy every condition after the bar |
| union | `(0,1) \/ (1, inf)` | the numbers in at least one of the sets |
| difference | `ℝ \ [0, 1]` | the numbers in the first set and outside the second |

**The algebra of subsets.** The subsets of one ambient set form a Boolean algebra: they are closed under intersection, union and complement (Jacobs 1999, §0.2, p. 12). The language writes the union of `A` and `B` as `A \/ B` and their relative difference as `A \ B`, among sets of numbers and only in the set of a parameter, of a derived parameter or of a setting (§§4 and 9). An intersection is written by listing sets as components of one type (§3), and the sign `@` is no form of a set expression. No sign stands for a complement, by choice: a difference names the set in which the complement is taken.

<a id="1-definitions"></a>

## 3 Basic definitions

**D1 (Signature).** A **signature** has a set of names called **sorts** and a set of names called **symbols**. Each symbol has a **rank**: its source sorts and its target sort. A symbol $o$ with the one source sort $t$ and the target sort $t'$ is written $o:t\to t'$. A signature may mark a symbol as a **decision symbol** and give it a set of **policies**. Without the policies this is a many-sorted signature (Goguen, Thatcher, Wagner and Wright 1977, §2, p. 70). Those authors call the source sorts with the target sort the type of the symbol; the word rank for them is that of Goguen and Meseguer (1992, Definition 2.1).

**D2 (Carrier).** A **carrier** is the set that interprets a name. A name, its carrier and a member of the carrier are three objects. An **algebra** of a signature in sets gives each sort $t$ a carrier $A_t$, each symbol of rank $t_1,\ldots,t_n\to t'$ that is no decision symbol a function $A_{t_1}\times\cdots\times A_{t_n}\to A_{t'}$, and each decision symbol one such function for each of its policies. §6 defines a category and states the same in one, where a carrier is an object of the category.

**D3 (Kind).** A **kind** is a name interpreted by a set, its carrier $K$, which holds every object of one nature. The account assigns each declared quantity, and each object that a stage constructs, to exactly one kind, and classifies it in that kind alone. No file states a kind. Each ambient set of §2 is the carrier of a kind of values. The account fixes eight further kinds where their members are defined: `Parameter` and `Setting` in §4, `Field` in §5, Step 1, and `Function`, `Measure`, `Operator`, `Grid` and `Method` in §5, Step 6. Two carriers may share a member: a function that a stage constructs on a finite set is also a member of an ambient set of functions (§2), and the account assigns it to `Function`.

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

**The sort a type names.** Each component of the type of a declared quantity names the class of one classifier at one value: a set $D$ names $\mathrm{Dom}[D]$ in the kind of that quantity, and a role word or a perch word names a fiber (§5). The type names the intersection of these sorts (D7), and a declaration asserts that its declared quantity is a member of that sort (D4). A set expression thus names two sorts: a sort of values when it stands alone, and a sort of declared quantities as a component. P8 (§7), on the intersections and the unions of classes, has three consequences. First, two components with the values $i$ and $j$ of one classifier name $R_c[i\wedge j]$ where $i$ and $j$ have a greatest lower bound $i\wedge j$, so two sets $D_1$ and $D_2$ in one type name $\mathrm{Dom}[D_1\cap D_2]$. Where the two sets have no common point this is $\mathrm{Dom}[\varnothing]$, which is empty because a declared set is nonempty, and the language refuses such a type where the written text shows it, as it refuses an interval whose written endpoints leave it empty. Second, two components whose values have no common lower bound name an empty sort. Under the discrete order any two different values are such a pair, so the language refuses two different role words in one type, or two different perch words. Third, the union of $\mathrm{Dom}[D_1]$ and $\mathrm{Dom}[D_2]$ need not be $\mathrm{Dom}[D_1\cup D_2]$. With $D_1=(0,1]$ and $D_2=(1,2)$, a quantity with the declared set $(0,2)$ lies in $\mathrm{Dom}[D_1\cup D_2]$ and in neither $\mathrm{Dom}[D_1]$ nor $\mathrm{Dom}[D_2]$. A union is therefore formed among sets of values, inside the set expression, and never with a sign between components.

<a id="parameters-and-settings"></a>

## 4 Parameters and settings

**Parameters.** A **parameter** is a name that the stage file declares with a set, with no role word, no perch word and no law, that no block header lists, that no line of a block writes and that no line defines by `:=`. Number the parameters of a file $1,\ldots,n$, and let $\Theta_0$ be the product of their ambient sets. A parameter denotes one coordinate $\theta_j$ of a **parameter vector** $\theta\in\Theta_0$, an assignment in the sense of §2, and $\theta_p$ also denotes the coordinate of the parameter named `p`.

**Derived parameters.** A **derived parameter** is a name defined by a line `q := e` without arguments, where `e` is a formula whose value is a number, written from parameters, derived parameters and numbers. It is a declared quantity, whose declared set $D$ is the set written on its definition, as in `q : D := e`, or $\mathbb{R}$ where none is written. The language refuses a cycle among definitions, so the name denotes a function $\theta\mapsto e(\theta)$ of the parameters, where the formula has a value. `Parameter` is the kind whose carrier holds the parameters and the derived parameters of a stage.

**The admissible set.** Each declaration of a parameter and each definition gives one condition on $\theta$. The declaration of parameter $j$ gives $\theta_j\in D_j(\theta)$, where $D_j$ is its declared set, the intersection of the sets that its type writes (§3). A definition `q := e` gives the condition that $e(\theta)$ has a value and lies in $D(\theta)$, where $D$ is the declared set of `q`. A condition holds at $\theta$ only if every expression in it has a value there. The **admissible set** $\Theta$ holds the vectors of $\Theta_0$ at which every condition holds, and a **calibration** is a point $\bar\theta$ of $\Theta$. The parameters of a file thus always have one joint admissible set (P9 and P10, §7).

**Implicit restrictions.** The condition of a definition is an **implicit restriction** on the parameters that its formula reads. A condition on several parameters is written in the declared set of one of them, as `Γ : (0, R)` writes $0<\theta_\Gamma<\theta_R$ (§8, case 2), or as an implicit restriction. With `α : ℝ` and `β : ℝ`, the line `q : (1, inf) := α*β` requires $\theta_\alpha\theta_\beta>1$, and a formula held at one value is written with a set of one member, as in `q : [1, 1] := e`.

**Settings.** A methods file $m$ may define derived parameters ([Methods](./06-Methods.md) §6), and $\Theta'_m\subseteq\Theta$, the **admissible set** of the stage with the methods file $m$, holds the $\theta$ at which their conditions hold too. A **setting** is a name that a methods file declares with a set and that no line defines, as in `n_a : ℕ`. A grid word names settings for its bounds and its counts, and the value of a keyword argument of a method word, an argument written `key=value`, is the name of a setting, a number, a quoted string or a word with arguments of its own ([Methods](./06-Methods.md) §§4 and 5). The conditions on the settings are their declared sets, which may name parameters, and the conditions that each word puts on its arguments, such as a count of at least two. With $\Xi_0$ the product of the ambient sets of the settings, their admissible set is a **family** $\Xi_m(\theta)\subseteq\Xi_0$, one set for each $\theta\in\Theta'_m$, and a **configuration** is a point $\xi$ of $\Xi_m(\bar\theta)$ at a calibration $\bar\theta\in\Theta'_m$. `Setting` is the kind whose carrier holds the settings of a methods file.

<a id="2-the-field-type-system-step-by-step"></a>

## 5 Fields and the objects of a stage

A **perch** is one of the three information sets of a stage, arrival, decision and continuation, written $\prec$, $\sim$ and $\succ$, each a $\sigma$-algebra called the **information of the perch** ([Stages and perches](./03-Stages%20and%20perches.md) §3).

**Step 1 (The kind of fields).** A **field** is a declared random quantity of a stage. Let $F$ be the set of the fields that a stage declares, and let `Field` be the kind with carrier $F$. A **shock** is a field with a law, and $F_{\mathrm{loc}}\subseteq F$ is the set of the fields other than shocks. A field in $F_{\mathrm{loc}}$ denotes a random variable with values in its declared set, measurable with respect to the information of its perch, and a shock denotes a random variable with its declared law.

**Step 2 (The classifiers).** Three classifiers classify the fields, the first two with the discrete order on their values. The role classifier is defined on $F$. Its five values are the roles state, control, value, shock and multiplier, a multiplier being attached to a constraint. The perch classifier is defined on $F_{\mathrm{loc}}$:

$$
\mathrm{perch}:F_{\mathrm{loc}}\to\{\prec,\sim,\succ\}.
$$

A state or a value is at the perch whose word follows the header side that lists it, or at the perch of its **perch mark**, `[<]`, `[~]` or `[>]` after its name for arrival, decision or continuation, as in `V[>]`. A control is at the decision perch wherever a header lists it: a listing on a continuation side records that the control is available there. A multiplier is at the perch of its mark. A shock is at no perch, and it may be measurable with respect to the information of a perch without being a state there. A field other than a shock is one name at one perch, so that `w` and `w[>]` are two fields. The language refuses two places that put one field at two perches, as a mark `[>]` on a name listed on an arrival side does, and two places that give one field two different role words, so role and perch are functions on their domains. The third classifier gives each field $f$ its declared set $D_f$, the intersection of the sets written for it at its places: its own declaration, and each header side that lists it with a set. The set $D_f$ may name parameters and is then the set $D_f(\theta)$, while role and perch do not depend on $\theta$. Where one block writes a field on one set and another block reads it on another, the language also requires the set written to lie in the set read at every $\theta\in\Theta$, and it requires the same of the two fields that a connection between stages pairs (§6). A field written on $\mathbb{R}_{++}$ may be read on $\mathbb{R}_+$, and the reverse is refused, although the intersection alone would give that field the declared set $\mathbb{R}_{++}$.

**Step 3 (The component sorts).** For a perch $p$, $\mathrm{PerchField}[p]$ is the sort of the fiber $\mathrm{perch}^{-1}(p)$; the three are `ArrivalField`, `DecisionField` and `ContinuationField`. For a role $r$, $\mathrm{RoleField}[r]$ is the sort of the fiber $\mathrm{role}^{-1}(r)$; the five are `StateField`, `ControlField`, `ValueField`, `ShockField` and `MultiplierField`. In a type (§3), a role word, `!state`, `!ctrl`, `!vlu` or `!shck`, names a role sort. A perch word, `!arvl`, `!dcsn` or `!cntn`, or a perch mark names the perch sort of the fields that Step 2 places at that perch. A perch word after a header side is a component of the types of the states and the values that the side lists, and of no other name on it. A control or a shock that the side lists takes no perch component there, because Step 2 places a control at the decision perch and a shock at no perch. Any type written for it at that place then names a sort to which the field belongs (Step 5). A field takes the role word written at any of its places, a field with a law is a shock, and a multiplier takes its role from the line of a block's body that declares it, with one set and no role word. Any other field without a role word is a state.

**Step 4 (The order by declared set).** Since $\mathbb{R}_{++}\subseteq\mathbb{R}_+\subseteq\mathbb{R}$, P3 gives $\mathrm{Dom}[\mathbb{R}_{++}]\subseteq\mathrm{Dom}[\mathbb{R}_+]\subseteq\mathrm{Dom}[\mathbb{R}]$. These inclusions follow from the conditions of the sorts (D5), and no declaration states them.

**Step 5 (Combined field sorts).** For a perch $p$, a role $r$ and a set $D$,

$$
\mathsf{Field}[p,r,D]
:=\mathrm{PerchField}[p]\wedge\mathrm{RoleField}[r]\wedge\mathrm{Dom}[D]
$$

is the intersection sort of D7. A field $f$ with perch $p$, role $r$ and declared set $D_f$ is a member of $\mathsf{Field}[p,r,D_f]$, the least of these sorts that contains it (P4, §7); for a shock the perch factor is absent. The type written at one place of $f$ names a sort that contains this one: `c : !ctrl @ ℝ₊₊` names $\mathrm{ControlField}\wedge\mathrm{Dom}[\mathbb{R}_{++}]$ (§8, case 1), and Step 2 places `c` at the decision perch.

**Step 6 (The objects of a stage).** Following [Stages and perches](./03-Stages%20and%20perches.md) §1.1, write $\mathsf{A}$ for the action space of a stage, $\Gamma$ for its **feasible correspondence**, which gives each point $x$ of the decision state space (§6) the set $\Gamma(x)\subseteq\mathsf{A}$ of feasible actions, and $(\mathsf{Z}_\zeta,\mu_\zeta)$ and $(\mathsf{Z}_\eta,\mu_\eta)$ for the shock spaces with their laws, before and after the decision. A **feasible pair** is such a point $x$ with an action $a\in\Gamma(x)$. The **laws of motion** are $g_\prec$, which sends a point of the arrival state space and a shock $\zeta$ into the decision state space, and $g_\succ$, which sends a feasible pair and a shock $\eta$ into the continuation state space. The **aggregators** $G_\prec$ and $G_\succ$ are pointwise maps into the **value line** $\mathsf{L}$, the set in which value functions take their values: $G_\succ(w,x,a,\eta)$ combines a continuation value $w$ with a feasible pair and a shock, and $G_\prec(w,x_\prec,\zeta)$ does the same at a point $x_\prec$ of the arrival state space. The running example is the buffer-stock stage of the [illustrative example](./02-Illustrative%20example.md) §2: assets on arrival $k$, income $y$, resources $m=Rk+y$, consumption $c$ and assets after consumption $a=m-c$, with gross return $R$, utility $u$ and discount factor $\beta$. In it, $g_\prec(k,y)=Rk+y$, $g_\succ(m,c)=m-c$, $G_\succ(w,m,c)=u(c)+\beta w$ and $G_\prec(w,k,y)=w$. Five kinds hold the objects that a stage constructs: `Function`, `Measure`, `Operator`, `Grid` and `Method`. The table lists each object of the account.

| Object | Kind | What it denotes | The line that declares it | Its type, sort or rank |
|---|---|---|---|---|
| field | `Field` | a random variable at a perch (Step 1) | a listing on a header side, `(m : Xm) : !dcsn`; for a multiplier, a line of a block's body | a role word, a set and its perch (Step 2) |
| shock | `Field` | a random variable with its declared law | `y : Y` with `y ~ LogNormal(μ_y, σ_y)` | a set; its law is stated on a line of its own |
| parameter | `Parameter` | one coordinate of the parameter vector | `β : (0,1)` | sets |
| derived parameter | `Parameter` | a function of the parameter vector | `h := 1/(1 - Γ/R)`; `q : (0,1) := (β*R)^(1/ρ)/R` | its declared set: the set written on its definition, or $\mathbb{R}$ where none is written (§4) |
| setting | `Setting` | a value that a method or a grid reads | `n_a : ℕ` in a methods file | a set |
| function | `Function` | a map between sets, such as a law of motion, a value function or a policy | `𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)`; none for a value function or a policy | the sets of its arguments; for a value function or a policy, a sort of the operator signature (§6) |
| measure | `Measure` | a finite measure on the state space of a perch; a probability measure is one of mass one (§6) | none | a sort of the operator signature (§6) |
| operator | `Operator` | at each parameter vector at which the stage is well posed, a map between sets of functions or of measures; the member of `Operator` is the occurrence that denotes it (§6) | a block, `[id=cntn_to_dcsn, … -> …] { … }`, for a builder, and a line of it for each operation | its rank (§6), and in a methods file its method label and its grid label |
| grid | `Grid` | a finite subset, with its inclusion, of the domain of a function that an operator stores or evaluates, which may be the set of feasible pairs ([Methods](./06-Methods.md) §5) | none; a grid word with its arguments names one at a configuration | none |
| method | `Method` | the rule by which an operator is computed | none; a method word names one | none |
| perch | no kind: a value of the perch classifier | an information set | a perch word or a perch mark (Step 3) | none |

**The grids form a kind of their own.** A grid is a member of the carrier of `Grid` and is no sort. Its points lie in the domain of a function, but it is a member of no sort of another kind (D4), and its inclusion in the domain states no order between sorts (D5). A function given only on a grid is a function on the domain only through a method that extends it, such as an interpolant ([Methods](./06-Methods.md) §5). A discrete set that a stage declares, such as a set of housing sizes, is the declared set of a field and no grid.

<a id="signature-versions-and-operators"></a>

## 6 The operators of a stage

A second construction gives a stage two signatures in the sense of D1. The running example is the buffer-stock stage of §5, Step 6.

**The state of a perch.** The **state of a perch** is the tuple of the state fields at the perch. A **joint restriction** is a condition that a stage states on several of those fields together. The **state sort** of the perch is the sort of the tuples whose coordinate for each of those fields lies in every set written for the field (§5, Step 2) and which satisfy every joint restriction. Where each field has one written set and the stage states no joint restriction, the product of those set expressions names the state sort. The carrier of the state sort at $\theta$ is the **state space** $\mathsf{X}_p$ of the perch $p$: the product of the declared sets of those fields, or the subset of that product on which every joint restriction holds ([Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) §2). The state, action and shock spaces of a stage are taken with the measurable structure of [Stages and perches](./03-Stages%20and%20perches.md) §1.1. In the example, suppose the stage names its sets, `Xa := ℝ₊` for assets and `Xm := ℝ₊₊` for resources. Then the states $k$ and $a$ have the state sort `Xa`, and the state $m$ has `Xm`.

**The state signature.** The **state signature** of a stage has the state sorts of its perches as its sorts and its **transitions** as its symbols, each with one source sort. The **arrival transition**, from the arrival state sort to the decision state sort, stands for the law of motion $g_\prec$ with the shock law $\mu_\zeta$. The **decision transition**, from the decision state sort to the continuation state sort, stands for $g_\succ$ with $\mu_\eta$ and the control. It is the decision symbol of the stage, and its policies are the measurable selections of the feasible correspondence $\Gamma$,

$$
\Pi_\Gamma=\{\pi:\mathsf{X}_\sim\to\mathsf{A}:\pi\text{ measurable},\ \pi(x)\in\Gamma(x)\text{ for every }x\},
$$

so that the declared control is the value $\pi(x)$ of a policy at the point $x\in\mathsf{X}_\sim$. A **forward block** is the lines of the file that state one transition, and a file with one forward block gives one transition. In the example `arvl_to_dcsn` has the rank `Xa → Xm`, `dcsn_to_cntn` has the rank `Xm → Xa`, and a policy is a measurable $\pi$ with $0<\pi(m)\le m$. The set $\Pi_\Gamma$ is formed from $\mathsf{X}_\sim$ and $\Gamma$ at a parameter vector $\theta$, so the graphs with policies below, their free categories and the operator signature are taken at each $\theta$, and a model at $\theta$ is a functor out of the free category at $\theta$.

**Terms and the free category.** A **directed graph** has vertices and edges, each edge with a source and a target. The **graph of a signature** whose symbols have one source sort each has the sorts as vertices and the symbols as edges, and its **graph with policies** replaces the edge of each decision symbol $o$ by one edge $(o,\pi)$ for each policy $\pi$ of $o$. A **path** is a finite sequence of edges, the target of each being the source of the next, or the empty path at a vertex, and a **term** is a path in the graph with policies. A **category** has objects, arrows between them, an identity arrow at each object, and an associative composition for which the identities are units. The **free category** of a directed graph has the vertices as objects, the paths as arrows, the joining of paths as composition and the empty paths as identities (Riehl 2016, Example 4.1.13); that of a signature is the free category of its graph with policies. A **functor** sends objects to objects and arrows to arrows and preserves sources, targets, identities and composition.

**The declaration graph.** A **declaration graph** is a directed graph whose vertices are states of perches, with a **typing** that sends each vertex to a state sort and each edge to a transition whose rank runs from the sort of the edge's source to that of its target. An edge is a **decision edge** when its transition is a decision symbol, and the **graph with policies** of a declaration graph replaces each decision edge $e$ by one edge $(e,\pi)$ for each policy $\pi$ of its transition. The declaration graph of a stage is the path from its arrival state through its decision state to its continuation state, with the edges $e_\prec$ and $e_\succ$ of the indexing path of [The stage term](./APPX-C-STAGE-TERM.md) §2, the path that joins the three perch indices. Its typing sends $e_\prec$ to the arrival transition and $e_\succ$ to the decision transition, so $e_\succ$ is its decision edge. A shock is integrated into the kernel of its edge (the models of a stage, below) and a control is the value of a policy, so neither is a vertex; the file declares both as fields because its equations name them. Two vertices may have one sort: the declaration graph $k\to m\to a$ of the example has three vertices, and the graph of its state signature has two.

**Algebras and models.** An algebra of a signature in a category gives each sort an object, its carrier, and each edge of the graph with policies an arrow from the carrier of its source to that of its target, as D2 does in sets. A **model** of a declaration graph does the same for its vertices and for the edges of its graph with policies, and by P11 each is one functor out of a free category. The typing turns an algebra into a model: a vertex receives the carrier of its sort, and an edge the arrow of its transition at the same policy.

**A stage well posed at a parameter vector.** The **value spaces** of a stage are three sets $\mathsf{V}_\prec$, $\mathsf{V}_\sim$ and $\mathsf{V}_\succ$, chosen in advance at each $\theta\in\Theta$ at which the state spaces have values, each a set of measurable functions from the state space of its perch to $\mathsf{L}$. A stage with its value spaces is **well posed** at $\theta\in\Theta$ when four conditions hold there. First, every field has a declared set, which has a value and is nonempty. Second, the feasible correspondence has a measurable selection, so that $\Pi_\Gamma$ is nonempty. Third, each law of motion is jointly measurable and maps into the state space of its target perch for almost every value of its shock: $g_\prec(x_\prec,\zeta)\in\mathsf{X}_\sim$ at every $x_\prec\in\mathsf{X}_\prec$, and $g_\succ(x,a,\eta)\in\mathsf{X}_\succ$ at every feasible pair $(x,a)$. Fourth, the three value spaces are nonempty, each integrand in

$$
(B_\succ v_\succ)(x,a)=\int G_\succ\bigl(v_\succ(g_\succ(x,a,\eta)),x,a,\eta\bigr)\,\mu_\eta(\mathrm{d}\eta),
\qquad
(B_\prec v_\sim)(x_\prec)=\int G_\prec\bigl(v_\sim(g_\prec(x_\prec,\zeta)),x_\prec,\zeta\bigr)\,\mu_\zeta(\mathrm{d}\zeta)
$$

has a finite absolute integral for every $v_\succ\in\mathsf{V}_\succ$ at every feasible pair and for every $v_\sim\in\mathsf{V}_\sim$ at every $x_\prec\in\mathsf{X}_\prec$, $x\mapsto(B_\succ v_\succ)(x,\pi(x))$ lies in $\mathsf{V}_\sim$ for every policy $\pi$, and $B_\prec v_\sim$ lies in $\mathsf{V}_\prec$ ([Stages and perches](./03-Stages%20and%20perches.md) §§1.2 and 2.2 to 2.4). The function $B_\succ v_\succ$ on the feasible pairs is the **choice value** of $v_\succ$. The language records these four conditions and does not decide them. The set $\Theta_{\mathrm{w}}\subseteq\Theta$ holds the $\theta$ at which the stage with its value spaces is well posed, and it depends on the choice of those spaces.

**The models of a stage.** A **stochastic kernel** from a measurable space $\mathsf{X}$ to a measurable space $\mathsf{Y}$ gives each point $x$ a probability measure $\kappa(x,\cdot)$ on $\mathsf{Y}$, with $x\mapsto\kappa(x,B)$ measurable for every measurable set $B$. Measurable spaces and stochastic kernels form a category: $\kappa$ followed by $\kappa'$ is the kernel $(x,B)\mapsto\int\kappa(x,\mathrm{d}y)\,\kappa'(y,B)$, and the identity gives each point the unit mass at that point (Fritz 2020, §4). At $\theta\in\Theta_{\mathrm{w}}$ the **forward model** of a stage is the model of its declaration graph in this category that sends the state of perch $p$ to $\mathsf{X}_p$, the edge $e_\prec$ to the kernel $\kappa_\prec$ with $\kappa_\prec(x_\prec,\cdot)$ the law of $g_\prec(x_\prec,\zeta)$ under $\mu_\zeta$, and the edge $(e_\succ,\pi)$ to the kernel $\kappa_{\succ,\pi}$ with $\kappa_{\succ,\pi}(x,\cdot)$ the law of $g_\succ(x,\pi(x),\eta)$ under $\mu_\eta$. The **backward model** is a model, in sets and maps, of the declaration graph with every edge reversed. By P11 it is a functor on the **opposite** of the free category, which has every arrow reversed and is the free category of the reversed graph. It sends the state of perch $p$ to $\mathsf{V}_p$, the edge $e_\prec$ to $\mathbb{T}_\prec=B_\prec:\mathsf{V}_\sim\to\mathsf{V}_\prec$, and the edge $(e_\succ,\pi)$ to $\mathbb{T}_{\succ,\pi}:\mathsf{V}_\succ\to\mathsf{V}_\sim$ with $(\mathbb{T}_{\succ,\pi}v_\succ)(x)=(B_\succ v_\succ)(x,\pi(x))$. The **model of laws**, also in sets and maps, sends the state of perch $p$ to the set $\mathsf{M}_p$ of finite measures on $\mathsf{X}_p$, of which the probability measures are those of mass one ([Stages and perches](./03-Stages%20and%20perches.md) §1.2), and each edge to the push-forward by its kernel, $\mu\mapsto\int\kappa(x,\cdot)\,\mu(\mathrm{d}x)$, written $\mathbb{M}_\prec:\mathsf{M}_\prec\to\mathsf{M}_\sim$ and $\mathbb{M}_{\succ,\pi}:\mathsf{M}_\sim\to\mathsf{M}_\succ$. A push-forward by a stochastic kernel preserves mass, because each $\kappa(x,\cdot)$ has mass one, so it sends a probability measure to a probability measure. The stage as constructed is a family of these models, one triple for each $\theta\in\Theta_{\mathrm{w}}$, and a calibration in $\Theta_{\mathrm{w}}$ chooses one ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §6). In the example $\kappa_\prec(k,\cdot)$ is the law of $Rk+y$, $\kappa_{\succ,\pi}(m,\cdot)$ is the unit mass at $m-\pi(m)$, and

$$
(\mathbb{T}_{\succ,\pi}v_\succ)(m)=u(\pi(m))+\beta v_\succ(m-\pi(m)),
\qquad
(\mathbb{T}_\prec v_\sim)(k)=\mathbb{E}_y[v_\sim(Rk+y)].
$$

**Builders and the operator signature.** Four **builders** of a stage are the images of its transitions: the **backward builders**, the arrival builder $\mathbb{T}_\prec$ and the decision builder at a policy $\mathbb{T}_{\succ,\pi}$, under the backward model, and the **forward builders** $\mathbb{M}_\prec$ and $\mathbb{M}_{\succ,\pi}$ under the model of laws. Two further builders are the image of no transition. A **measurable maximizer** of the choice value of $v\in\mathsf{V}_\succ$ is a policy $\pi$ with $(B_\succ v)(x,\pi(x))\ge(B_\succ v)(x,a)$ at every feasible pair $(x,a)$. The **policy builder** is a partial operator from $\mathsf{V}_\succ$ to $\Pi_\Gamma$, an operator defined on a subset of $\mathsf{V}_\succ$, whose value at $v$ is written $\pi_v$. On the selection route of [Operators and builders](./05-Operators%20and%20builders.md) §6, $\pi_v$ is a measurable maximizer of the choice value of $v$, picked by a fixed rule where one exists. On the relation route, $\pi_v$ is a policy that solves a relation that the stage states, such as a first-order condition, and the policy builder is defined at $v$ only where a unique solution or a specified measurable selection determines that policy ([Operators and builders](./05-Operators%20and%20builders.md) §7.2). The **optimizing decision builder** $\mathbb{T}_\succ$ is the partial operator from $\mathsf{V}_\succ$ to $\mathsf{V}_\sim$ that sends $v$ to the function $x\mapsto\sup_{a\in\Gamma(x)}(B_\succ v)(x,a)$. It is defined at each $v$ at which that function lies in $\mathsf{V}_\sim$ ([Stages and perches](./03-Stages%20and%20perches.md) §2.5). Where $\pi_v$ is a measurable maximizer of the choice value of $v$, the supremum at each $x$ is attained at $\pi_v(x)$, so that function is $\mathbb{T}_{\succ,\pi_v}v$, which lies in $\mathsf{V}_\sim$ by the fourth condition of a well-posed stage:

$$
\mathbb{T}_\succ v=\mathbb{T}_{\succ,\pi_v}v.
$$

This equality holds on the selection route wherever the policy builder is defined, and on the relation route only where $\pi_v$ is a maximizer. Where it holds, every policy $\pi$ has $(\mathbb{T}_{\succ,\pi}v)(x)\le(B_\succ v)(x,\pi_v(x))$, so $(\mathbb{T}_\succ v)(x)$ is also the supremum of $(\mathbb{T}_{\succ,\pi}v)(x)$ over the policies. The **operator signature** of a stage has, for each perch $p$, a sort $\mathtt{V}_p$ with the carrier $\mathsf{V}_p$ and a sort $\mathtt{M}_p$ with the carrier $\mathsf{M}_p$, and a sort of policies with the carrier $\Pi_\Gamma$. Its symbols are the builders, each with the rank of its operator: $\mathbb{T}_\prec:\mathtt{V}_\sim\to\mathtt{V}_\prec$, $\mathbb{T}_{\succ,\pi}$ and $\mathbb{T}_\succ$ from $\mathtt{V}_\succ$ to $\mathtt{V}_\sim$, $\mathbb{M}_\prec:\mathtt{M}_\prec\to\mathtt{M}_\sim$, $\mathbb{M}_{\succ,\pi}:\mathtt{M}_\sim\to\mathtt{M}_\succ$, and the policy builder from $\mathtt{V}_\succ$ to the sort of policies. These sorts are sorts of `Function` and of `Measure` (D4). The policy builder and $\mathbb{T}_\succ$ are partial operators, so these carriers and builders form a **partial algebra** of the operator signature: D2 with a partial function in place of a function for each of these two symbols. At $\theta\in\Theta_{\mathrm{w}}$ every other builder is defined on the whole carrier of its source sort, and a term of the operator signature has a value only where each partial builder in it is defined at the function to which it is applied. The operator signature is the stage signature of [The stage term](./APPX-C-STAGE-TERM.md) §2 with the sort of policies and the policy builder added. The carriers of the sorts $\mathtt{V}_p$ and $\mathtt{M}_p$ are the objects that the backward model and the model of laws give the states, and four of its builders are the images of the transitions, which relates the term account of [The stage term](./APPX-C-STAGE-TERM.md) §4 to its indexing path.

**The operators of a stage.** The **path of a stage** at a policy $\pi$ is the path $e_\prec$ followed by $(e_\succ,\pi)$ in its declaration graph with policies, and the typing sends it to the term `arvl_to_dcsn` followed by (`dcsn_to_cntn`, $\pi$). The backward model sends the path to the composite of the two images in the reverse order of the edges, the **stage operator at the policy**,

$$
\mathbb{T}_\pi=\mathbb{T}_\prec\circ\mathbb{T}_{\succ,\pi}:\mathsf{V}_\succ\to\mathsf{V}_\prec.
$$

The model of laws sends the path to the **forward operator at the policy**, $\mathbb{M}_\pi=\mathbb{M}_{\succ,\pi}\circ\mathbb{M}_\prec:\mathsf{M}_\prec\to\mathsf{M}_\succ$. The **Bellman operator** of the stage is the partial operator

$$
\mathbb{T}=\mathbb{T}_\prec\circ\mathbb{T}_\succ:\mathsf{V}_\succ\to\mathsf{V}_\prec,
$$

defined where $\mathbb{T}_\succ$ is. Where $\pi_v$ is a measurable maximizer of the choice value of $v$, $\mathbb{T}v=\mathbb{T}_\prec(\mathbb{T}_{\succ,\pi_v}v)$. The Bellman operator is the image of no path of the declaration graph: it is formed from the builders outside the models, and a method states how the policy builder and the decision builder at a policy are combined ([Operators and builders](./05-Operators%20and%20builders.md) §6). These three composites, and the policy builder as a term of one symbol, are terms of the operator signature, the **terms of a stage**. In the example, $(\mathbb{T}v_\succ)(k)=\mathbb{E}_y\bigl[\sup_{0<c\le m}\{u(c)+\beta v_\succ(m-c)\}\bigr]$ with $m=Rk+y$, wherever $\mathbb{T}_\succ$ is defined at $v_\succ$.

**Operations inside a builder.** A builder is a composite of **operations**: a pullback along a law of motion, an aggregation, an expectation, a maximization, an evaluation ([Stages and perches](./03-Stages%20and%20perches.md) §2.8). An operation may read several **wires** of the [semantic graph](../wiki/semgraph.md) of a stage, whose boxes are its operators and whose wires are their inputs and outputs, or one wire twice. These operations are symbols of a finer signature, whose sorts include those of functions on the feasible pairs and on the shocks ([The stage term](./APPX-C-STAGE-TERM.md) §3). With such symbols a term is no path but an arrow of the free category with finite products (Jacobs 1999, §2.2, Theorem 2.2.5, p. 129; [Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §5). In sets and maps, where the backward model and the model of laws take their values, the cartesian product interprets these terms. A line of a forward block that reads several fields would instead need a kernel out of a product of measurable spaces, and that product is no categorical product among stochastic kernels, since a law on a product space is not determined by its marginal laws. The account leaves these terms as an extension, and its propositions are stated for whole builders, where every symbol has one input.

**Methods and grids.** An **occurrence** is an operator at its place in the stage: one box of the semantic graph of the stage and a member of the carrier of `Operator`, which at each $\theta\in\Theta_{\mathrm{w}}$ denotes a map between sets of functions or of measures. It is a builder, named by the identifier of its block, as `policy` names the policy builder, or an operation inside a builder. The method and the grid are two classifiers of `Operator` (D6), defined on the occurrences, and their values are **labels**, with the discrete order. A **typing entry** of a methods file, whose type is a method word or a grid word, places one occurrence in a class and declares no object: `policy.method : !egm` asserts that the occurrence `policy` has the method label `!egm`. The pair of the two values is the label of the occurrence. A classifier whose entries do not name an occurrence gives it a value that names nothing, and the pair of two such values is the **identity label** ([Methods](./06-Methods.md) §2 states one exception). A label changes no rank, and erasing the labels of a term returns the term ([Methods](./06-Methods.md) §§3 and 8). A method word names a member of `Method`, and a grid word with its arguments names, at a configuration, a member of `Grid`. The labels admitted at an occurrence are those of its operation kind ([Methods](./06-Methods.md) §4), a value of a third classifier and no kind in the sense of D3. The language also admits a method, with a grid where the method reads one, at two further places ([Methods](./06-Methods.md) §§4 and 5). The first is a **line with an identifier**, a line of a block to which the author gives a name, as `InvEuler` in [Methods](./06-Methods.md) §9. The account takes the computation that such a line states as an operator at its place and a member of `Operator`, and the two classifiers are defined on it as on an occurrence. The second is a **declared function**, a member of `Function` that a line of a file defines, as `𝑢` in the table of §5, Step 6. A declared function is no occurrence, and a classifier is defined on part of one kind (D6), so two further classifiers, defined on the declared functions, give the method and the grid of a declared function. Their values lie among the same labels, with the same identity label.

**The versions of a stage.** A stage is **bound** in three steps, each of which fixes one more choice and gives a new **version**: it is calibrated, then methodized, then configured ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §7). The wiki calls the stage as constructed the [symbolic stage](../wiki/symbolic_stage.md) and the stage with the three bindings the [specified stage](../wiki/specified_stage.md), and the bindings may be made in more than one order ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §7). The **reference approximation** of an operator is the numerical algorithm that its term determines once every setting has a value ([Functional programming](./APPX-G-FUNCTIONAL-PROGRAMMING.md) §8).

| Version | What is bound | The Bellman operator | The forward operator at a policy |
|---|---|---|---|
| as constructed | nothing | the operators $\mathbb{T}=\mathbb{T}_\prec\circ\mathbb{T}_\succ$, one for each $\theta\in\Theta_{\mathrm{w}}$ | the operators $\mathbb{M}_\pi=\mathbb{M}_{\succ,\pi}\circ\mathbb{M}_\prec$, one for each $\theta\in\Theta_{\mathrm{w}}$ and each policy at $\theta$ |
| calibrated | a calibration $\bar\theta\in\Theta_{\mathrm{w}}$ | the operator $\mathbb{T}$ at $\bar\theta$ | the operator $\mathbb{M}_\pi$ at $\bar\theta$ |
| methodized | a methods file $m$ that types a method at one place at least, with $\bar\theta\in\Theta_{\mathrm{w}}\cap\Theta'_m$: a label on each occurrence | the same operator; where a method supplies the lines by which a builder is computed, those lines denote the declared builder under the condition that the stage lists ([Methods](./06-Methods.md) §9) | the same operator |
| configured | a configuration $\xi\in\Xi_m(\bar\theta)$ | the same operator; its term now determines the reference approximation $\widehat{\mathbb{T}}=\widehat{\mathbb{T}}_\prec\circ\widehat{\mathbb{T}}_\succ$, a composite where the numerical output of the approximate optimizing decision builder is a valid input of the approximate arrival builder | the same operator; at a supplied policy its term determines its reference approximation |

The computed operators also need **handlers**, the programs that compute the methods, which are no part of a term and are named by entries that type nothing ([Methods](./06-Methods.md) §7). A stage is methodized when its methods file types a method at one place at least, that is, when one of its typing entries has a method word as its type, at an occurrence, at a line with an identifier or at a declared function. A methods file that types grids alone, names handlers alone, or does both leaves the stage at the version it had. No row asserts that an approximation is close to the operator it approximates ([Semi-conjugacy](./10-semi-conjugacy.md) §3).

**Periods and the trellis.** A **period** is a collection of stages with **connections** between them, and a **trellis** orders periods ([Periods and the trellis](./08-periods-and-trellis.md) §§1 to 3). The **parameter vector of a period** has one coordinate for each name that one of its stage files declares as a parameter, and a name that two of its stages declare is one coordinate ([Periods and the trellis](./08-periods-and-trellis.md) §1). For a period, $\Theta_0$ is the product of the ambient sets of these coordinates, and $\Theta$ is the set of the vectors at which the conditions of §4 of every stage hold, so P9 and P10 apply to it. The language requires the sets that two stages write for one parameter to agree, where it can decide it. The **signature of a period** has the state sorts and the transitions of the state signatures of its stages and, for each connection, one further transition from the continuation state sort of one stage to the arrival state sort of the next, which pairs the coordinates of the two states, has no shock and is no decision symbol ([Stage composition](./07-stage-composition.md) §1). The declaration graph of a period is typed in that signature and joins those of its stages by one edge for each connection, from the continuation state of the first stage to the arrival state of the next. Let $\varphi$ send a point of the continuation state space of the first stage to the arrival tuple of the next whose coordinates the pairing reads from it. The language requires, at every $\theta\in\Theta$, the declared set of each continuation state field to lie in that of the arrival state field paired with it: for a continuation field $f$ and the arrival field $g$ paired with it, $f\in\mathrm{Dom}[D_g]$, that is, $D_f\subseteq D_g$ (D6). Equality of the two sets is not required, since a declared set contains the values of a field and need not be exhausted by them ([Stage composition](./07-stage-composition.md) §1). Where the next stage states no joint restriction on its arrival state, $\varphi$ then maps the first state space into the second, and where it states one, the account assumes that every tuple $\varphi(x)$ satisfies it. At each $\theta$ at which every stage of the period is well posed, the forward model of the period sends the connection to the kernel that gives each point $x$ the unit mass at $\varphi(x)$, and its backward model sends it to $v_\prec\mapsto v_\prec\circ\varphi$ on the arrival value space of the next stage, where the value spaces admit it. Where each coordinate is paired with the coordinate in the same position, $\varphi$ is the inclusion of the first state space in the second, and $v_\prec\circ\varphi$ is the restriction of $v_\prec$ to it. Where $\varphi$ is one-to-one and onto the second state space, the two states may be identified, as [Stage composition](./07-stage-composition.md) §2 and [Periods and the trellis](./08-periods-and-trellis.md) §6 describe. A trellis joins the declaration graphs of its periods in the same way, typed in the signature formed likewise from its periods, and the operators of the stages compose along the joined path. The parameter vector of a trellis and its admissible set are formed in the same way, except that a name declared in two periods gives two coordinates.

<a id="3-propositions"></a>

## 7 Propositions

**P1 (Partitions on the stated domains).** The role classifier partitions $F$, and the perch classifier partitions $F_{\mathrm{loc}}$: a classifier gives each member of its domain one value, so under the discrete order each member lies in exactly one fiber. ∎

**P2 (No inhabited common subsort of disjoint fibers).** Let $i\ne j$ be values of one classifier $c$ with the discrete order. Then $R_c[i]\cap R_c[j]=\varnothing$, because a common member $x$ would have $c(x)=i$ and $c(x)=j$, and a sort $s$ below both fibers has $A_s=\varnothing$ (D5). ∎

> **Corollary.** A sort of fields with a member cannot be below both `ArrivalField` and `DecisionField`. The value fields at a perch $p$ form $\mathrm{ValueField}\wedge\mathrm{PerchField}[p]$, a set of declared quantities and not the value space $\mathsf{V}_p$.

**P3 (Class inclusions by declared set).** If $D\subseteq D'$, then $\mathrm{Dom}[D]\subseteq\mathrm{Dom}[D']$, because $D_x\subseteq D$ gives $D_x\subseteq D'$. The inclusion is strict exactly when some $x$ lies in $\mathrm{Dom}[D']\setminus\mathrm{Dom}[D]$. ∎

**P4 (Combined constraints).** The carrier of $\mathsf{Field}[p,r,D]$ is

$$
\{f\in F_{\mathrm{loc}}:\mathrm{perch}(f)=p,\ \mathrm{role}(f)=r,\ D_f\subseteq D\}.
$$

For a field $f$ with perch $p$ and role $r$, the choice $D=D_f$ gives the least such carrier that contains $f$, since every $D$ that admits $f$ contains $D_f$. The classifiers need not be independent. ∎

**P5 (Arrival is a subsort of the sort of all fields).** The condition of `ArrivalField` implies the condition that every member of $F$ satisfies, so by D5 the sort lies below the sort interpreted by $F$, and no declared inclusion is needed. ∎

**P6 (A field and its representative are distinct objects).** Let $\mathrm{V}_\succ$ be a value field at continuation information with the declared set $\mathsf{L}$, a random variable with values in $\mathsf{L}$. When it is measurable with respect to $\sigma(\mathrm{X}_\succ)$, the information generated by the continuation state $\mathrm{X}_\succ$, it has a measurable representing function $v_\succ:\mathsf{X}_\succ\to\mathsf{L}$ with $\mathrm{V}_\succ=v_\succ(\mathrm{X}_\succ)$ almost surely ([Fields, functions and types](./04-fields%2C%20functions%20and%20types.md) §1.2). The representation implies no square integrability and fixes no values of $v_\succ$ outside the law of the state. ∎

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

<a id="worked-cases"></a>

## 8 Worked cases

1. `c : !ctrl @ ℝ₊₊`, for a name that a block header lists. The name is a field. The component `!ctrl` names the sort `ControlField`, and `ℝ₊₊` names $\mathrm{Dom}[\mathbb{R}_{++}]$ (§5, Step 3). The type names their intersection (D7), the line asserts that `c` is a member of it (D4), and `c` is at the decision perch wherever a header lists it.
2. `Γ : (0, R)`, where `Γ` is a growth factor and not the feasible correspondence of §5. The name is a parameter, and the line gives the condition $\theta_\Gamma\in(0,\theta_R)$. With `R : ℝ₊₊` numbered first, P9 gives the pairs with $\theta_R\in\mathbb{R}_{++}$ and $0<\theta_\Gamma<\theta_R$.
3. `β : ℝ₊₊ @ (0, ρ)`. Two sets in one type name $\mathrm{Dom}[\mathbb{R}_{++}\cap(0,\theta_\rho)]$ at each $\theta$ (§3), and the line gives the one condition $0<\theta_\beta<\theta_\rho$.
4. `q : (0,1) := (β*R)^(1/ρ)/R`. The line defines `q` and requires $(\theta_\beta\theta_R)^{1/\theta_\rho}/\theta_R$ to have a value in $(0,1)$, an implicit restriction on `β`, `R` and `ρ` (§4). Suppose the file also declares `R : ℝ₊₊`, `ρ : (1, inf)` and `β : (0,1) @ (0, R^(ρ-1))`. Given finite $\theta_R>0$, $\theta_\rho>1$ and $\theta_\beta>0$, the condition on `q` is equivalent to $\theta_\beta<\theta_R^{\theta_\rho-1}$, the second component of the type of `β`, so beside that line it changes nothing (P10). The converse fails: the condition on `q` does not imply $\theta_\beta<1$, since $\theta_R=1.04$, $\theta_\rho=2$ and $\theta_\beta=1.02$ give `q` near $0.990$.
5. `q := 1`. The line is a definition and restricts nothing: `q` is the constant 1, its condition $1\in\mathbb{R}$ always holds, and $\Theta$ is unchanged.
6. `ρ : (0,1) \/ (1, inf)`. The set expression denotes the union of two intervals, the line gives the condition $\theta_\rho\in(0,1)\cup(1,\infty)$, and the language admits the union because the name is a parameter (§2).
7. `n_a : ℕ` in a methods file, read by `policy.grid : !Cartesian(a=(a_min, a_max, n_a))`. The name is a setting. Its line requires its value to lie in $\mathbb{N}$, and the grid word adds conditions on $\Xi_m(\theta)$: a count of at least two, and bounds in order inside the declared set of the coordinate `a` ([Methods](./06-Methods.md) §5).
8. `policy.method : !egm`, with the grid of case 7. The entry declares no object. It types the occurrence `policy`, the policy builder, whose rank runs from $\mathtt{V}_\succ$ to the sort of policies (§6): its method label is `!egm`, its grid label is the grid word, and neither changes the rank.

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
- The perch values have the discrete order (§5, Step 2). The information sets are nested ([Stages and perches](./03-Stages%20and%20perches.md) §3), and an order on the perch values after them would make `!arvl @ !dcsn` equal to `!arvl`. Whether to order them is open.
- The language admits fewer types than the account gives a meaning to. A union or a difference is not written after `:=`. It is refused in the set of a field, of a shock or of a function's argument, because a grid is checked at its two bounds, and two bounds inside a set with a gap do not place the points between them inside the set.
- §6 is stated for a stage with both transitions and without branches ([Branching](./09-branching.md) §1). The form of the choice value with a second map outside the integral, which an Epstein–Zin certainty equivalent needs ([Stages and perches](./03-Stages%20and%20perches.md) §2.3a), is not yet stated in the account. #todo
- The policy builder has two readings in the project's pages. On the first, it returns one policy: on the selection route its value at $v$ is a measurable maximizer of the choice value of $v$, picked by a fixed rule. This reading is that of §6 and of [Operators and builders](./05-Operators%20and%20builders.md) §§6 and 7.2. On the second, it returns the set of all the policies that maximize the choice value, and a numerical method selects one member of that set. This reading stands in [Operators](./catalogues/operators.md) §4, in the wiki entries [backward builder](../wiki/backward_builder.md) and [semantic graph](../wiki/semgraph.md), in rules R7 and R8 of Bellman-SYM's Appendix C, and in the signature that the package prints for the policy builder, whose output is a set of policies. The two readings give the same policy where exactly one policy maximizes the choice value, since the set then has one member. Which of the two the account keeps is open. #todo

<a id="6-sources"></a>

## 10 Sources

- Fritz, T. (2020). A synthetic approach to Markov kernels, conditional independence and theorems on sufficient statistics. *Advances in Mathematics* 370, 107239. Read in the arXiv version, arXiv:1908.07021.
- Goguen, J. A., and Meseguer, J. (1992). Order-sorted algebra I: equational deduction for multiple inheritance, overloading, exceptions and partial operations. *Theoretical Computer Science* 105(2), 217–273. Definitions 2.1 and 2.7 are those of the version read, Technical Monograph PRG-80, Oxford University Computing Laboratory, December 1989.
- Goguen, J. A., Thatcher, J. W., Wagner, E. G., and Wright, J. B. (1977). Initial algebra semantics and continuous algebras. *Journal of the ACM* 24(1), 68–95.
- Jacobs, B. (1999). *Categorical Logic and Type Theory*. Studies in Logic and the Foundations of Mathematics 141. Elsevier.
- Meseguer, J. (1998). Membership algebra as a logical framework for equational specification. In *Recent Trends in Algebraic Development Techniques (WADT 1997)*, Lecture Notes in Computer Science 1376, 18–61. Read in the author's version, without the printed page numbers.
- Riehl, E. (2016). *Category Theory in Context*. Dover. Read in the author's second edition.
- Rushby, J., Owre, S., and Shankar, N. (1998). Subtypes for specifications: predicate subtyping in PVS. *IEEE Transactions on Software Engineering* 24(9), 709–720.
