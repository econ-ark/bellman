"""The behaviour test of `asva.egm` (the lean implementation rule, layer 3):
the endogenous grid step built on `make_egm_1d` from two records of kernels
made by hand, run on arrays.

A record here has the form egm reads from a builder's `kernels()` record of
the package `bellman`, which asva does not import: its pieces in order of
application, each with its function, or none for a row that states a
relation, and the names of its arguments, its outputs and its parameters;
the record's parameters and the values its calibration binds. The functions
are written in the form in which the package writes the kernels of the
consumption stage `applications/portfolio-choice/declaration/stages/cons/cons.bl`: the kernel's
arguments, then the parameters it reads, the named functions as inner
functions.
"""
from collections import namedtuple

import numpy as np
import pytest

import asva

Piece = namedtuple("Piece", "name function arguments outputs parameters")
Kernels = namedtuple("Kernels", "pieces parameters parameter_values")


def G_policy_InvEuler(V_cntn, a, argument, ρ):
    def duinv(x):
        return x**(-1/ρ)
    c_cntn = duinv(argument)
    return c_cntn


def G_policy_endoggrid(c_cntn, a):
    m_d_cntn = a + c_cntn
    return m_d_cntn


def g_dcsn_to_cntn(m_d, c):
    a = m_d - c
    return a


def G_cntn_to_dcsn(V_cntn, m_d, c, ρ):
    def u(c):
        return c**(1 - ρ)/(1 - ρ)
    V = u(c) + V_cntn
    return V


def records(ρ):
    """The records of the policy builder and of the backward decision
    builder of the consumption stage calibrated at ρ, with the two rows of
    the policy block that state a relation and the two evaluations."""
    policy = Kernels((Piece("InvEuler:Aggregation", G_policy_InvEuler, ("V≻", "a", "D_{a}(V≻)"), ("c≻",), ("ρ",)),
                      Piece("endoggrid:Aggregation", G_policy_endoggrid, ("c≻", "a"), ("m_d≻",), ()),
                      Piece("cons_choice:Pullback", None, ("c≻",), ("c",), ()),
                      Piece("Evaluation", None, ("c",), ("c",), ())),
                     ("ρ",), (ρ,))
    decision = Kernels((Piece("Pullback", g_dcsn_to_cntn, ("m_d", "c"), ("a≻",), ()),
                        Piece("Aggregation", G_cntn_to_dcsn, ("V≻", "m_d", "c"), ("V",), ("ρ",)),
                        Piece("Evaluation", None, ("V",), ("V",), ())),
                       ("ρ",), (ρ,))
    return policy, decision


def test_egm_1d_egm_builds_the_step_from_records_of_kernels_and_takes_the_parameter_values_at_each_call():
    """The continuation value V≻(a) = K(1 + a)^(1−ρ)/(1 − ρ), K = 2, has the
    marginal value K(1 + a)^(−ρ), at which the inverse Euler equation gives
    the consumption k(1 + a), k = K^(−1/ρ), and the endogenous grid the
    resources a + k(1 + a). Both are linear in a, so the interpolation is
    exact: at resources m ≥ k the consumption is k(1 + m)/(1 + k); at the
    resources 0.5, below k, the borrowing constraint binds and the
    consumption is 0.5 less the margin 1e-10. The records of the
    calibrations ρ = 2 and ρ = 3 hold the same functions, and each step
    gives the values of its own calibration. A policy record with a third
    function, and a record that binds no parameter value, are refused."""
    savings = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    evaluation = np.array([0.5, 1.0, 2.5, 4.0])
    K = 2.0
    for ρ in (2.0, 3.0):
        k = K ** (-1 / ρ)

        def utility(c):
            return c ** (1 - ρ) / (1 - ρ)

        def continuation(a):
            return K * (1 + a) ** (1 - ρ) / (1 - ρ)

        step = asva.egm(*records(ρ), savings, evaluation)(continuation, lambda a: K * (1 + a) ** -ρ)

        control = np.where(evaluation < k, evaluation - 1e-10, k * (1 + evaluation) / (1 + k))
        state = evaluation - control
        expected = {"control": control, "continuation_state": state,
                    "value": utility(control) + continuation(state),
                    "continuation_value": continuation(state),
                    "endogenous_grid": savings + k * (1 + savings), "endogenous_control": k * (1 + savings),
                    "endogenous_value": utility(k * (1 + savings)) + continuation(savings)}
        for name, array in expected.items():
            np.testing.assert_allclose(getattr(step, name), array, rtol=1e-12, atol=1e-12, err_msg=f"ρ = {ρ}: {name}")

    policy, decision = records(2.0)
    candidate = Piece("cand_value:Aggregation", G_policy_endoggrid, ("c≻", "V≻"), ("v≻",), ())
    with pytest.raises(ValueError, match="cand_value:Aggregation"):
        asva.egm(policy._replace(pieces=policy.pieces[:2] + (candidate,) + policy.pieces[2:]), decision,
                 savings, evaluation)
    with pytest.raises(ValueError, match="ρ of InvEuler:Aggregation"):
        asva.egm(policy._replace(parameter_values=None), decision, savings, evaluation)
