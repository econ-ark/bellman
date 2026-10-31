---
title: Functional programming foundations
short_title: Functional programming
tags:
  - foundations
  - ffp
  - semantics
audience: user
type: theory
topic: [calculus]
---

# Appendix G — Functional programming

> [!summary]
> A stage declares typed objects and equations from which Bellman operations are constructed. Calibration assigns economic parameter values; methodization assigns numerical procedures to specified operations; configuration supplies their numerical settings. This appendix defines those objects and maps, states the composition they preserve, and works through an income-and-consumption stage. Backus's functional programming supplies the distinction between functions, represented functions and forms for combining them.

> [!info]- Relationship with other documents
> **Builds on** — [Stages and perches](./03-Stages%20and%20perches.md) defines the economic data and information. [Fields, functions and types](./04-fields,%20functions%20and%20types.md) distinguishes fields from their representing functions.
> **Formal account** — [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md) gives the term-interpretation result. [Operator algebra](./APPX-F-OPERATOR-ALGEBRA.md) gives the economic and numerical conditions.
> **Used by** — [Stages](../Bellman-Sym/01-stage.md) and [Methodization](../Bellman-Sym/04-methodization.md) give the concrete source and attachment rules, [Equation parsing rules](../Bellman-Sym/appendices/12-equation-parsing-rules.md) the admitted expression forms, and Bellman-SYM's [Appendix C](../Bellman-Sym/appendices/14-appendix-c-syntax-to-semantics.md) the interpretation rules that §3 names. The notation below describes their mathematics, not an additional source format.

## 1. Primitive objects and expressions

The Bellman-Euler Domain-Specific Declarative Language (**BE-DDSL**) distinguishes data, representations of functions, and operations on functions. A representation is a finite expression with declared meaning; it is an object that can be inspected and transformed before the represented function is applied. A number, an expression denoting a number, and an expression denoting a function therefore have different roles.

Let $\mathbb O_P$ denote the language's **primitive objects**, the literals and supplied symbols from which expressions are formed. Separate them as

$$
\mathbb O_P=\mathbb O_P^{\mathrm{lit}}\sqcup\mathbb O_P^{\mathrm{sym}}.
$$

The symbol $\sqcup$ means that the two classes are distinguished even if their printed spellings coincide. The following table classifies their uses; each supplied symbol still requires its own type and interpretation.

| Class | Examples and meaning |
|---|---|
| Literal data | An integer or decimal literal denotes a number; a truth literal denotes true or false; a quoted string supplies text. A displayed quotient such as `1/3` is an expression using division, not necessarily a separate rational literal. |
| Domain and law symbols | Real domains, interval and product constructions, and a distribution family such as `LogNormal` denote spaces or laws when their required inputs are supplied. A symbol denoting a space is distinct from an element of that space. |
| Pointwise operations | Addition, subtraction, multiplication, division, powers and comparisons act on their declared numerical domains. |
| Operations on functions | Expectation, evaluation, differentiation and optimization act on functions or relations, subject to their mathematical domains. |
| Numerical method symbols | A quadrature, interpolation or optimization method identifies a procedure for a stated operation. Its settings and eventual arrays or callable implementation are different objects. |

Declarations, local function definitions, application, typed composition and finite tuple or record formation supply **expression-forming rules**. Punctuation spells those rules in source; a colon is not thereby an extra numerical operation. Bellman-SYM's equation parsing rules determine the admitted source forms. The table is a mathematical classification, not a claim that every conceivable constructor or numerical method is implemented.

Write $\mathbb O$ for the class of finite, well-formed represented objects obtained from the supplied vocabulary and declared names. Finite tuples and records belong to this constructed class; their components need not all be literals. The primitive vocabulary itself need not be closed under every construction. In particular, assembling a tuple of primitive values does not turn that tuple into an additional primitive symbol.

