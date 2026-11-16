"""Fields supplied by one stage to another in a modular model."""

import math
import re

import numpy as np
import pytest

from bellman.refusals import ConstructionError
from bellman.stage import elaborate_text
from bellman.syntax.source import to_source
from bellman.trellis import connection_report, elaborate_trellis

CONSUMPTION = """\
@stage: consumption
Γ_c(x : ℝ) := [0, x]

[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (m : ℝ) : !dcsn] {
    m = k + 1
}
[id=dcsn_to_cntn, (m, c : ℝ₊ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
    a = m - c
}
[id=cntn_to_dcsn, (W[>] : ℝ @ !vlu, c) : !cntn -> (W : ℝ @ !vlu) : !dcsn] {
    W = c + W[>]/2
}
[id=dcsn_to_arvl, (W) : !dcsn -> (W[<] : ℝ @ !vlu) : !arvl] {
    W[<] = W
}
[id=policy, (W[>]) : !cntn -> (c : ℝ₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(cp + W[>]/2)
}
"""

KEPT_BOUND = (
    CONSUMPTION.replace(
        "(W[>] : ℝ @ !vlu, c)", "(W[>] : ℝ @ !vlu, L : (-inf, 0] @ !vlu @ !cnst, c)"
    )
    .replace("(W : ℝ @ !vlu) : !dcsn", "(W : ℝ @ !vlu, L) : !dcsn")
    .replace(
        "(W) : !dcsn -> (W[<] : ℝ @ !vlu)",
        "(W, L) : !dcsn -> (W[<] : ℝ @ !vlu, L[<] : (-inf, 0] @ !vlu @ !cnst)",
    )
    .replace("W[<] = W", "W[<] = W\n    L[<] = L")
)

SECOND_FIELD = (
    CONSUMPTION.replace("(W : ℝ @ !vlu) : !dcsn", "(W : ℝ @ !vlu, B : ℝ @ !vlu) : !dcsn")
    .replace(
        "(W) : !dcsn -> (W[<] : ℝ @ !vlu)", "(W, B) : !dcsn -> (W[<] : ℝ @ !vlu, B[<] : ℝ @ !vlu)"
    )
    .replace("W[<] = W", "W[<] = W\n    B[<] = B")
)


def kernel_outputs(record, key, **values):
    """Evaluate a compiled piece at its named arguments."""
    (piece,) = (piece for piece in record.pieces if piece.key == key)
    result = piece.function(
        *(values[name] for name in piece.arguments), *(piece.parameter_values or ())
    )
    if len(piece.outputs) == 1:
        result = (result,)
    return dict(zip(piece.outputs, result, strict=True))


@pytest.mark.parametrize(
    "case", ["kept-state", "kept-bound", "arrival-known-field", "choice-dependent-constant"]
)
def test_kept_fields_preserve_their_values(case):
    if case == "kept-state":
        text = (
            CONSUMPTION.replace(
                "(k : ℝ) : !arvl -> (m : ℝ)", "(k : ℝ, z : ℝ) : !arvl -> (m : ℝ, z)"
            )
            .replace("(m, c : ℝ₊ @ !ctrl)", "(m, z, c : ℝ₊ @ !ctrl)")
            .replace("a = m - c", "a = m - c + z")
        )
        stage = elaborate_text(text, "consumption.bl")
        values = kernel_outputs(stage.builder["arvl", "dcsn"].kernels(), "Pushforward", k=2, z=7)
        assert values == {"m": 3, "z": 7}
    elif case == "kept-bound":
        stage = elaborate_text(KEPT_BOUND, "consumption.bl")
        values = kernel_outputs(
            stage.builder["cntn", "dcsn"].kernels(),
            "Aggregation",
            **{"W≻": 4, "L": -2, "m": 3, "c": 1},
        )
        assert values == {"W": 3, "L": -2}
    elif case == "arrival-known-field":
        text = (
            SECOND_FIELD.replace("@stage: consumption", "@stage: consumption\ny : ℝ\ny ~ N(0, 1)")
            .replace("(k : ℝ) : !arvl -> (m : ℝ)", "(k : ℝ, z : ℝ, y) : !arvl -> (m : ℝ, z_d : ℝ)")
            .replace("m = k + 1", "m = k + y\n    z_d = z")
            .replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = z_d")
            .replace("W[<] = W", "W[<] = E_{y}(W)")
        )
        stage = elaborate_text(text, "consumption.bl")
        values = kernel_outputs(
            stage.builder["dcsn", "arvl"].kernels(), "Aggregation", w=4, W=4, B=-2, k=3, z=-2
        )
        assert values == {"W": 4, "B": -2}
    else:
        text = SECOND_FIELD.replace("B : ℝ @ !vlu", "B : ℝ @ !vlu @ !cnst").replace(
            "W = c + W[>]/2", "W = c + W[>]/2\n    B = c"
        )
        with pytest.raises(
            ConstructionError, match=r"(?is)(?=.*\bB\b)(?=.*\b(?:choice|control)\b).*constant"
        ):
            elaborate_text(text, "consumption.bl")


