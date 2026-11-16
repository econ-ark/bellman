# cons[^digests]

```
STAGE cons / BACKWARD BUILDER cntn → dcsn (cntn_to_dcsn)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → ℝ
       ───────────────────────────────────────────────────
  out  𝑉   : Xm → ℝ

At
  𝑐  : Xm → ℝ₊₊,  𝑐(m) ∈ Γ(m)

Operations
  1  Pullback
     in: 𝑉≻                             out: 𝑉≻ ∘ 𝑔≻(·, 𝑐)
     ─────────────────────────────────────────────────────
     rule: (𝑉≻ ∘ 𝑔≻(·, 𝑐))(m) = 𝑉≻(𝑔≻(m, 𝑐(m)))

  2  Aggregation
     in: (1)                            out: 𝑉
     ─────────────────────────────────────────────────────
     rule: 𝑉(m) = 𝑢(𝑐(m)) + 𝑉≻(𝑔≻(m, 𝑐(m)))

  3  Evaluation
     in: 𝑉                              out: 𝑉
     ─────────────────────────────────────────────────────
     rule: 𝑉 : Xm → ℝ
           D_{m}𝑉(m) = 𝑑𝑢(𝑐(m))

Conditions
  Aggregation  𝑉(m) ∈ ℝ

Method
  !Linear   !Cartesian(m=(m_min, m_max, n_m, !expmult))  cntn_to_dcsn.evaluate
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  13  V = 𝑢(c) + V[>]

Source  methods.bl
  40  D_{m}V = 𝑑𝑢(c)  :: [id=envelope]

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  𝑢     cons:function:𝑢
  Γ     cons:correspondence:Γ
  𝑑𝑢    cons:function:𝑑𝑢  methods.bl:18
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```
STAGE cons / POLICY BUILDER policy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   𝑉≻  : Xa → ℝ
       ────────────────────────────────────────
  out  𝑐   : Xm → ℝ₊₊,  𝑐(m) ∈ Γ(m)

Declared
  𝑐(m) ∈ argmax_{cp ∈ Γ(m)} [𝑢(cp) + 𝑉≻(𝑔≻(m, cp))]

Operations
  1  InvEuler:Aggregation
     in: 𝑉≻                             out: 𝑐≻
     ──────────────────────────────────────────
     rule: 𝑐≻(a) ≤ 𝑑𝑢𝑖𝑛𝑣(D_{a}𝑉≻(a)) ⟂ a ≥ 0

  2  grid:Aggregation
     in: 𝑐≻                             out: 𝑚≻
     ──────────────────────────────────────────
     rule: 𝑚≻(a) = a + 𝑐≻(a)

  3  identification:Pullback
     in: 𝑐≻, 𝑚≻                         out: 𝑐
     ──────────────────────────────────────────
     rule: 𝑐(𝑚≻(a)) = 𝑐≻(a)                                          on 𝑚≻(Xa)

  4  Evaluation
     in: 𝑐                              out: 𝑐
     ──────────────────────────────────────────
     rule: 𝑐 : Xm → ℝ₊₊,  𝑐(m) ∈ Γ(m)

Conditions
  grid:Aggregation  𝑚≻(a) ∈ Xm
  policy            egm-eligibility: the construction satisfies the declared
                      line where the continuation value 𝑉≻ is concave and
                      continuously differentiable above the savings bound,
                      with a positive right derivative at the bound, finite or
                      infinite; an infinite derivative gives zero consumption
                      as the interpolation endpoint, outside a strictly
                      positive consumption domain   [required]

Method
  !egm   !Cartesian(a=(a_min, a_max, n_a, !expmult))   "cons-port:egm"  policy
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  17  c = argmax_{cp : Γ(m)}(𝑢(cp) + V[>])  :: [id=optimality]

Source  methods.bl
  32  c[>] <= 𝑑𝑢𝑖𝑛𝑣(D_{a}V[>]) ⟂ a >= 0     :: [id=InvEuler]
  33  m[>] = a + c[>]                       :: [id=grid]
  34  c = c[>]                              :: [id=identification]

Definitions referenced
  Xm     cons:set:Xm
  Xa     cons:set:Xa
  𝑢      cons:function:𝑢
  Γ      cons:correspondence:Γ
  𝑑𝑢𝑖𝑛𝑣  cons:function:𝑑𝑢𝑖𝑛𝑣  methods.bl:19
  𝑔≻     cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```
STAGE cons / FORWARD BUILDER dcsn → cntn (dcsn_to_cntn)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signature
  in   μ   : finite measure on Xm
       ────────────────────────────────────────
  out  μ≻  : finite measure on Xa

At
  𝑐  : Xm → ℝ₊₊,  𝑐(m) ∈ Γ(m)

Operations
  1  Pushforward
     in: μ                              out: μ≻
     ──────────────────────────────────────────
     rule: μ≻(B) = μ({m ∈ Xm | 𝑔≻(m, 𝑐(m)) ∈ B})
──────────────────────────────────────────────────────────────────────────────
Source  cons.bl
  9  a = m - c

Definitions referenced
  Xm    cons:set:Xm
  Xa    cons:set:Xa
  Γ     cons:correspondence:Γ
  𝑔≻    cons:g:dcsn_to_cntn
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

![cons](cons.svg)

[^digests]: SHA-256 digests of the stage file and the files it is bound from: `declaration/stages/cons/cons.bl` `34cf564877c0d7a4ecd5e15dcd55ed776ffe7f649a1cb674d378753b33cdea78`; `declaration/spec.cons-port.yml` `5f3b0532c050f1b2c4dd7dbe90167b94c30b77595fbb72c54f7759c199a03376`; `declaration/trellis.cons-port.yml` `0d77d967eb153ef50863160376c7b79f654fa2f9400e1abb7c454c328fd1654f`; `declaration/calibration/portfolio.yml` `939c9c4f380a5924a22634073e6989df99df35a511a23337ca25191cedbfef4a`; `declaration/settings/cons_wide.yml` `bdaf3b6673fac56b8de384da7435acfb62390b494df89370e360e4dd6ee07116`; `declaration/stages/cons/methods.bl` `34ef3c54fc4cfbc2debcab2b0fea774051079101cb01b64c3b8a30f3476ba0fe`.