A **function object** is an expression denoting a function with specified arguments and result. Let $\mathbb F\subseteq\mathbb O$ be their class, and let $\mathbb T\subseteq\mathbb F$ consist of those denoting **higher-order functions**, functions whose inputs or outputs include functions. A transition $g:X\times Z\to Y$ and utility $u:C\to\mathbb R$ are function objects when represented; an expectation $\mathcal V(Y)\to\mathcal V(X)$ and a Bellman operator are higher-order examples. Here $\mathcal V(X)$ is a declared class of value functions on $X$, with the regularity required by the operation. Membership in these classes depends on the interpretation, not on the spelling of a name.

There are two different uses of “primitive.” A primitive *language operation*, such as multiplication, is supplied by the language. An economic *primitive*, such as a utility function or transition law, is supplied by the model and may itself be defined by an expression. Conversely, a supplied integration operation can be mathematically substantial. The [operator catalogue](./catalogues/operators.md) identifies the operations used in the calculus.

## 2. Declarations and function objects

A **declaration environment** $D$ records the names in scope, their types, roles, information requirements and defining expressions where supplied. It also includes shock-law declarations and stage-level domain restrictions, which need not occur inside a builder's equations. It distinguishes an economic parameter from a local function argument, a state field from its state space, and an input function from a function the stage constructs. A name introduced by the modeler extends $D$; it does not become a new built-in primitive.

Write $D\vdash e:A$ to mean that expression $e$ has type $A$ under these declarations. Two basic formation rules are

$$
\frac{D\vdash f:A\to B\qquad D\vdash x:A}{D\vdash f(x):B},
\qquad
\frac{D\vdash f:B\to C\qquad D\vdash g:A\to B}
     {D\vdash f\circ g:A\to C}.
$$

Application produces a result at an argument; composition produces a function. A local definition binds its formal arguments within its body. In the consumption source of Bellman-SYM's Stages page, for example,

```bl
ρ : (1, inf)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
```

The symbol `ρ` is an economic parameter. The `c` in this definition is a local argument, distinct from a control with the same spelling in another scope. The definition represents the parameterized family $u_\rho:\mathbb R_{++}\to\mathbb R$, with $u_\rho(c)=c^{1-\rho}/(1-\rho)$. Calibration at $\rho=2$ selects $u_2(c)=-1/c$. It supplies no particular consumption argument.

The earlier function-object account can also describe a declared constant through a **nullary operation**, one with no arguments. Formally, a symbol of rank $()\to A$ is interpreted by an element of $A$, or equivalently by a function $1\to A$, where $1$ is a singleton. A named space can be treated this way in an algebra whose relevant carrier consists of spaces. A parameter can be treated as a named nullary symbol whose interpretation is supplied by calibration. This is a precise way to express the declaration idea; it does not identify a space with a scalar or require the program to store a separate function for each name.

An unbound economic parameter and a free continuation function are declared inputs with different roles. In the construction above, a parameter's name, domain and binding remain inspectable even after calibration. It is not replaced everywhere by an anonymous numeric literal. Local argument binding is likewise retained in interpreted definitions so that substitution respects scope.

**Parameters are not separate semgraph wires.** A **semgraph**, the semantic graph of the constructed stage, retains the full definitions using their named parameters, along with parameter declarations and calibration. For example, $u_\rho$ still has the consumption argument $c$; $\rho$ determines which function it is. The graph can display that function without a separate parameter input wire. This applies to the two initial diagrams, forward and backward, as well as to the two builders graphs. Parameters must be accounted for in the constructed graph's definitions, rather than removed from the drawing afterward.

## 3. A stage as a declaration unit

A symbolic **stage** is a finite collection of related declarations and typed equation groups. One way to record its structure mathematically is

$$
s=\bigl(D;\ (b,I_b,O_b,e_b)_{b\in B}\bigr).
$$

Here $B$ is the finite collection of authored builder identifiers; $I_b$ and $O_b$ are the ordered declared inputs and outputs of builder $b$; and $e_b$ is its collection of equations, local definitions and conditions. A **builder** is an authored typed block defining a transition, value calculation or policy relation. This record describes information already present in a stage, not a proposed software class. An individual implicit equation can denote a relation until conditions make it a function.