@pytest.mark.parametrize(
    "case",
    [
        "one-objective",
        "duplicate-objective",
        "no-objective",
        "explicit-policy",
        "choice-dependent-feasibility",
        "partial-line",
        "partial-product",
        "tuple-minimum",
        "tuple-maximum",
        "unbound-shock",
        "unbound-policy-derivative",
    ],
)
def test_decision_fields_use_one_policy_on_their_domains(case):
    if case == "unbound-policy-derivative":
        text = (
            CONSUMPTION.replace("@stage: consumption", "@stage: consumption\ny : ℝ\ny ~ N(0, 1)")
            .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y)")
            .replace("a = m - c", "a = m - c + y")
            .replace("W = c + W[>]/2", "W = c + E_{y}(W[>])/2")
            .replace("c = argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "1*D_{a}W[>] = 1/(c + 1)")
        )
        with pytest.raises(ConstructionError) as refusal:
            elaborate_text(text, "consumption.bl")
        assert refusal.value.rule == "shock-observed"
        assert "y" in refusal.value.message
        return
    if case == "unbound-shock":
        text = (
            SECOND_FIELD.replace("@stage: consumption", "@stage: consumption\ny : ℝ\ny ~ N(0, 1)")
            .replace("(m, c : ℝ₊ @ !ctrl)", "(m, c : ℝ₊ @ !ctrl, y)")
            .replace("a = m - c", "a = m - c + y")
            .replace("W = c + W[>]/2", "W = c + E_{y}(W[>])/2\n    B = W[>]")
            .replace("cp + W[>]/2", "cp + E_{y}(W[>])/2")
        )
        with pytest.raises(ConstructionError) as refusal:
            elaborate_text(text, "consumption.bl")
        assert refusal.value.rule == "shock-observed"
        assert "y" in refusal.value.message
        return

    line = {
        "duplicate-objective": "c + W[>]/2",
        "partial-line": "if m > 0 then 1/m else -1",
        "partial-product": "if m > 0 then (1/m, m) else (-1, 0)",
        "tuple-minimum": "min((m, m + 1))",
        "tuple-maximum": "max((m, m + 1))",
    }.get(case, "c/2")
    text = SECOND_FIELD.replace("W = c + W[>]/2", f"W = c + W[>]/2\n    B = {line}")
    if case == "partial-product":
        text = text.replace("B : ℝ", "B : ℝ × ℝ").replace("B[<] : ℝ", "B[<] : ℝ × ℝ")
    if case == "choice-dependent-feasibility":
        text = text.replace(
            "Γ_c(x : ℝ) := [0, x]", "Γ_c(x : ℝ) := {cp : ℝ₊ | cp <= x - B}"
        ).replace("[id=policy, (W[>]) : !cntn", "[id=policy, (W[>] : !cntn, B : !dcsn)")
        with pytest.raises(
            ConstructionError, match=r"(?is)(?=.*\bB\b).*(choice|control)"
        ) as refusal:
            elaborate_text(text, "consumption.bl")
        assert refusal.value.rule == "policy-feasibility"
        # the feasible set may read a decision field that depends on no choice
        elaborate_text(text.replace("B = c/2", "B = m/2"), "consumption.bl")
        return
    if case in {"no-objective", "duplicate-objective"}:
        pattern = r"(?s)(?=.*\bW\b)(?=.*\bB\b).*objective"
        if case == "no-objective":
            text = text.replace("cp + W[>]/2", "2*cp + W[>]/2")
            pattern = r"(?is)(?=.*argmax).*objective"
        with pytest.raises(ConstructionError, match=pattern):
            elaborate_text(text, "consumption.bl")
        return
    if case == "explicit-policy":
        text = text.replace("argmax_{cp : Γ_c(m)}(cp + W[>]/2)", "m/2")
    stage = elaborate_text(text, "consumption.bl")
    builder = stage.builder["cntn", "dcsn"]
    expression_cases = {"partial-line", "partial-product", "tuple-minimum", "tuple-maximum"}
    if case not in expression_cases:
        equations = str(builder["Evaluation"].denote())
        assert "𝑊(m) = 𝑐(m)" in equations
        assert "𝐵(m) = 𝑐(m)/2" in equations
    m = np.array([0.0, 2.0]) if case in expression_cases else 4.0
    # W increases with c for a constant continuation. Its maximizer is c=m.
    c = m
    if case == "explicit-policy":
        policy = stage.dcsn.builder.policy.kernels()
        c = kernel_outputs(policy, "1:Aggregation", m=m)["c"]
        assert c == 2.0
    with np.errstate(divide="raise", invalid="raise"):
        values = kernel_outputs(builder.kernels(), "Aggregation", **{"W≻": 4.0, "m": m, "c": c})
    if case in expression_cases:
        from numba import njit

        expected = {
            "partial-line": [-1.0, 0.5],
            "partial-product": [[-1.0, 0.0], [0.5, 2.0]],
            "tuple-minimum": [0.0, 2.0],
            "tuple-maximum": [1.0, 3.0],
        }[case]
        np.testing.assert_array_equal(values["W"], [2.0, 4.0])
        np.testing.assert_array_equal(values["B"], expected)
        (piece,) = (piece for piece in builder.kernels().pieces if piece.key == "Aggregation")
        compiled = njit(piece.function)
        for point, result in ((m, expected), (0.0, expected[0])):
            arguments = {"W≻": 4.0, "m": point, "c": point}
            actual = compiled(*(arguments[name] for name in piece.arguments))
            np.testing.assert_array_equal(actual[1], result)
    else:
        expected = (4.0, 1.0) if case == "explicit-policy" else (6.0, 2.0)
        assert (values["W"], values["B"]) == expected


