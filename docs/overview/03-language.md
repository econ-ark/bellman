---
title: The Bellman-SYM language
tags:
  - bellman-sym
  - user-facing
  - syntax
  - type
status: Draft
related:
  - "[[01-stage]]"
  - "[[12-equation-parsing-rules]]"
  - "[[13-perch-tagging-rules]]"
date: 2026-09-19
audience: user
type: overview
---

# The Bellman-SYM language

> [!summary]
> A stage is written in a stage file (a `.bl` file), and we read the buffer-stock file part by part. Every object has a type, and a field's type says where the field is known and what values it takes. The file opens with a preamble that declares parameters, shocks and functions. Its five blocks follow: two state the laws of motion, two state how value is computed backward, and one states the choice. Annotations give blocks and equations addresses; a numerical method can attach at an address only when the constructed object there admits that method.

Now that we have the core concepts, let's turn to the Bellman-SYM language. We write the stage of the previous page as a stage file, and the next page joins stage files into periods and a trellis. 

## 1 The stage syntax

We declare a stage in a stage file (a `.bl` file). A stage file declares the objects of a stage ([The stage](02-stage.md) §1), together with their types. The types are the information, necessary and sufficient, that Bellman-SYM needs in order to turn the equations of the file, which are written as in a paper, into the operators that give the model its meaning. 

It is useful to understand what the types do before writing a file.

### 1.1 Typing

#type 
Every object in a stage is typed with a colon `:`. A field's type gives its set of values and its perch: `b : ℝ₊ @ !arvl` declares `b` a field known on arrival with values in ℝ₊. A field known at decision need not be known on arrival; seen from the arrival perch it is random, and a law of motion, with its shock, determines it from the arrival fields. Each object is typed once in the stage file. 

#type #classifier #type/join 

A type may have several components: a set, a role word such as `!ctrl` for the control, and a perch word such as `!arvl`, joined by `@` in any order. A shock's distribution is not a type and is written on its own line with `~`. [Stages](../Bellman-Sym/01-stage.md) states the typing rules in full.

## 2 The buffer-stock stage file

#bl-file #preamble 

### 2.1 Preamble

The buffer-stock stage file first declares its parameters, its shocks and its functions, in what we call informally the 'preamble' of the stage. Each declaration is a name, a colon and a type: `β : (0,1)` says that the discount factor lies in the open unit interval.  Here is the buffer-stock preamble. 
```bl
@stage: buffer_stock

# Declare parameters, shocks and functions
β : (0,1)
ρ : (1, inf)
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊
y : ℝ₊₊
y ~ LogNormal(μ_y, σ_y)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
```

### 2.2 Blocks

A **block** connects one perch to the next, forward or backward. Its header, an annotation in square brackets, names the block and types its inputs and outputs; its body, in braces, holds the equations. Two blocks state the laws of motion, `arvl_to_dcsn` and `dcsn_to_cntn`; two state how value is computed backward, `cntn_to_dcsn` and `dcsn_to_arvl`; and the `policy` block states the choice. Let's look at the `arvl_to_dcsn` block:

```bl
[id=arvl_to_dcsn, (b : ℝ₊ @ !arvl, y) -> (m : ℝ₊₊ @ !dcsn)] {
    m = R*b + y                  :: [id=resources]
}

```

#annotations 
Note that the body of a block begins with `{` and ends with `}`, and that within it each equation has a field on its left side and a formula on its right. A block is annotated in the square brackets before its body, and an equation after the `::` symbol: the annotation `:: [id=resources]` gives the equation its address. An `id` has no mathematical meaning: it gives the line an address, by which a methods file names it. [Methodization](../Bellman-Sym/04-methodization.md) lists the constructed operators, [evaluated fields](08-fields-evaluation-and-methods.md) and [builders](../wiki/builder.md) to which methods can attach.

A forward block's header lists every field its equations read that no earlier line of the block defines, including a control or a shock, and the state fields it writes. A backward block's header lists the value fields it reads and writes and the controls at which its equations are read, and no state. For example, the value equation `V = 𝑢(c, H_d) + β*V[>]` in a housing stage reads `H_d`, a decision state, without listing it: that state is a coordinate of the decision value. A state of the backward block's input perch must instead be reached through the law of motion. A state listed on a backward header is refused.

A field can also be defined within a block. Such a field is neither a state nor a control; it is just an intermediate quantity. For instance:

```bl
[id=arvl_to_dcsn, (b : ℝ₊ @ !arvl, y) -> (m : ℝ₊₊ @ !dcsn)] {
    rtrns_b = R*b  
    m = rtrns_b + y                  :: [id=resources]
}

```

The underscore in `rtrns_b` is part of the name and indexes nothing. 

Combining the other blocks, the whole stage file is:

```bl
@stage: buffer_stock

# Declare parameters, shocks and functions
β : (0,1)
ρ : (1, inf)
R : ℝ₊₊
μ_y : ℝ
σ_y : ℝ₊
y : ℝ₊₊
y ~ LogNormal(μ_y, σ_y)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)

# Blocks

[id=arvl_to_dcsn, (b : ℝ₊ @ !arvl, y) -> (m : ℝ₊₊ @ !dcsn)] {
    m = R*b + y                  :: [id=resources]
}
[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ₊) : !cntn] {
    a = m - c                    :: [id=savings]
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, c) : !cntn -> (V : ℝ @ !vlu) : !dcsn] {
    V = 𝑢(c) + β*V[>]            :: [id=value]
}
[id=dcsn_to_arvl, V : !dcsn -> (V[<] : ℝ @ !vlu) : !arvl] {
    V[<] = E_{y}(V)              :: [id=value]
}
[id=policy, V[>] : !cntn -> c] {
    c = argmax_{c}(𝑢(c) + β*V[>]) :: [id=choice]
}
```

In the blocks above, `V[>]` is the continuation value the stage receives, `V` the decision value, and `V[<]` the arrival value; the marks `[>]` and `[<]` select perches, not calendar periods. Listing `y` among the inputs of the first block makes income an argument of its law of motion; it does not place `y` at the arrival perch, whose information is everything known before income is drawn. The operator `E_{y}` averages over the income law, and `argmax_{c}` gives the set of feasible maximizers: the policy block states that the policy lies in that set, and choosing one member of it is the task of a numerical method ([Stages](../Bellman-Sym/01-stage.md) §4 says when a maximizer exists). 

Note that the file has no line for the borrowing constraint: the equation `a = m - c` and the declared domains of `c` and `a` jointly impose `0 < c ≤ m`, and the maximization ranges over these feasible choices.