The stage is **closed with respect to declarations**: every name used is supplied by the language, declared in the stage or bound locally. That does not make it a closed numerical calculation. A declared continuation function remains an input to the backward problem, and declared parameters still need values. Nor does closure prove that every output is well defined: equations and their domains must determine the outputs as functions or specified relations under the interpretation rules of Bellman-SYM's Appendix C.

The ordinary economic stage has the data

$$
\bigl(X_\prec,X_\sim,X_\succ;\ A,\Gamma;\
(Z_\zeta,\mu_\zeta),(Z_\eta,\mu_\eta);\
g_\prec,g_\succ;\ G_\prec,G_\succ\bigr).
$$

The three $X_p$ are state spaces at arrival, decision and continuation. The action space is $A$, and $\Gamma(x)\subseteq A$ is the set of feasible actions at decision state $x$. Each $Z$ is a shock space with its law $\mu$, conditional on the relevant state or state–action pair when required. The transitions $g_\prec,g_\succ$ determine the next state; the pointwise aggregators $G_\prec,G_\succ$ combine a scalar continuation value with current quantities. [Stages and perches](./03-Stages%20and%20perches.md) §1 gives their complete domains. The perches are information sets; state arguments summarize what is needed from that information.

These economic primitives determine operations on value functions and distributions. They are distinct from the stage's source expressions and from the language's supplied primitive symbols. A stage occurrence supplies the equations, declarations and bindings needed for its particular position in a model. Different occurrences of the same source can have different parameter values or methods. Compatible stages compose through declared identifications of outgoing and incoming fields; those identifications do not supply a missing transition equation.

### 3.1 Income and consumption

Use the stage of §4 of Bellman-SYM's Stages page. Beginning assets are $b\geq0$, observed income is $y>0$, resources are $w>0$, consumption satisfies $0<c\leq w$, and continuation savings are $a\geq0$. Its economic parameter vector is

$$
\theta=(R,\beta,\rho,\mu_y,\sigma_y),\qquad
R>0,\quad0<\beta<1,\quad\rho>1,\quad\mu_y\in\mathbb R,\quad\sigma_y\geq0.
$$

The income law $\nu_\theta$ is that of $y=\exp(\mu_y+\sigma_y Z)$ with $Z$ standard normal and independent of arrival information. This statement fixes the meaning of the two lognormal parameters. The stage's pointwise definitions are

$$
\begin{aligned}
 g_{\prec,\theta}(b,y)&=Rb+y,& g_\succ(w,c)&=w-c,\\
 u_\rho(c)&=\frac{c^{1-\rho}}{1-\rho},&
 G_{\succ,\theta}(v,w,c)&=u_\rho(c)+\beta v,\qquad G_\prec(v,b,y)=v.
\end{aligned}
$$

The continuation input is a function $W:\mathbb R_+\to\mathbb R$. The function $g_\succ$ first supplies its argument, then $G_{\succ,\theta}$ combines the resulting scalar with current utility. Thus

$$
 Q_\theta[W](w,c)=u_\rho(c)+\beta W(w-c),\qquad
 (\mathbb T_{\succ,\theta}W)(w)=\sup_{0<c\leq w}Q_\theta[W](w,c),
$$

and arrival evaluation is

$$
 (\mathbb T_{\prec,\theta}v)(b)
 =\int v(Rb+y)\,\nu_\theta(dy),\qquad
 \mathbb T_\theta=\mathbb T_{\prec,\theta}\circ\mathbb T_{\succ,\theta}.
$$

Take $W$ continuous, so it is bounded on every compact savings interval. Because $\rho>1$, utility tends to minus infinity as consumption tends to zero; for each $w>0$ the supremum is attained. A policy output additionally requires a specified measurable maximizing selection. The arrival calculation requires absolute integrability of the resulting $v(Rb+y)$; these are the hypotheses used in the example of Bellman-SYM's Stages page. Continuation value, choice value, selected policy and numerical arrays are different objects.