PENSION = """\
@stage: pension
Age := {1, 2}
Y_tab : Age → ℝ

[id=dcsn_to_cntn, (m : ℝ) : !dcsn -> (a : ℝ) : !cntn] {
    a = m
}
[id=cntn_to_dcsn, (age[>] : Age @ !vlu @ !cnst) : !cntn
    -> (age : Age @ !vlu @ !cnst, pension : ℝ @ !vlu @ !cnst) : !dcsn] {
    age = 3 - age[>]
    pension = Y_tab[age[>]]
}
"""

AGE_LAW = (
    CONSUMPTION.replace("@stage: consumption", "@stage: consumption\ny : ℝ\ny(_age) ~ N(_age, 1)")
    .replace("(k : ℝ) : !arvl", "(k : ℝ, y, age) : !arvl")
    .replace("m = k + 1", "m = k + y(age) + y[age]")
    .replace("(W[>] : ℝ @ !vlu, c)", "(W[>] : ℝ @ !vlu, age : ℝ @ !vlu @ !cnst, c)")
    .replace("W[<] = W", "W[<] = E_{y}(W)")
)

FUNCTION_VALUE = (
    SECOND_FIELD.replace("@stage: consumption", "@stage: consumption\nF := ℝ → ℝ")
    .replace("(W[>] : ℝ @ !vlu, c)", "(W[>] : ℝ @ !vlu, f : F @ !vlu @ !cnst, c)")
    .replace("W = c + W[>]/2", "W = c + W[>]/2\n    B = f(c)")
)


