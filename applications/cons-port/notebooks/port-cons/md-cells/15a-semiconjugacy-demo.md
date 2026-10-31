<!-- notebook cell 36 | id: 8hfyhy4vdri -->

## Order semiconjugacy between period configurations

Beginning-returns and end-returns use the **same two economic stages** (cons, port) in opposite composition order. The two undiscounted period operators are:

$$
\mathbb{S}_{\text{port}} \circ \mathbb{S}_{\text{cons}}
\qquad\text{(beginning-returns)}
\qquad
\mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{port}}
\qquad\text{(end-returns)}
$$

These are **order semiconjugate** (Sargent and Stachurski, 2026). The **iterates lemma** gives, for $n$ backward steps:

$$
(\mathbb{S}_{\text{port}} \circ \mathbb{S}_{\text{cons}})^n = \mathbb{S}_{\text{port}} \circ (\mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{port}})^{n-1} \circ \mathbb{S}_{\text{cons}}
$$

With discounting, the disc operator $\mathbb{S}_{\text{disc}}(v) = \beta\,v$ commutes with the linear $\mathbb{S}_{\text{port}}$ but **not** with the nonlinear $\mathbb{S}_{\text{cons}}$, so $\mathbb{S}_{\text{disc}}$ must be absorbed into the $\mathbb{S}_{\text{cons}}$ bookend. Writing $\mathbb{T}_{\text{beg}}$ and $\mathbb{T}_{\text{end}}$ for the discounted period operators:

$$
\boxed{
\mathbb{T}_{\text{beg}}^n = \mathbb{S}_{\text{port}} \circ \mathbb{T}_{\text{end}}^{\,n-1} \circ (\mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{disc}})
}
\qquad
\boxed{
\mathbb{T}_{\text{end}}^n = (\mathbb{S}_{\text{cons}} \circ \mathbb{S}_{\text{disc}}) \circ \mathbb{T}_{\text{beg}}^{\,n-1} \circ \mathbb{S}_{\text{port}}
}
$$

The upshot: solve end-returns for $n{-}1$ steps, then wrap with one discounted cons step at the start and one port step at the end to recover beginning-returns — or vice versa.