At the operation level, **Pullback along the law of motion** names composition with $g$, and **Value aggregation $G$** names the subsequent pointwise aggregation. A sub-builder is named by the function its complete equation and ordered arguments define. Keeping these operations inside their whole builders preserves both the Bellman decomposition and the equations defining it. Arithmetic inside $g$ or $G$ remains part of those definitions; it is not a further builder/primitive semgraph grain, or level of displayed decomposition.

## 4. Forms and represented functions

Backus distinguishes objects, functions, application, functional forms and definitions in an **FP system**.[^backus-fp] A functional form combines functions, or functions and objects, to produce another function. His **FFP systems** additionally represent functions systematically by objects.[^backus-ffp] The represented-function classes in §1 apply this distinction to a typed economic vocabulary.

| Form | Function it defines |
|---|---|
| Composition | $(f\circ g)(x)=f(g(x))$. |
| Construction | $[f_1,\ldots,f_n](x)=(f_1(x),\ldots,f_n(x))$, for functions sharing the argument domain. |
| Condition | Apply $f$ or $g$ according to a predicate evaluated at $x$. This is a specified conditional choice, distinct from maximizing over branch values. |
| Constant | Return a supplied object, with the adopted rule for undefined arguments. |
| Apply-to-all, or map | Apply a function to every element of a finite sequence. |
| Insert | Combine a nonempty sequence from the right with a binary function: $/f\,(x_1,x_2,x_3)=f(x_1,f(x_2,x_3))$. |

Backus's particular FP object set contains atoms, finite sequences and an undefined object $\bot$. Its functions are strict, meaning $f(\bot)=\bot$, and a sequence containing $\bot$ collapses to $\bot$. His constant form therefore takes an argument and returns $\bot$ on an undefined argument; it is not a nullary operation. Map preserves the empty sequence; insert on an empty sequence needs a specified suitable right identity. Changing the grouping of insert needs associativity. His additional while and binary-to-unary forms respectively repeat a function under a predicate and fix one argument of a function on pairs.[^backus-forms] These choices do not assign undefinedness to every infeasible action or identify undefinedness with a zero terminal value.

A supplied primitive and a definition have different status. A definition assigns a fresh name to a defining form, possibly recursively. Its meaning is obtained from that form; recursion may fail to terminate. Backus fixes a system through its atoms, primitive functions, forms and a set of definitions with distinct left-hand names.[^backus-definitions] A local definition in the economic language additionally has its declared arguments and scope.

For total functions $g:X\to Y$ and $f_i:Y\to Z_i$, construction satisfies

$$
 [f_1,f_2]\circ g=[f_1\circ g,f_2\circ g],
$$

because both sides return $(f_1(g(x)),f_2(g(x)))$ for each $x\in X$.[^backus-algebra] This is an equation between functions. It permits substitution while economic parameters and all other inputs are held fixed. Shared randomness must also be preserved: $(U,U)$ for a single binary draw always has equal entries, whereas two independent fair binary draws have equal entries with probability one half.

In FFP an atom can represent a function, and a headed sequence can represent a form. Backus's representation function $\rho$ assigns the represented function; his meaning function $\mu$ evaluates expressions containing applications to objects. Some represented functions return further application expressions, so these two roles are distinct. His **metacomposition rule** interprets a sequence by applying the function represented by its first element to the pair consisting of the whole sequence and the original argument.[^backus-meaning] For example, the controlling function for $\langle\mathrm{CONST},a\rangle$ selects $a$ from $\langle\langle\mathrm{CONST},a\rangle,y\rangle$ on defined inputs. The rule permits new represented forms; it does not itself supply the meanings of Bellman builders.

The project's mathematical interpretation Υ and numerical realization Ρ below are distinct from Backus's $\rho$ and $\mu$. Representation by objects also leaves the choice of parser open. The current `.bl` language parses arithmetic and binding into a temporary syntax tree and retains interpreted equations and operations in the semgraph.

## 5. Interpretation and composition