@pytest.mark.parametrize(
    "case", ["marked-age", "same-block-age", "function-value", "selected-function", "law", "different-law-arguments"]
)
def test_fields_supply_table_keys_functions_and_shock_arguments(case):
    if case == "selected-function":
        text = (
            FUNCTION_VALUE.replace("f : F @ !vlu @ !cnst, c", "f : F @ !vlu @ !cnst, g : F @ !vlu @ !cnst, L : ℝ @ !vlu @ !cnst, c")
            .replace("B : ℝ @ !vlu", "B : F @ !vlu @ !cnst")
            .replace("B[<] : ℝ @ !vlu", "B[<] : F @ !vlu @ !cnst")
            .replace("B = f(c)", "B = if L > 0 then f else g")
        )
        stage = elaborate_text(text, "functions.bl")

        def first(_x):
            pytest.fail("selecting a function value must not invoke it")

        def second(_x):
            pytest.fail("selecting a function value must not invoke it")

        record = stage.builder["cntn", "dcsn"].kernels()
        for bound, expected in ((1, first), (0, second), (-1, second)):
            values = kernel_outputs(
                record, "Aggregation", **{"W≻": 4, "f": first, "g": second, "L≻": bound, "m": 3, "c": 2}
            )
            assert values["B"] is expected
        return
    if case in {"marked-age", "same-block-age"}:
        text = PENSION if case == "marked-age" else PENSION.replace("Y_tab[age[>]]", "Y_tab[age]")
        stage = elaborate_text(text, "pension.bl").calibrate({"calibration": {"Y_tab": [5, 8]}})
        values = kernel_outputs(
            stage.builder["cntn", "dcsn"].kernels(), "Aggregation", **{"age≻": 2, "m": 3}
        )
        assert values["pension"] == (8 if case == "marked-age" else 5)
    elif case == "function-value":
        stage = elaborate_text(FUNCTION_VALUE, "consumption.bl")
        values = kernel_outputs(
            stage.builder["cntn", "dcsn"].kernels(),
            "Aggregation",
            **{"W≻": 4, "f": lambda c: c * c + 1, "m": 3, "c": 2},
        )
        assert values == {"W": 4, "B": 5}
    elif case == "different-law-arguments":
        text = (
            AGE_LAW.replace("y[age]", "y[other_age]")
            .replace("(k : ℝ, y, age)", "(k : ℝ, y, age, other_age)")
            .replace(
                "age : ℝ @ !vlu @ !cnst, c)",
                "age : ℝ @ !vlu @ !cnst, other_age : ℝ @ !vlu @ !cnst, c)",
            )
        )
        with pytest.raises(
            ConstructionError, match=r"(?s)(?=.*\by\b)(?=.*\bage\b)(?=.*\bother_age\b)"
        ):
            elaborate_text(text, "consumption.bl")
    else:
        stage = elaborate_text(AGE_LAW, "consumption.bl")
        inputs = {"age": 6, "W[>]": lambda a: a}
        forward = stage.builder["arvl", "dcsn"].kernels(inputs=inputs)
        backward = stage.builder["dcsn", "arvl"].kernels(inputs=inputs)
        # Each spelling adds the same realized income of 7 to assets of 3.
        assert kernel_outputs(forward, "Pushforward", k=3, y=7, age=6) == {"m": 17}
        (extension,) = (piece for piece in forward.pieces if piece.kind == "DistributionExtension")
        (expectation,) = (piece for piece in backward.pieces if piece.kind == "Expectation")
        for law in (forward.laws[extension.key], backward.laws[expectation.key]):
            (declaration,) = law.declarations
            assert re.fullmatch(r"N\(6(?:\.0)?, 1(?:\.0)?\)", to_source(declaration.term))


