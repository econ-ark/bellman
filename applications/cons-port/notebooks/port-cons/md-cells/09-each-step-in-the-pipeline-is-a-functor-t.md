<!-- notebook cell 19 | id: 383dc02f3234 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

Each step in the pipeline is a **functor** that attaches metadata
to the symbolic stage without mutating it:

- **Parse** — YAML → $\mathbb{S}^{\text{SYM}}$ (symbolic stage).  Defines perches,
  symbol groups, equation blocks.  This is what $\Upsilon$ reads.
- **Methodize** — attaches numerical schemes for each builder
  ($\mathbb{G}$: `!egm`, `!vfi`; $\mathbb{I}$: `!gauss-hermite`, etc.).
  Still symbolic with respect to parameter and setting values.
- **Configure** — binds numerical settings ($\mathrm{P}$-level):
  grid sizes, bounds, quadrature nodes, tolerances.
  Changing a setting changes the *approximation*, not the problem.
- **Calibrate** — binds parameter values ($\Upsilon$-level):
  $\beta$, $\rho$, shock moments.
  Changing a parameter changes the *mathematical model*.

The output of this pipeline is $\mathbb{S}^{\text{CFG}}$ — a configured stage with all syntax, methods, settings, and parameters bound but not yet executable. None of this is "solving." The whisperer later builds $\mathbb{S}^{\text{CFG}} \to \mathbb{S}^{\text{CMP}}$ (callable operators). The helper `bind_stage` in `ffp_utils` collapses the methodize–configure–calibrate steps into a single call — used in the next section when we build full period maps.