A **signature** $\Sigma$ specifies type names and operation symbols with ranks, their ordered input and output types. A **target algebra** assigns a mathematical set to each type and an operation of the corresponding rank to each symbol. A **homomorphism** preserves these operations. Given a target algebra and an environment assigning meanings to free inputs, interpretation of finite terms extends uniquely from their constituents.[^adj] We write this interpretation as $\Upsilon_\theta(e)$ when the economic parameter assignment is $\theta$.

For example, the interpretation of the represented composition of stage operations obeys

$$
 \Upsilon_\theta(t_\prec\circ t_\succ)
 =\Upsilon_\theta(t_\prec)\circ\Upsilon_\theta(t_\succ)
 =\mathbb T_{\prec,\theta}\circ\mathbb T_{\succ,\theta}.
$$

In these composition formulas, $t_\prec,t_\succ$ denote represented operator arrows with a formal value-function input. An operator can instead be encoded by a closed term $h_\succ$ of function type, denoting a function $\mathcal V(X_\succ)\to\mathcal V(X_\sim)$. Its continuation argument is an input of the denoted function, not a free variable of $h_\succ$. Evaluating this function term at the formal input $W$ gives the corresponding operator arrow $t_\succ$; evaluating the application $h_\succ(W)$ at a particular continuation requires an assignment to $W$. The [initial-algebra account](./APPX-B-INITIAL-ALGEBRA.md) distinguishes ground terms, those without free variables, from free terms and treats exact expansion of builders into constituent operations.

A **category** consists of objects, arrows, identities and associative composition of compatible arrows. For sets and total functions, its objects are sets and its arrows are functions. A categorical object is therefore a whole domain, whereas the represented objects in §1 are particular data or expressions. A **functor** assigns objects and arrows to another category, preserving domains, codomains, identities and composition.

For the structural statements below, use the checked first-order operation signature of [Initial-algebra semantics](./APPX-B-INITIAL-ALGEBRA.md). “First-order” means that terms are formed by applying declared operation symbols to terms: a function space can be one of the types, with evaluation or selection supplied as a typed operation. It does not supply a rule for binding a function argument. Local definitions are elaborated with their binding checked before this operation presentation is used.

Let $\mathsf{Term}(\Sigma)$ have finite products of declared types as objects and finite tuples of these well-typed operation terms, in listed input variables, as arrows. Composition substitutes terms for those variables; identity is the tuple of input variables. Arrows are identified by the structural rules for composition and tuple formation; renaming bound variables in retained definitions does not change their meaning. The functor claims below concern this represented operation category, rather than every raw source expression containing a binder. Additional economic equations require separate verification in a target interpretation.

The categorical product $A\times B$ has projections selecting its components; $[f,g]$ is the unique function whose projections are $f$ and $g$. This justifies typed construction, without importing every product identity into Backus's different strict-sequence convention.

This construction is the setting in which calibration and methodization can be called functorial. Their formulas specify the object and arrow assignments. It is not a claim that every transformation of program records, or every interpretation of stochastic diagrams, preserves all categorical structure.

## 6. Calibration

Let $P$ be the declared economic parameter names. An **admissible calibration** $\theta$ assigns a value of the declared type to every required name in $P$, including any joint restrictions. For the stage in §3.1, $P=\{R,\beta,\rho,\mu_y,\sigma_y\}$. Let $\Theta$ be the set of admissible assignments. Writing only $P\to\mathbb O_P$ describes a name-to-value assignment; functoriality concerns its extension to the represented operations and their compositions.

Consider a category whose objects are families of domains $(X_\theta)_{\theta\in\Theta}$ and whose arrows are families of total functions $(f_\theta:X_\theta\to Y_\theta)_{\theta\in\Theta}$. These claims cover operations that are total on their declared carriers. An unsolved implicit relation can be retained as an element of a relation-valued type; this does not make it a total function from states to controls. Identity and composition are defined separately at each $\theta$. For a fixed $\bar\theta\in\Theta$, calibration is the evaluation functor