RETIREMENT = """\
@stage: retirement
[id=dcsn_to_cntn, (a : ℝ, d : !ctrl @ {work, retire}) : !dcsn -> ()] {
    [label=work, () -> (a_w : ℝ) : !cntn] { a_w = a }
    [label=retire, () -> (a_r : ℝ) : !cntn] { a_r = a }
}
[id=cntn_to_dcsn, (W_w[>] : ℝ @ !vlu, W_r[>] : ℝ @ !vlu,
    L_w[>] : (-inf, 0] @ !vlu @ !cnst, L_r[>] : (-inf, 0] @ !vlu @ !cnst, d) : !cntn
    -> (W : ℝ @ !vlu, L : (-inf, 0] @ !vlu @ !cnst) : !dcsn] {
    W = (W_w[>], W_r[>])[d]
    L = min(L_w[>], L_r[>])
}
[id=policy, (W_w[>], W_r[>]) : !cntn -> (d : {work, retire} @ !ctrl) : !dcsn] {
    d = argmax_{d}(W_w[>], W_r[>])
}
"""


def period(stages, connectors=()):
    """A period of stage texts joined by the given connector entries."""
    return {
        "stages": {
            key: {
                "stage": {"text": text, "origin": f"{key}.bl"},
                "calibration": {},
                "methods": {},
                "settings": {},
            }
            for key, text in stages.items()
        },
        "connectors": list(connectors),
    }


INITIAL_TRELLIS = {
    "periods": [period({key: CONSUMPTION}) for key in ("latest", "earliest")],
    "inter_connectors": [{"a": "k"}],
}

RETIREMENT_TRELLIS = {
    "periods": [
        period(
            {"choice": RETIREMENT, "work": KEPT_BOUND, "retire": KEPT_BOUND},
            [{"a_w": "work.k", "a_r": "retire.k", "L_w": "work.L", "L_r": "retire.L"}],
        )
    ],
    "inter_connectors": [],
}


