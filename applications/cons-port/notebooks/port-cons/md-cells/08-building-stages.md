<!-- notebook cell 15 | id: 5ea306f0c731 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

<div style="border-top: 2px solid rgba(0,0,0,0.15); margin: 2.5em 0 1em;"></div>

## Building stages

To take stock, we now have the three stage YAMLs (cons, port, disc) in the library. In principle, we can represent this syntax in any way we want in memory, and then layer on a faithful computational representation on top of it. `dolo-plus` has a native representation in the form of a `SymbolicModel` (`.mod`) object: a **symbolic stage** containing symbol declarations (with perch annotations), equation blocks (transitions, builders), and space definitions—but **no** numerical methods, **no** parameter values, and **no** solver settings. It is the syntactic object to which the meaning map ($\Upsilon$) is applied.

The key point is that each `.mod` object—_not_ the YAML template in the library—is a syntactic stage instance in a particular form. Even if we “repeat” the same stage template across time, we construct a new (identical) stage instance each time, rather than reusing a single shared object. Why? Because we define a stage as a composition of morphisms between **perches** (nodes containing the state variable, value function, information set, etc.). The morphism
$$
V_{t} \xrightarrow{\mathbb{S}_{t}} V_{t-1}
$$
is a distinct object, even if we specialize $\mathbb{S}_{t}$ to be an instance of the _same_ operator at every $t$. Practically, this means we can inspect a stage object $V_{t} \xrightarrow{\mathbb{S}_{t}} V_{t-1}$ (and ultimately its forward graph) and have everything needed to describe _that occurrence_: its own symbol table, its own equation ASTs, and—once attached—its own methods, settings, and calibration, without having to trace back to a shared template.

>We _could_ reuse one shared stage template across time and let each period “point” to it. But then we need extra bookkeeping rules—_for period $t$, which calibration, methods, and settings apply, and where do we attach them without mutating the shared template?_ Treating each stage **occurrence** as its own (possibly identical) object avoids this: each one is self-contained and easy to inspect.

Methods, settings, and calibration are attached via **functorial rebindings**: each functor takes a stage and returns a _new_ stage with the relevant attachment populated. A convenient way to present the pipeline is:

$$ \text{YAML} \overset{\text{parse}}{\longrightarrow} \mathbb{S}^{\text{SYM}} \overset{\text{methodize}}{\longrightarrow} \overset{\text{configure}}{\longrightarrow} \overset{\text{calibrate}}{\longrightarrow} \mathbb{S}^{\text{CFG}} $$

Let’s walk through this pipeline explicitly. Importantly, we are not yet building the stage objects we will solve below—we are simply demonstrating the pipeline and inspecting the intermediate forms.