$$
 \mathcal C_{\bar\theta}:(X_\theta)_{\theta\in\Theta}\longmapsto X_{\bar\theta},
 \qquad
 \mathcal C_{\bar\theta}:(f_\theta)_{\theta\in\Theta}\longmapsto f_{\bar\theta}.
$$

It preserves identity and composition because

$$
 \mathcal C_{\bar\theta}(\mathrm{id}_X)=\mathrm{id}_{X_{\bar\theta}},
 \qquad
 \mathcal C_{\bar\theta}(f\circ g)
 =f_{\bar\theta}\circ g_{\bar\theta}
 =\mathcal C_{\bar\theta}(f)\circ\mathcal C_{\bar\theta}(g).
$$

This also accommodates a domain such as $[0,a_{\max}]$ depending on a parameter: calibration selects the domain as well as the function on it. Calibration must be admissible for every operation being composed. A declaration alone does not establish the analytical conditions needed for a family of integrals or optimizing operations to be well defined.

On a represented expression, the corresponding specialization assigns each parameter its value and acts through its defining forms. In particular,

$$
 \mathcal C_{\bar\theta}(f(x))
 =\mathcal C_{\bar\theta}(f)\bigl(\mathcal C_{\bar\theta}(x)\bigr),
 \qquad
 \mathcal C_{\bar\theta}([f,g])
 =[\mathcal C_{\bar\theta}(f),\mathcal C_{\bar\theta}(g)].
$$

Locally bound variables are not parameter names to replace. The same specialization applies to parameter-dependent laws, feasible sets and complete stage definitions. It is an algebraic account of their meaning; the current stage construction records bindings alongside retained symbolic equations.

For example, with $\bar\theta=(1.04,0.96,2,0,0.1)$, the calibrated stage has

$$
 g_{\prec,\bar\theta}(b,y)=1.04b+y,\qquad
 Q_{\bar\theta}[W](w,c)=-\frac1c+0.96W(w-c),\qquad
 y=\exp(0.1Z).
$$

The transition still takes beginning assets and income; the choice value still takes a continuation function, resources and consumption. Calibration selects the economic instance without supplying those arguments or solving the stage. When two stages share one economic parameter, compatible composition uses the same binding for it. Distinct stage-local parameters may instead have distinct calibrations.

## 7. The binding maps

The three binding verbs with a source held fixed are maps from stage versions to stage versions, each writing one binding: $\mathcal C_c(S) = \mathrm{calibrate}(S, c)$, $M_m(S) = \mathrm{methodize}(S, m)$ and $K_s(S) = \mathrm{configure}(S, s)$. Here a **source** is the set of assignments of one kind that a verb binds, parameter values $c$, a method assignment $m$ or settings $s$; a **stage version** is a stage as it stands after its construction or after one of its bindings; and $\mathcal C_c$ is the calibration of §6 with $\bar\theta = c$. The bindings are made in the order calibrate, methodize, configure, so a specified stage is $S^{\mathrm{spec}} = K_s\, M_m\, \mathcal C_c(S)$. $\mathcal C$ commutes with $M$ and with $K$ in bindings and graphs; $K$ is defined on methodized versions only, since settings are read against the methods that name them; $M$ is applied once, a version holding one methods binding. Three laws hold, verified on `cons.bl` and `port.bl`: a verb binds once from a merged source and refuses one that values fewer names than the stage requires; for complete sources $c_1, c_2$ the versions $\mathcal C_{c_2}(\mathcal C_{c_1}(S))$ and $\mathcal C_{c_2}(S)$ have equal bindings and graphs; a binding changes no graph.

A **method assignment** $m$ selects numerical methods for supported operation occurrences. Fix these occurrences and their identities, and write $\omega_i$ for one such operation symbol. A methodized signature $\Sigma_m$ records the same mathematical inputs and outputs, together with the selected method and the settings it requires. Distinct occurrences can be distinguished even when they denote the same mathematical operation.

Methodization acts on generators by

$$
 M_m(\omega_i)=\omega_i^{m(i)},
$$

