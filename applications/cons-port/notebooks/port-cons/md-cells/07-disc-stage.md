<!-- notebook cell 14 | id: cell-9 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

### Disc stage

The **disc stage** extracts the discount factor $\beta$ into a
standalone operator:

$$
\mathbb{S}_{\text{disc}}(\mathrm{v}_\succ)(x) = \beta \cdot \mathrm{v}_\succ(x)
$$

Applied first in backward direction, it scales both
$\mathrm{v}_\succ$ and $\partial\mathrm{v}_\succ$ by $\beta$,
so economic stages remain beta-free and reusable across
configurations.