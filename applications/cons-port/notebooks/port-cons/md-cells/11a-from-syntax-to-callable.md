<!-- notebook cell 26 | id: k1hv6l6eg2k -->

## From syntax to callable: the whisperer builds $\mathbb{T}^{\text{CMP}}$

We now have everything needed to solve: configured stages $\mathbb{S}^{\text{CFG}}$ (from the binding pipeline), de-sugared expressions (from the recipe step), and the period structures defined above. The remaining step is the whisperer's **build**: it reads a period dict and constructs a callable period operator $\mathbb{T}^{\text{CMP}}$.

The function `make_period_operator` in `ffp_utils` does this. Given a period dict `{"stages": ..., "connectors": ...}` and an inter-period connector, it:

1. **derives the backward solve order** from the connector graph (following poststate → prestate links),
2. **dispatches each stage** to the appropriate operator factory (`make_egm_cons_operator`, `make_vfi_port_operator`, etc.) based on the method tag attached during methodization, and
3. **chains the resulting callables** into a single function $\mathbb{T}^{\text{CMP}}(V_{\text{cont}}) \to V_{\text{arvl}}$.

If a disc operator is provided, it is applied first in the backward direction — wrapping the continuation before any economic stage sees it.

The operator factories for the consumption stage `eval` the de-sugared expressions stored earlier (the recipe from the previous section) against concrete grid arrays at each backward step. This is the only place where the translation from stage YAML to executable code actually executes — everything before this was syntax manipulation. The recipe is stored as a module-level dict in `ffp_utils`; a future refactor could attach it directly to each stage object, but for now the global is sufficient.