@pytest.mark.parametrize(
    "case",
    [
        "terminal-callable",
        "terminal-bound",
        "terminal-table",
        "same-name",
        "explicit-pair",
        "unpaired-kept-field",
        "branch-suppliers",
        "initial-arrival-law",
    ],
)
def test_connections_and_terminal_data_supply_the_declared_fields(case):
    if case == "terminal-table":
        text = PENSION.replace("Y_tab : Age → ℝ\n", "").replace(
            "(age[>] : Age", "(Y_tab : Age → ℝ @ !vlu @ !cnst, age[>] : Age"
        )
        stage = elaborate_text(text, "pension.bl")
        table = np.array([5.0, 8.0])
        values = {"age[>]": np.int64(2), "Y_tab": table}
        assert stage.check_inputs(values) == ()
        assert values["Y_tab"] is table
        np.testing.assert_array_equal(table, [5.0, 8.0])
        with pytest.raises(ConstructionError, match="Y_tab"):
            stage.check_inputs({"age[>]": 2, "Y_tab": np.array([5.0, np.nan])})
        return
    if case == "terminal-callable":
        stage = elaborate_text(CONSUMPTION, "consumption.bl")

        def continuation(_a):
            pytest.fail("checking terminal inputs must not sample a callable")

        conditions = stage.check_inputs({"W[>]": continuation})
        assert any(item.status == "required" and "W" in str(item) for item in conditions)
        return

    if case == "terminal-bound":
        stage = elaborate_text(KEPT_BOUND, "consumption.bl")

        continuation = {"W[>]": lambda _a: 0.0}
        conditions = stage.check_inputs({**continuation, "L": np.float64(-2)})
        assert conditions and all("W" in str(item) for item in conditions)
        with pytest.raises(ConstructionError, match=r"(?s)\bL\b.*\b2\b"):
            stage.check_inputs({**continuation, "L": 2})
        with pytest.raises(ConstructionError, match=r"(?s)W\[>\]"):
            stage.check_inputs({"W": continuation["W[>]"], "L": -2})
        return

    if case == "initial-arrival-law":
        trellis = elaborate_trellis(INITIAL_TRELLIS)
        report = connection_report(trellis)
        (condition,) = report.obligations
        assert (condition.condition, condition.status) == ("initial-law-supported", "required")
        assert "periods[1].earliest.k" in condition.explanation
        assert "mass one" in str(report)
        assert connection_report(trellis, periods=(1,)).obligations == (condition,)
        return

    if case == "branch-suppliers":
        with pytest.raises(ConstructionError) as refusal:
            elaborate_text(RETIREMENT.replace(" @ !cnst", ""), "choice.bl")
        assert refusal.value.rule == "branch-value-position"
        routes = connection_report(elaborate_trellis(RETIREMENT_TRELLIS)).routes
        observed = {}
        for route in routes:
            fields = [item.required.rsplit(":", 1)[-1] for item in route.components]
            observed[route.branch] = (
                route.status,
                [name for name in fields if name.startswith("L_")],
            )
        assert observed == {"work": ("certified", ["L_w"]), "retire": ("certified", ["L_r"])}
        return

    later = KEPT_BOUND if case == "same-name" else KEPT_BOUND.replace("L[<]", "M[<]")
    connector = {"a": "k", "L": "M"} if case == "explicit-pair" else {"a": "k"}
    trellis = elaborate_trellis(
        {
            "periods": [period({"consumption": later}), period({"consumption": KEPT_BOUND})],
            "inter_connectors": [connector],
        }
    )
    (route,) = connection_report(trellis).routes
    assert route.status == ("certified" if case != "unpaired-kept-field" else "uncertified")
    (bound,) = (component for component in route.components if component.required.endswith(":L"))
    expected = {"same-name": "L", "explicit-pair": "M", "unpaired-kept-field": None}[case]
    assert (bound.supplied.rsplit(":", 1)[-1] if bound.supplied else None) == expected


EGM = """\
@methods: consumption
extra_grid : ℝ₊
a_min : ℝ
a_max : ℝ
n_a : ℕ

[id=policy, policy.method : !egm | policy.grid : !Cartesian(a=(a_min, a_max, n_a))
    | policy.evaluate.method : !Linear] {
    c[>] = (D_{a}W[>]/2)^(-1/2) :: [id=InvEuler]
    m[>] = a + c[>]          :: [id=grid]
    c[~] = c[>]
}
"""


@pytest.mark.parametrize("case", ["field-grid", "infinite-marginal-value"])
def test_savings_grid_includes_the_zero_consumption_limit(case):
    text = (
        (KEPT_BOUND if case == "field-grid" else CONSUMPTION)
        .replace("c : ℝ₊ @ !ctrl", "c : ℝ₊₊ @ !ctrl")
        .replace("Γ_c(x : ℝ) := [0, x]", "Γ_c(x : ℝ) := (0, x)\n𝑢(c : ℝ₊₊) := -1/c")
        .replace("c + W[>]/2", "𝑢(c) + W[>]/2")
        .replace("cp + W[>]/2", "𝑢(cp) + W[>]/2")
    )
    methods = EGM
    if case == "field-grid":
        text = text.replace("[id=policy, (W[>])", "[id=policy, (W[>], L)").replace(
            "Γ_c(x : ℝ) := (0, x)", "Γ_c(x : ℝ) := {c : ℝ₊₊ | c < x - L}"
        )
        methods = EGM.replace("a=(a_min,", "a=(L + extra_grid,")
    stage = elaborate_text(text, "consumption.bl")
    stage.methodize({"text": methods, "origin": "methods.bl"})
    stage.calibrate({"calibration": {}})
    stage.configure({"settings": {"extra_grid": 0, "a_min": 0, "a_max": 2, "n_a": 3}})

    policy = stage.dcsn.builder.policy
    if case == "field-grid":
        assert "L" in policy.kernels().grids["policy"].reason
        first = policy.kernels(inputs={"L": -2, "W[>]": lambda _a: 0.0})
        second = policy.kernels(inputs={"L": -4, "W[>]": lambda _a: 0.0})
        assert first.grids["policy"].points == ((-2.0,), (0.0,), (2.0,))
        assert second.grids["policy"].points == ((-4.0,), (-1.0,), (2.0,))
    else:
        record = policy.kernels()
        values = kernel_outputs(
            record, "grid:Aggregation", **{"a": 0.0, "W≻": -1.0, "D_{a}(W≻)": math.inf}
        )
        assert values == {"c≻": 0.0, "m≻": 0.0}
        (condition,) = (
            item for item in stage.obligations() if item.condition == "egm-eligibility"
        )
        assert re.search(r"\binfinite\b|\+∞|∞\]", condition.explanation)


