"""The wage schedule of the durables model, written into the syntactic trellis.

`write_wage_schedule(syntactic)` gives each period's `tenure` record the income
level `Y` and the retirement income `y_R` of that period's age. The stage file
`declaration/stages/tenure/tenure.bl` declares both as parameters and states
the shape `y(z) = Y z + y_R` and no more; their values vary with age, which no
stage carries, so `declaration/calibration/durables.yml` holds no value for
them and this function computes them from the eight registry-level names of
`declaration/calibration/wage_schedule.yml`, which `load_recipe` carries under
`syntactic["registry"]["calibration"]` (AMD-FAC-002 §5; decisions A56 and A60).

Period `h` of the trellis is age `last_age - h`, `periods[0]` the terminal
period (D15). While the household works, at ages up to `retirement_age`,

    Y = earnings_scale * exp(λ0 + λ1 t + λ2 t² + λ3 t³ + λ4 t⁴ + λ5 s + λ6 s²),
    s = min(tenure_cap, t - tenure_origin),    y_R = 0,

with t the age and λ0 to λ6 the entries of `wage_coefficients`: the female wage
function of Dobrescu, Shanker, Bateman, Newell and Thorp (2025), a quartic in
age and a quadratic in job tenure for log earnings, with the coefficients of the
replication code of Dobrescu and Shanker (2026). From the year after
`retirement_age`, Y = 0 and y_R = `retirement_income`. At the calibrated
coefficients Y is about 0.75 at age 40 and about 0.90 at age 60 (`economics.md`,
"Calibration").

The function runs after every `load_recipe` and before the binding verbs: a
fill produces a fresh syntactic trellis from the registry, so the values are
written again after each one. It writes into the records in place and returns
the trellis. A period holding no `tenure` record, as every period of
`trellis.two-stages.yml`, is left as it is. Each tenure record's
`provenance["source_lists"]["calibration"]` receives the entry
`{"source": "applications/durables/code/wage_schedule.py", "names": ["Y", "y_R"], "age": <age>}`
after the sources the recipe named, so that a record's provenance names every
function that wrote into it (A64).
"""
import math

NAMES = ("wage_coefficients", "earnings_scale", "tenure_cap", "tenure_origin",
         "retirement_income", "first_age", "retirement_age", "last_age")
SOURCE = "applications/durables/code/wage_schedule.py"


def income_at(age, schedule):
    """`(Y, y_R)` at `age` under the schedule mapping, the eight names of
    `declaration/calibration/wage_schedule.yml`."""
    if age > schedule["retirement_age"]:
        return 0.0, float(schedule["retirement_income"])
    coefficients = schedule["wage_coefficients"]
    tenure = min(schedule["tenure_cap"], age - schedule["tenure_origin"])
    exponent = sum(coefficient * age ** power for power, coefficient in enumerate(coefficients[:5]))
    exponent += coefficients[5] * tenure + coefficients[6] * tenure ** 2
    return float(schedule["earnings_scale"] * math.exp(exponent)), 0.0


def write_wage_schedule(syntactic):
    """The syntactic trellis with `Y` and `y_R` written into the calibration
    mapping of each period's `tenure` record, at that period's age
    `last_age - h`; the trellis is changed in place and returned. Refused with
    a `ValueError` when the registry block lacks one of the eight names or the
    trellis has more periods than the ages from `first_age` to `last_age`."""
    schedule = syntactic.get("registry", {}).get("calibration", {})
    missing = [name for name in NAMES if name not in schedule]
    if missing:
        raise ValueError(f"the registry block of the syntactic trellis lacks {', '.join(missing)}; "
                         f"write them in calibration/wage_schedule.yml, named by the recipe's registry block")
    ages = schedule["last_age"] - schedule["first_age"] + 1
    if len(syntactic["periods"]) > ages:
        raise ValueError(f"the trellis holds {len(syntactic['periods'])} periods, more than the {ages} ages from "
                         f"first_age {schedule['first_age']} to last_age {schedule['last_age']}")
    for h, period in enumerate(syntactic["periods"]):
        record = period["stages"].get("tenure")
        if record is None:
            continue
        age = schedule["last_age"] - h
        income, retirement = income_at(age, schedule)
        record["calibration"]["Y"] = income
        record["calibration"]["y_R"] = retirement
        # the entry is appended to a new list under a new mapping, so that a
        # list or mapping two records share is not written twice
        provenance = dict(record.get("provenance", {}))
        lists = dict(provenance.get("source_lists", {}))
        lists["calibration"] = list(lists.get("calibration", ())) + [
            {"source": SOURCE, "names": ["Y", "y_R"], "age": age}]
        provenance["source_lists"] = lists
        record["provenance"] = provenance
    return syntactic
