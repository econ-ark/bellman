#!/usr/bin/env python3
"""Refine a housing-renting stage YAML via Matsya --refine round-trips.

A record only: step 4 calls the command-line client of Matsya, a retrieval
service outside the repository that is disabled (AAS, 7 September 2026). In a
clone of the repository only a dry run (`--dry-run`), which prints the
prompts, runs; the outputs under converged_output/ are kept as a record.

The script:
  1. Reads the stage markdown from stages/<name>.md
  2. Extracts the YAML code block under "## Stage YAML"
  3. Builds a context-rich prompt with the model description
  4. Calls econ-ark-matsya --llm --refine
  5. Saves the full Matsya output to converged_output/<name>.md
  6. Reports whether convergence was achieved

Source files (stages/*.md, dolo submodule YAMLs) are NEVER modified.
"""

import argparse
import re
import subprocess
import sys
import textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STAGES_DIR = SCRIPT_DIR / "stages"
OUTPUT_DIR = SCRIPT_DIR / "converged_output"

STAGE_NAMES = [
    "tenure_choice",
    "owner_housing",
    "owner_cons",
    "renter_housing",
    "renter_cons",
]

# ── Economic context shared across all stages ──────────────────────────
MODEL_CONTEXT = textwrap.dedent("""\
    This stage is part of a 5-STAGE HOUSING TENURE-CHOICE MODEL
    (Dobrescu & Shanker 2024, Application 3; based on Fella 2014).

    MODEL: Agent lives T periods with assets a >= 0, housing H >= 0,
    Markov income y. Each period: (1) tenure choice own/rent, (2) on
    own path: discrete housing H' then continuous consumption; on rent
    path: discrete rental S then continuous consumption.

    OWNER budget: w_oc = (1+r)*a + z_vals[y] + H - (1+phi*1[H'!=H])*H'
    RENTER budget: w_r = (1+r)*a + z_vals[y] + H; then w_rc = w_r - P_r*S

    CES utility: u(c,h) = [theta*c^rho + (1-theta)*(kappa*h+iota)^rho]^((1-gamma)/rho)/(1-gamma)
    where h = H' for owners, h = S for renters. gamma=1 -> Cobb-Douglas (solver handles).

    KEY DECISIONS:
    - Disjoint branch poststates: _o suffix (own), _r suffix (rent) per spec 0.1l
    - Renter outputs H_r = 0 explicitly for uniform inter-period connector
    - CES InvEuler requires numerical inversion
    - Income in renter path: w_r includes z_vals[y]
    - Borrowing: a >= 0 via endogenous grid truncation in EGM
    - Terminal: V_{T+1} = 0

    5-stage DAG:
    (a,H,y_pre) -> [tenure_choice] -own-> [owner_housing] -> [owner_cons]
                                   -rent-> [renter_housing] -> [renter_cons]
    """)

STAGE_CONTEXT = {
    "tenure_choice": (
        "STAGE 1 — TENURE CHOICE (BRANCHING). Agent observes Markov income "
        "shock y, then chooses own or rent. Own branch passes (a,H,y) as "
        "(a_o, H_o, y_o). Rent branch liquidates to cash w_r = (1+r)*a + "
        "z_vals[y] + H and passes (w_r, y_r). Branch poststates DISJOINT. "
        "Backward builder: max over branch values. Arrival builder: E_{y|y_pre}."
    ),
    "owner_housing": (
        "STAGE 2 — OWNER HOUSING CHOICE. Discrete choice over housing H' "
        "from grid XH with transaction cost phi. Cash-on-hand w_oc computed "
        "after adjustment. Arrival is identity from tenure_choice own branch. "
        "Backward builder: discrete max over H'."
    ),
    "owner_cons": (
        "STAGE 3 — OWNER CONSUMPTION. Continuous consumption c via EGM. "
        "CES utility u(c, H_nxt). Budget b_o = w_oc - c, b_o >= 0. "
        "Needs values_marginal (dV, dV[>]) for EGM. InvEuler: numerical "
        "inversion of CES marginal utility. Housing and income pass through."
    ),
    "renter_housing": (
        "STAGE 4 — RENTER HOUSING CHOICE. Discrete choice over rental "
        "services S from grid XS. Cash after rental: w_rc = w_r - P_r*S. "
        "Arrival from tenure_choice rent branch (w_r, y_r). "
        "Backward builder: discrete max over S."
    ),
    "renter_cons": (
        "STAGE 5 — RENTER CONSUMPTION. Continuous consumption c via EGM. "
        "CES utility u(c, S). Budget b_r = w_rc - c, b_r >= 0. CRITICAL: "
        "poststate H_r = 0 explicitly — renters carry no housing. Needs "
        "values_marginal for EGM. InvEuler: numerical inversion."
    ),
}


