---
title: "The within-life model of Benhabib, Bisin and Luo (2019)"
audience: developer
type: model-note
topic: [applications]
---
# The within-life model of Benhabib, Bisin and Luo (2019)

> [!summary]
> A household with a fixed earnings type and a fixed return type chooses how
> much to consume and to save at each age from 25 to 60, and it leaves the wealth
> remaining at the end of life as a bequest. This page states the model, the two
> stages it is written in, the trellis of 37 periods, the calibration, the fifty
> instances, and what differs from the legacy registry this registry replaces.
> The within-life stage is explained in `benhabib_bellman.md`. The notebook
> [`tutorials/models/benhabib-2019/the-factory-on-benhabib.ipynb`](../../tutorials/models/benhabib-2019/the-factory-on-benhabib.ipynb)
> builds the trellis; nothing is solved. The
> terms of the factory are defined in
> [The Bellman factory](../../docs/Bellman-Sym/08-bellman-factory.md).

## The model and the paper

The model is the within-life problem of Benhabib, J., Bisin, A. and Luo, M.
(2019), "Wealth distribution and social mobility in the US: A quantitative
approach", *American Economic Review* 109(5), 1623–1647 (the working paper,
NBER Working Paper 21721, 2015, is cited in `reference/README.md`). The timing is that of the paper's online
Appendix A.1, which describes the authors' numerical solution. The legacy's
`bellman-excerpt.md` and `dolo-plus-draft.yaml` adopted that timing for this
reason, and `benhabib_bellman.bl` follows them.

A household has an earnings type $\tau$, one of ten deciles, and a return type
$r$, one of five rates. Both are "drawn at birth, fixed within life". At age
$24 + t$, for $t = 1, \dots, T$ with $T = 36$, it arrives with wealth $a$,
consumes $c \in [0, a]$, earns the return $r$ on its saving, and then receives
the earnings $w_t(\tau)$ of its age bracket:

$$
a' = (1 + r)(a - c) + w_t(\tau).
$$