HUMAN_WEALTH = """\
@stage: perfect_foresight
Γ : ℝ₊₊
R : ℝ₊₊
β : (0, 1)
ρ : (1, inf)
𝑢(c : ℝ₊₊) := c^(1-ρ)/(1-ρ)
Γ_c(x : ℝ) := {c : ℝ₊₊ | c < x + h[>]}

[id=arvl_to_dcsn, (k : ℝ) : !arvl -> (m : ℝ) : !dcsn] {
    m = R*k/Γ + 1
}
[id=dcsn_to_cntn, (m, c : ℝ₊₊ @ !ctrl) : !dcsn -> (a : ℝ) : !cntn] {
    a = m - c
}
[id=cntn_to_dcsn, (V[>] : ℝ @ !vlu, h[>] : ℝ₊ @ !vlu @ !cnst, c) : !cntn
    -> (V : ℝ @ !vlu, h : ℝ₊ @ !vlu @ !cnst) : !dcsn] {
    V = 𝑢(c) + β*V[>]
    h = 1 + h[>]
}
[id=dcsn_to_arvl, (V, h) : !dcsn -> (V[<] : ℝ @ !vlu, h[<] : ℝ₊ @ !vlu @ !cnst) : !arvl] {
    V[<] = Γ^(1-ρ) * V
    h[<] = h*Γ/R
}
[id=policy, (V[>], h[>]) : !cntn -> (c : ℝ₊₊ @ !ctrl) : !dcsn] {
    c = argmax_{cp : Γ_c(m)}(𝑢(cp) + β*V[>])
}
"""


@pytest.mark.parametrize(
    "remaining",
    [0, 100, 2000, None],
    ids=["last-period", "100-later-periods", "2000-later-periods", "stationary"],
)
def test_human_wealth_equals_discounted_future_income(remaining):
    stage = elaborate_text(HUMAN_WEALTH, "perfect_foresight.bl")
    stage.calibrate({"calibration": {"β": 1 / 1.04, "ρ": 2, "R": 1.04, "Γ": 1.02}})
    inputs = stage.dcsn.builder.policy.signature().inputs
    assert {
        wire.identity.field: tuple(coordinate.field for coordinate in wire.sort.coordinates)
        for wire in inputs
    } == {"V": ("a",), "h": ()}
    assert not stage.diagnostics()["unread_inputs"]
    to_decision = stage.builder["cntn", "dcsn"].kernels()
    to_arrival = stage.builder["dcsn", "arvl"].kernels()
    taken = 51.0 if remaining is None else 0.0
    for _ in range(1 if remaining is None else remaining + 1):
        decision = kernel_outputs(
            to_decision, "Aggregation", **{"V≻": 0.0, "h≻": taken, "m": 2.0, "c": 1.0}
        )["h"]
        taken = kernel_outputs(to_arrival, "Aggregation", V=0.0, h=decision, k=0.0)["h"]
    ratio = 51 / 52
    expected = 52.0 if remaining is None else math.fsum(ratio**j for j in range(remaining + 1))
    # The tolerance allows rounding when the two kernels run once per period.
    assert (decision, taken) == pytest.approx((expected, ratio * expected), abs=2e-12, rel=0)