leaves unselected generators unchanged, and extends to composite expressions by

$$
 M_m(\mathrm{id}_A)=\mathrm{id}_A,\qquad
 M_m(f\circ g)=M_m(f)\circ M_m(g),\qquad
 M_m([f,g])=[M_m(f),M_m(g)].
$$

Thus $M_m:\mathsf{Term}(\Sigma)\to\mathsf{Term}(\Sigma_m)$ is a functor once the selected generators have compatible ranks. The notation describes a fixed, consistent assignment: if the same represented occurrence is shared, its method is shared; different occurrence-specific choices require distinct occurrences in the source of this map. Bellman-SYM's authoring rules for [methodization](../wiki/methodization.md) resolve supported addresses and occurrence overrides before this mathematical assignment is considered.

For an expectation occurrence, for example,

$$
 E_y\longmapsto E_y^{\mathrm{GH}(n)}.
$$

Here $\mathrm{GH}$ denotes the Gauss–Hermite quadrature family and $n$ is its node-count setting. The tag retains expectation as its mathematical target. The node count does not become an additional economic input of that expectation, and numerical representation can still use a different carrier, such as sampled values on a grid.

Define **erasure** $U_m$ to forget the method annotations while preserving the underlying operation, its equations and economic inputs. Then

$$
 U_m\circ M_m=\mathrm{id}
$$

on this represented term structure. The identity states what methodization retains. It does not say the numerical quadrature sum equals the exact expectation. A method assigned to a whole builder retains that builder's defining equations and must state how it accounts for required constituent computations. It does not authorize deletion of their definitions or conflicting duplication of their settings.

After $m$ is selected, let $N_m$ be its required setting names and let $s$ assign values of the required types to those names. **Configuration**, denoted $K_s$, specializes the settings of the methodized symbols; for example,

$$
 K_s\bigl(E_y^{\mathrm{GH}(n)}\bigr)=E_y^{\mathrm{GH}(3)}
 \quad\text{when }s(n)=3.
$$

Its object assignment retains the declared economic types. Its action on expressions preserves identity, composition and construction by the same constituent-wise definition as $M_m$. Hence it is a functor between the corresponding categories of method-annotated terms. A numerical domain that belongs to the *model*, such as an explicitly discrete action set, remains economic data; a grid chosen only to approximate a continuous function belongs to numerical configuration.

Settings are read against the methods that name them, so $K$ is defined on methodized versions. For a constructed stage $S$, a specified stage has the form

$$
 S^{\mathrm{spec}}=K_s\, M_m\, \mathcal C_c(S).
$$

It retains the model's equations together with $c$, $m$ and $s$. The order is calibrate, methodize, configure; each operation returns a distinct stage. Mathematical specialization of disjoint fixed assignments can commute—for example, $\mathcal C_c M_m=M_m\mathcal C_c$ when the same method assignment remains applicable on both sides. This does not assert that the public interface accepts every ordering, or that choosing a method according to parameter values is independent of calibration.

## 8. Mathematical and numerical realization

Three mathematical objects are associated with a fully specified operation:

| Object | What determines it |
|---|---|
| Exact target $\Upsilon_\theta(e)$ | The economic expression and parameter assignment. |
| Reference approximation $\widehat e_{c,m,s}$ | A fully specified mathematical algorithm, including its numerical settings. |
| Executable realization $\mathrm P_{c,m,s}(e)$ | The selected implementation of that algorithm, including its numerical representations. |

Here $\mathrm P$ is the project's capital Rho, Ρ, written this way to distinguish it from the utility parameter $\rho$. A **handler** is the implementation assigned to the stated operation and method. Its correctness means agreement with the reference algorithm under the chosen numerical conventions; accuracy means agreement of that algorithm with the economic target to a stated precision or in a justified limit. If numerical and exact functions have different domains, the comparison must include the maps between those representations. [Operator algebra](./APPX-F-OPERATOR-ALGEBRA.md) §6 states these separate requirements.

### 8.1 The arrival expectation

In §3.1 the exact operation is