def extract_yaml_block(md_text: str, heading: str) -> str:
    """Extract the first ```yaml ... ``` block after a markdown heading."""
    heading_pat = re.compile(rf"^##\s+{re.escape(heading)}", re.MULTILINE)
    m = heading_pat.search(md_text)
    if not m:
        raise ValueError(f"Heading '## {heading}' not found in markdown")

    code_start = md_text.find("```yaml", m.end())
    if code_start == -1:
        raise ValueError(f"No ```yaml block found after '## {heading}'")
    yaml_start = md_text.index("\n", code_start) + 1

    code_end = md_text.find("```", yaml_start)
    if code_end == -1:
        raise ValueError("Unterminated ```yaml block")

    return md_text[yaml_start:code_end]


def extract_final_yaml(matsya_output: str) -> str | None:
    """Extract the last YAML block from matsya --refine output."""
    blocks = re.findall(r"```yaml\n(.*?)```", matsya_output, re.DOTALL)
    if not blocks:
        return None
    return blocks[-1].strip()


def check_convergence(matsya_output: str) -> bool:
    """Check if Matsya reported convergence."""
    return "CONVERGED" in matsya_output.upper()


def call_matsya(prompt: str, model: str, max_iter: int) -> str:
    """Call econ-ark-matsya --llm --refine and return stdout."""
    cmd = [
        "econ-ark-matsya",
        prompt,
        "--llm",
        "--refine",
        f"--max-iter={max_iter}",
        f"--model={model}",
    ]
    print(f"  Running matsya (model={model}, max_iter={max_iter})...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  ERROR: matsya exited {result.returncode}", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout


def refine_stage(
    stage_name: str, model: str, max_iter: int, dry_run: bool
) -> bool:
    """Refine one stage. Returns True if converged."""
    md_path = STAGES_DIR / f"{stage_name}.md"
    if not md_path.exists():
        print(f"ERROR: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Refining: {stage_name}")
    print(f"{'='*60}")

    md_text = md_path.read_text()
    current_yaml = extract_yaml_block(md_text, "Stage YAML")

    # Build the prompt
    context = STAGE_CONTEXT.get(stage_name, "")
    prompt = (
        f"Refine the following dolo-plus YAML for the {stage_name} stage.\n\n"
        f"{MODEL_CONTEXT}\n"
        f"{context}\n\n"
        f"CURRENT YAML:\n{current_yaml}"
    )

    if dry_run:
        print("  DRY RUN — prompt would be:")
        print(textwrap.indent(prompt[:500] + "...", "    "))
        return True

    output = call_matsya(prompt, model, max_iter)

    # Save full output
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{stage_name}.md"

    converged = check_convergence(output)
    final_yaml = extract_final_yaml(output)

    # Build output file
    header = (
        f"# Matsya Refinement Output: {stage_name}\n\n"
        f"**Model**: {model}  \n"
        f"**Max iterations**: {max_iter}  \n"
        f"**Converged**: {'YES' if converged else 'NO'}  \n\n"
    )

    sections = [header, "## Full Matsya Output\n\n", output, "\n"]

    if final_yaml:
        sections.extend([
            "\n## Final YAML\n\n```yaml\n",
            final_yaml,
            "\n```\n",
        ])

    if not converged:
        sections.extend([
            "\n## Non-Convergence Notes\n\n",
            "The refinement did NOT converge within the iteration limit.\n",
            "Review the diffs in the full output above to see what is still changing.\n",
        ])

    out_path.write_text("".join(sections))
    print(f"  Saved output to {out_path}")

    if converged:
        print(f"  CONVERGED")
    else:
        print(f"  DID NOT CONVERGE (see {out_path} for details)")

    return converged


def main():
    parser = argparse.ArgumentParser(
        description="Refine housing-renting stage YAMLs via Matsya round-trips"
    )
    parser.add_argument(
        "stage",
        nargs="?",
        choices=STAGE_NAMES,
        help="Stage to refine (omit for --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Refine all 5 stages sequentially",
    )
    parser.add_argument(
        "--model",
        default="gpt5.2pro",
        help="LLM model for matsya (default: gpt5.2pro)",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=4,
        help="Max refinement iterations (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling matsya",
    )
    args = parser.parse_args()

    if not args.stage and not args.all:
        parser.error("Provide a stage name or --all")

    stages = STAGE_NAMES if args.all else [args.stage]
    results = {}

    for stage in stages:
        results[stage] = refine_stage(stage, args.model, args.max_iter, args.dry_run)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for stage, converged in results.items():
        status = "CONVERGED" if converged else "DID NOT CONVERGE"
        print(f"  {stage:20s}  {status}")

    not_converged = [s for s, c in results.items() if not c]
    if not_converged:
        print(f"\nStages that did NOT converge: {', '.join(not_converged)}")
        print(f"Review their output files in {OUTPUT_DIR}/")

    print("\nDone. Source files were NOT modified.")
    print(f"Converged outputs saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