Utility is $u(c) = c^{1-\sigma}/(1-\sigma)$, discounted by $\beta$. The wealth
$a_{T+1}$ left after the last decision is valued by the warm-glow bequest
$e(a) = A\,a^{1-\mu}/(1-\mu)$, and the paper's last recursion,
$V_T(a) = \max_c \{u(c) + e(a')\}$, does not discount it. The value of age
$24 + t$ is therefore

$$
V_t(a) = \max_{0 \le c \le a} \bigl\{ u(c) + \beta\, V_{t+1}\bigl((1+r)(a-c) + w_t(\tau)\bigr) \bigr\},
\qquad V_{T+1}(a) = \frac{e(a)}{\beta}.
$$

## The stages

A stage is one decision step with three information sets, or perches: arrival,
decision and continuation. The within-life stage has no arrival perch: it is
entered at its decision perch.

| Stage | File | What happens in it |
|---|---|---|
| `benhabib_bellman` (stage name `bellman`) | `declaration/stages/benhabib_bellman/benhabib_bellman.bl` | The household enters the stage with wealth `m` at the decision perch, chooses `c` in `[0, m]` and continues with `a = R_vec[r_type]*(m - c) + wage_fn[tau]`. |
| `bequest` | `declaration/stages/bequest/bequest.bl` | Only in the terminal period. The stage arrives with `a_pre`, the wealth left after the last decision, and writes `V = (A/β)*a^(1-μ)/(1-μ) + V[>]`; its methods file, `declaration/stages/bequest/methods.bl`, states its derivative, `D_{a}V = (A/β)*a^(-μ)`, as a line of the same block. It makes no choice. |

In the equation above, $a$ is the stage's `m`, and $a'$ is its `a`.

The bequest's value line and the derivative line of its methods file are
the legacy's terminal block, `V_terminal` and `dV_terminal`, written in the
stage's names, with `V[>]` added to the value
as in the durables bequest. The weight $A/\beta$ makes the stage of age 60,
which discounts what it reads by $\beta$, receive $e(a)$ undiscounted. The
bequest's own `V[>]` is the terminal boundary data, zero, supplied at
realization, the step after configuration that builds the numerical model, as
for the bequest of the durables model.

## The period and the trellis

A period holds one stage. `period.yml` lists both stages, and the recipe,
`spec.yml`, places each: `bequest` in the terminal period alone, `periods: [0, 0]`, and
`benhabib_bellman` in the others, `periods: [1, 36]`. `trellis.yml` repeats the
template 37 times. `periods[h]` is age $61 - h$: `periods[0]` is the terminal
period, the paper's period $T + 1$ (age 61 under the paper's own count, age
$24 + t$); `periods[1]`, age 60, is the last decision; `periods[36]`, age 25,
is the first. `trellis.yml` writes one inter-period mapping for each adjacent
pair: `inter_connectors[h]` joins the wealth `a` of `periods[h + 1]` to the
wealth with which `periods[h]` is entered, the bequest's arrival wealth
`a_pre` for `h = 0`, `{a: a_pre}`, and the within-life stage's decision
wealth `m` for every other `h`, `{a: m}`.

## The age brackets

Earnings are constant within six age brackets of six years (Table 1), so the
recipe gives each bracket's file, `declaration/calibration/wage/bracket_k.yml`, to a range
of periods. The legacy counted in two ways. Its recipe counted periods from 1 at
age 25 (period $t$ is age $24 + t$). Its trellis file counted from 0 at age 25,
with the terminal entry at index 36. Here $h$ counts from the terminal period,
so $h = 37 - t$.

| Bracket | Ages | Legacy recipe key | Legacy trellis indices | Key here |
|---|---|---|---|---|
| 1 | 25–30 | `"1-6"` | 0–5 | `"31-36"` |
| 2 | 31–36 | `"7-12"` | 6–11 | `"25-30"` |
| 3 | 37–42 | `"13-18"` | 12–17 | `"19-24"` |
| 4 | 43–48 | `"19-24"` | 18–23 | `"13-18"` |
| 5 | 49–54 | `"25-30"` | 24–29 | `"7-12"` |
| 6 | 55–60 | `"31-36"` | 30–35 | `"1-6"` |

The legacy never assembled its trellis. Read against its trellis indices, as a
factory reads a range, each of its ranges falls one period late: no range
covers age 25 (index 0), and bracket 6 covers ages 56 to 60 and the terminal
entry. Counted from the terminal period, the keys are the same six strings, the
brackets run in the reverse order, and each range covers its bracket's ages.

## The instances

In the words of the legacy's `dolo-plus-draft.yaml`, the fifty types form a
"50-instance family: tau ∈ {1..10} (earnings decile, paper Table 1) × r_type ∈
{1..5} (rate-of-return state, paper Table 4). Each instance is one
finite-horizon Bellman problem."
The stage writes the types as parameters over finite sets whose members are
names: `tau` in `{q1, …, q10}`, where `qk` is the decile from $10(k-1)$ to
$10k$ percent of the earnings distribution, and `r_type` in `{r1, …, r5}`, with
these net returns from Table 4:

| Return type | r1 | r2 | r3 | r4 | r5 |
|---|---|---|---|---|---|
| net return | 0.0011 | 0.0094 | 0.0258 | 0.0560 | 0.0841 |
| standard error | 0.0069 | 0.0118 | 0.0004 | 0.0059 | 0.0043 |

The legacy registry produced the fifty "by the state-space grid product, not by
varying slot bindings", keeping the types as states whose transition is the
identity. Here each instance is a fill, for example
`fill={"calibration": {"tau": "q5", "r_type": "r3"}}`, and the family is a
sweep over fills. The legacy names no default instance, so
`declaration/calibration/main.yml` holds the first pair of its enumeration: the legacy's
tau 1 and r_type 1, written `q1` and `r1`. That pair is the lowest decile,
from 0 to 10 percent, with the net return 0.0011. The notebook's sweep fills
two other pairs. `q5` and `r3` are the legacy's tau 5 and r_type 3, the decile
from 40 to 50 percent with the net return 0.0258. `q10` and `r5` are its tau 10
and r_type 5, the decile from 90 to 100 percent with the net return 0.0841.

## Calibration

`declaration/calibration/main.yml` holds the values of Table 4 of the AER edition:
$\beta = 0.97$ and $\sigma = 2$, fixed; $\mu = 0.5993$ and $A = 0.0006$,
estimated; and the five gross returns $1 + r$ as `R_vec`. Both stages read this
file, and each binds the parameters it declares. The earnings of Table 1 of the
AER edition, in thousands of dollars a year for each bracket and decile, are in
`declaration/calibration/wage/`; the paper takes them from the PSID as computed by
Heathcote, Perri and Violante (2010).
`declaration/calibration/horizon.yml` holds $T = 36$, `first_age` 25 and `last_age` 61. No
stage declares these three names, and they set neither the number of periods,
which `trellis.yml` writes, nor any stage: the recipe's `registry` block admits
them, the trellis holds them, and its drawing reads `last_age` to label each
period with its age.

The working paper, NBER Working Paper 21721 (2015), which `reference/README.md`
cites, reports different earnings in its Table 1. Its first decile is negative,
−2.689 at ages 25 to 30, and its top decile at those ages is 87.90, where the AER
edition gives 100.3. The working paper therefore does not support the values of
`declaration/calibration/wage/`. Nor does it support those of `declaration/calibration/main.yml`: its
estimates, in its Table 2, include $\mu = 1.1860$ and $A = 0.0312$, and its
Table 4 is a transition matrix.

## What the stage files cannot state

1. **The dynasty.** The intergenerational Markov chains over $(\tau, r)$ and
   the passing of the bequest to a child join lives, not ages, and lie outside
   the within-life problem.
2. **The initial wealth** with which a household starts at age 25.
3. **The family of instances as one object.** It is the set of fills of `tau`
   and `r_type`.

## Numerical methods

The methods of a stage stand in a methods file beside its stage file, a `.bl`
file that opens with `@methods:` and is read with the stage file as an addition
to it: a block of the methods file names a block of the stage by its id and
adds its entries and its lines to that block, and a file-level entry names its
place by a path. `declaration/stages/benhabib_bellman/methods.bl` holds one
entry of the legacy's `bellman_methods.yml`, `!egm` on the policy builder, with
the legacy's handler, `"dolo:egm_backward"`, a placeholder that no callable
realizes yet, and with the grid of savings `!Cartesian(a=(a_min, a_max, n_a))`,
whose three settings the file declares with their sets. Its block `policy`
writes the inverse Euler line, the endogenous grid and `c = c[>]`, which stand
in place of the stage file's maximization at the operative level while the
declared level keeps the maximization, and its block `cntn_to_dcsn` appends the
derivative line `D_{m}V = c^(-σ)`. Three parts of the legacy file are not
written:

- the `upper_env` entry (`!FUES`), because the stage has no upper-envelope
  operator for it to attach to;
- `grid: endogenous`, because the endogenous grid is what the method computes
  and no entry names it;
- the `!Identity` entry at `dcsn_to_arvl`, because the stage has no arrival
  perch and so no builder from the decision perch to it.

The legacy's two other entries, `!Linear` on the line `c = c[>]`, the
representation of the policy at the policy builder's Evaluation,
`policy.evaluate`, and `!analytic-inverse` at the node `policy.InvEuler`, stand
in a second methods file of the stage,
`declaration/stages/benhabib_bellman/methods.bellman_method.bl`, which the
recipe does not name; an author who names it after the first in the stage's
methods list binds both.

`declaration/settings/default.yml` holds the legacy's six values. The three
the grid names, `n_a`, `a_min` and `a_max`, are read at `policy`; `grid_phi`,
`tol` and `max_iter` are read at no place. The bequest's methods file,
`declaration/stages/bequest/methods.bl`, states the derivative of the bequest's
value, which the endogenous grid step of age 60 reads; the bequest has no
settings list.

## What differs from the legacy registry

The legacy registry is `applications/pre-dynspec/benhabib-2019/registry/`,
which moved out of the repository and is kept privately by AAS.

- Its stage file `stages/bellman/bellman.yaml` paid the wage before the
  decision, in the timing of the paper's Section I. `benhabib_bellman.bl` pays
  it after the return, in the timing of Appendix A.1, as the legacy's
  `bellman-excerpt.md` and `dolo-plus-draft.yaml` do.
- Its terminal entry, `terminal: !period` with a `terminal:` block, is the
  stage `bequest` here: the bequest is a stage (AMD-FAC-002 §5, the
  specification of the Bellman factory).
- Names follow the stage files: `beta`, `sigma` and `mu` become β, σ and μ.
  The net rates `r_vec`, keyed 1 to 5, become the gross list `R_vec`, and the
  deciles keyed 1 to 10 become list positions.
- The slot `$draw` becomes `$fill`, which the settings list now names as well;
  a methods list names the stage's methods files and no slot.
- `settings/pretty_plot`, named by the legacy recipe, is dropped: the legacy
  folder does not hold it.
- The stage key is the file name, `benhabib_bellman`. The stage's own name is
  still `bellman`, which the methods file names.

## References

- Benhabib, J., Bisin, A. and Luo, M. (2019). "Wealth distribution and social
  mobility in the US: A quantitative approach." *American Economic Review*
  109(5), 1623–1647. Section I, online Appendix A.1, Tables 1 and 4.
- Heathcote, J., Perri, F. and Violante, G. L. (2010). "Unequal we stand: An
  empirical analysis of economic inequality in the United States, 1967–2006."
  *Review of Economic Dynamics* 13(1), 15–51.