$$
 (E_{\theta}v)(b)
 =\int_{\mathbb R}v\bigl(Rb+e^{\mu_y+\sigma_y z}\bigr)\,\phi(dz),
$$

where $\phi$ is the standard-normal probability law and the integrand is absolutely integrable. Selecting Gauss–Hermite quadrature and $n$ nodes gives the reference operation

$$
 (\widehat E_{\theta,n}v)(b)
 =\sum_{j=1}^{n}w_j\,
 v\bigl(Rb+e^{\mu_y+\sigma_y z_j}\bigr).
$$

The nodes $z_j$ and weights $w_j$ here are normalized for the standard-normal law: weights sum to one. If a library returns nodes $x_j$ and weights $a_j$ for the weight $e^{-x^2}$, use $z_j=\sqrt{2}x_j$ and $w_j=a_j/\sqrt{\pi}$.[^quadrature] The expectation target, the chosen quadrature rule and an implementation's convention are therefore distinct inspectable objects.

For a numerical check of this one operation, take $b=0$, $v(w)=w$, $\mu_y=0$ and $\sigma_y=0.1$. The exact value is $e^{0.005}$. One-node standard-normal quadrature has $z_1=0,w_1=1$ and gives $1$. Thus methodization and configuration preserve the identified target but give an approximation that is already different in this elementary case. The numerical analysis must justify how increasing resolution improves agreement for the intended function class.

Applied to the stage composition, the assignments give

$$
 M_m(t_\prec\circ t_\succ)
 =M_m(t_\prec)\circ M_m(t_\succ),
 \qquad
 \widehat{\mathbb T}_{c,m,s}
 =\widehat{\mathbb T}_{\prec,c,m,s}
  \circ\widehat{\mathbb T}_{\succ,c,m,s},
$$

provided the numerical output of the decision operation is a valid input to the arrival operation, including any stated representation conversion. The first equation is structural functoriality; the second defines the composed numerical calculation. Neither equation supplies a bound on its distance from $\mathbb T_\theta$. Substituting a candidate policy for a maximizer, changing shock dependence, or omitting a feasibility condition changes the economic target unless a separate equivalence has been established.

Forward probability propagation uses the same declared transitions and a supplied policy, where required. Its pairing with backward transition expectation holds under the integrability conditions in [Operators and builders](./05-Operators%20and%20builders.md) §3. Reward aggregation and optimization require their own interpretation. Likewise, fixed-point existence and convergence of repeated Bellman application require the conditions in [Periods and the trellis](./08-periods-and-trellis.md); they are not consequences of the functor laws above.

[^backus-fp]: J. Backus (1978), “Can Programming Be Liberated from the von Neumann Style? A Functional Style and Its Algebra of Programs,” *Communications of the ACM* 21(8), 613–641, §§11.2–11.2.3, p. 620.
[^backus-forms]: Backus (1978), §11.2.4, pp. 621–622.
[^backus-definitions]: Backus (1978), §§11.2.5–11.2.6, p. 622.
[^backus-algebra]: Backus (1978), §12, especially the construction–composition law discussed in §12.9, p. 631.
[^backus-ffp]: Backus (1978), §13.1, p. 631.
[^backus-meaning]: Backus (1978), §§13.2–13.3.2, p. 632.
[^adj]: J. A. Goguen, J. W. Thatcher, E. G. Wagner and J. B. Wright (1977), “Initial Algebra Semantics and Continuous Algebras,” *Journal of the ACM* 24(1), 68–95, §2, especially Propositions 2.1, 2.3 and 2.6, pp. 71–75. The categorical term presentation here uses typed substitution and finite products; additional equations must be satisfied by its interpretation.
[^quadrature]: NumPy, [`numpy.polynomial.hermite.hermgauss`](https://numpy.org/doc/stable/reference/generated/numpy.polynomial.hermite.hermgauss.html), specifies the weight $e^{-x^2}$. The displayed conversion follows by substituting $z=\sqrt{2}x$ into the standard-normal density.
