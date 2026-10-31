"""
ffp_utils — Reusable infrastructure for the FFP (Functional Financial Programming)
portfolio-consumption notebook.

Extracts from the notebook:
  - ValueFn class
  - Equation compiler (Ρ map for individual equations)
  - Stage loading / binding
  - Stage operator factories (EGM, VFI, expectation, disc)
  - Inter-period connector + period operator factory

Design:
  - Beta is NOT baked into cons operators.  A separate disc operator
    multiplies the continuation by beta before economic stages see it.
  - The matsya_recipe is a module-level dict set from the notebook
    via set_recipe().
"""

from __future__ import annotations

import re as _re
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import yaml

# ═══════════════════════════════════════════════════════════════
# Repo bootstrap + library path
# ═══════════════════════════════════════════════════════════════

def _repo_root():
    p = Path(__file__).resolve().parent
    for cand in [p] + list(p.parents):
        if (cand / "packages" / "legacy" / "dolo").exists():
            return cand
    raise RuntimeError("Could not locate repo root")


def _legacy_library():
    """Put the archived dolang and dolo of packages/legacy/ on the import
    path, dolo first, once. Each function that imports them calls this first,
    so that this module imports without the archived packages; where
    packages/legacy/ is absent the call raises the RuntimeError of
    _repo_root."""
    import sys
    root = _repo_root()
    for name in ("dolang", "dolo"):
        path = str(root / "packages" / "legacy" / name)
        if path not in sys.path:
            sys.path.insert(0, path)


# ═══════════════════════════════════════════════════════════════
# Settings loader
# ═══════════════════════════════════════════════════════════════

def load_settings(path):
    """Load settings.yaml and return the settings dict."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    return raw.get('settings', raw)


def _expmult_grid(maxval, size, timestonest=20):
    """Multi-exponentially nested grid on [~0, maxval] (SolvingMicroDSOPs ``setup_grids_expMult``).

    Points are spaced so the growth rate from each point to the next is constant — concentrating
    points near the constraint at 0 — by nesting ``log(·+1)`` ``timestonest`` times. The minimum is
    not a free parameter here; the grid starts just above 0, exactly as in SolvingMicroDSOPs.
    """
    g = float(maxval)
    for _ in range(int(timestonest)):
        g = np.log(g + 1.0)
    index = g / float(size)
    points = np.empty(int(size))
    point = g
    for j in range(1, int(size) + 1):
        points[size - j] = np.exp(point) - 1.0
        point = point - index
        for _ in range(2, int(timestonest) + 1):
            points[size - j] = np.exp(points[size - j]) - 1.0
    return points


def build_grids(settings):
    """Build grids from settings.yaml values.

    Returns a dict with keys 'a', 'k', 'm' — each a 1D numpy array. Bounds and sizes come from the
    settings layer (Ρ-level). When ``grid_spacing: expmult`` is set, the assets and capital grids
    (a, k) use SolvingMicroDSOPs multi-exponential nesting; the cash-on-hand grid (m) is always
    linear. Absent the flag the grids are linear, so other apps are unaffected.
    """
    spacing = str(settings.get('grid_spacing', 'linear')).lower()
    if spacing == 'expmult':
        a = _expmult_grid(float(settings['a_max']), int(settings['n_a']))
        k = _expmult_grid(float(settings['k_max']), int(settings['n_k']))
    else:
        a = np.linspace(float(settings.get('a_min', 1e-6)),
                        float(settings['a_max']), int(settings['n_a']))
        k = np.linspace(float(settings['k_min']),
                        float(settings['k_max']), int(settings['n_k']))
    return {
        'a': a,
        'k': k,
        'm': np.linspace(float(settings['m_min']),
                         float(settings['m_max']),
                         int(settings['n_m'])),
    }


# ═══════════════════════════════════════════════════════════════
# ValueFn — a value function on a grid (callable, composable)
# ═══════════════════════════════════════════════════════════════

class ValueFn:
    """Value function on a 1D grid.  Callable via linear interpolation."""

    def __init__(self, grid, values, dvalues=None, policy=None):
        self.grid = np.asarray(grid)
        self.values = np.asarray(values)
        self.dvalues = np.asarray(dvalues) if dvalues is not None else None
        self.policy = policy or {}

    def __call__(self, x):
        return np.interp(x, self.grid, self.values)

    def dV(self, x):
        """Marginal value dV(x) — the DDSL dV[>] when used as continuation."""
        if self.dvalues is not None:
            return np.interp(x, self.grid, self.dvalues)
        return np.interp(x, self.grid, np.gradient(self.values, self.grid))

    def __repr__(self):
        return (f"ValueFn(n={len(self.grid)}, "
                f"range=[{self.values.min():.4f}, {self.values.max():.4f}])")


# ═══════════════════════════════════════════════════════════════
# Equation compiler (the Ρ map for individual equations)
# ═══════════════════════════════════════════════════════════════

_UNICODE_TO_ASCII = {
    'β': 'beta', 'ρ': 'rho',
    'μ_Ψ': 'mu_Psi', 'σ_Ψ': 'sigma_Psi',
    'μ_θ': 'mu_theta', 'σ_θ': 'sigma_theta',
    'ρ_ζ': 'rho_zeta',
}


def _sanitize_expr(expr, _calib=None):
    s = expr
    s = s.replace('^', '**')
    s = _re.sub(r'(\w+)\[>\]', r'\1_cntn', s)
    s = _re.sub(r'(\w+)\[<\]', r'\1_arvl', s)
    return s


def _sanitize_lhs(lhs):
    s = lhs.strip()
    s = _re.sub(r'(\w+)\[>\]', r'\1_cntn', s)
    s = _re.sub(r'(\w+)\[<\]', r'\1_arvl', s)
    return s


def _ns_with_ascii(calib):
    ns = {k: float(v) for k, v in calib.items()}
    for uk, ak in _UNICODE_TO_ASCII.items():
        if uk in ns:
            ns[ak] = ns[uk]
    ns['np'] = np
    return ns


def compile_eq(eq_str, calib):
    lhs_raw, rhs_raw = eq_str.split('=', 1)
    lhs = _sanitize_lhs(lhs_raw)
    rhs = _sanitize_expr(rhs_raw.strip(), calib)
    bound = {k: float(v) for k, v in calib.items()}
    bound['np'] = np
    code = compile(rhs, f'<eq: {lhs_raw.strip()} = {rhs_raw.strip()}>', 'eval')

    def fn(**kw):
        ns = {**bound, **kw}
        return eval(code, {'__builtins__': {}, 'np': np}, ns)

    fn._eq = f'{lhs} = {rhs}'
    fn._lhs = lhs
    fn._raw = eq_str.strip()
    return fn


def compile_eqs_from_block(block, calib):
    if isinstance(block, list):
        lines = block
    elif isinstance(block, str):
        lines = [l.strip() for l in block.strip().split('\n')]
    else:
        return {}
    fns = {}
    for line in lines:
        line = line.strip()
        if not line or '=' not in line:
            continue
        rhs = line.split('=', 1)[1]
        if any(op in rhs for op in ['max_{', 'argmax_{', 'E_{']):
            continue
        try:
            fn = compile_eq(line, calib)
            fns[fn._lhs] = fn
        except SyntaxError:
            pass
    return fns


def _read_equation_block(stage_data, *keys):
    """Read an equations block directly from the stage YAML AST as a list of
    equation strings, robust to the spec-0.3 list form.

    ``extract_raw_equations`` (the doloplus_translator helper) only handles
    block-scalar / mapping equation values; against the spec-0.3 list form
    (``dcsn_to_cntn:\n  - m = k_d*R + θ``) it returns nothing, so the transition
    reads downstream need a sequence-aware reader. This walks the YAML AST and
    returns the bare equation lines for the FIRST of *keys* that is present
    (e.g. the new ``dcsn_to_cntn`` or the legacy ``dcsn_to_cntn_transition``).
    Named sub-items (``- reward: u = ...``) contribute their equation text too.
    """
    _legacy_library()
    from dolo.compiler.stage_factory.symbolic import mapping_get, mapping_items
    import yaml as _yaml

    eqs_node = mapping_get(stage_data, "equations")
    if eqs_node is None:
        return []

    def _clean(text):
        out = []
        for raw in str(text).strip().split("\n"):
            cleaned = raw.split("#")[0].strip()
            if cleaned:
                out.append(cleaned)
        return out

    for key in keys:
        val = mapping_get(eqs_node, key)
        if val is None:
            continue
        lines = []
        if isinstance(val, _yaml.ScalarNode):
            lines.extend(_clean(val.value))
        elif isinstance(val, _yaml.MappingNode):
            for _sk, sv in mapping_items(val):
                if isinstance(sv, _yaml.ScalarNode):
                    lines.extend(_clean(sv.value))
        elif isinstance(val, _yaml.SequenceNode):
            for item in val.value:
                if isinstance(item, _yaml.ScalarNode):
                    lines.extend(_clean(item.value))
                elif isinstance(item, _yaml.MappingNode):
                    for _sk, sv in mapping_items(item):
                        if isinstance(sv, _yaml.ScalarNode):
                            lines.extend(_clean(sv.value))
        if lines:
            return lines
    return []


# ═══════════════════════════════════════════════════════════════
# Stage loading
# ═══════════════════════════════════════════════════════════════

def load_stage(name, lib):
    """Load a symbolic stage from a YAML file on disk."""
    _legacy_library()
    from dolo.compiler.doloplus_translator.core import strip_equation_comments_from_data
    from dolo.compiler.stage_factory import SymbolicModel

    path = Path(lib) / f"{name}.yaml"
    with open(path) as f:
        data = yaml.compose(f.read())
    strip_equation_comments_from_data(data)
    return SymbolicModel(data, filename=str(path))


def load_stage_from_string(yaml_text, name='<matsya>'):
    """Build a SymbolicModel from a YAML string (e.g. Matsya output)."""
    _legacy_library()
    from dolo.compiler.doloplus_translator.core import strip_equation_comments_from_data
    from dolo.compiler.stage_factory import SymbolicModel

    data = yaml.compose(yaml_text)
    strip_equation_comments_from_data(data)
    return SymbolicModel(data, filename=name)


def bind_stage(stage, methods, settings, params):
    """Apply the full binding pipeline to a symbolic stage.

    All inputs are in-memory objects (loaded at I/O boundary).
    Pipeline: methodize → configure → calibrate.
    """
    _legacy_library()
    from dolo.compiler.methodization import load_methodization
    from dolo.compiler.stage_factory import calibrate as calibrate_stage, configure as configure_stage
    from dolo.compiler.stage_factory import methodize as methodize_stage

    s = methodize_stage(stage, methods)
    s = configure_stage(s, settings)
    s = calibrate_stage(s, params)
    # Keep the full normalized methods list alongside the stage. methodize only
    # retains targets it can extract from the equations block, which against the
    # spec-0.3 list-form stage YAML excludes the node-targeted nodes (`policy`,
    # `evaluate`, …), leaving `stage.methods` empty. The full normalized list is
    # what `_extract_stage_config` dispatches on.
    try:
        s._app_methods = load_methodization(methods).get("methods", [])
    except Exception:
        s._app_methods = list((stage.methods or {}).values()) if getattr(stage, "methods", None) else []
    return s


def display_stage_yaml(path, repo_root=None):
    """Read a stage YAML, strip comments/metadata, and display it as HTML.

    Strips full-line comments, inline comments, the ``dolo_plus:`` metadata
    block, and trailing blank lines so the reader sees only the meaningful
    YAML structure.
    """
    from IPython.display import HTML, display as _display

    text = Path(path).read_text()
    lines = []
    in_metadata = False
    for raw in text.splitlines():
        if raw.rstrip() == 'dolo_plus:':
            in_metadata = True
        if in_metadata:
            continue
        if raw.strip().startswith('#'):
            continue
        stripped = raw.split('#')[0].rstrip() if '#' in raw else raw.rstrip()
        lines.append(stripped)

    while lines and not lines[-1].strip():
        lines.pop()

    clean = '\n'.join(lines)
    escaped = clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    rel = Path(path)
    if repo_root is not None:
        try:
            rel = Path(path).relative_to(repo_root)
        except ValueError:
            pass

    _display(HTML(
        f"<p><strong>Canonical source</strong>: <code>{rel}</code></p>"
        f"<pre><code class='language-yaml'>{escaped}</code></pre>"
    ))


# ═══════════════════════════════════════════════════════════════
# Save Matsya-generated YAML
# ═══════════════════════════════════════════════════════════════

_MATSYA_OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'notebooks' / 'port-cons' / 'artifacts' / 'matsya'


def save_matsya_yaml(yaml_text, stage_name):
    """Save Matsya-generated YAML to matsya_output/ with a timestamp.

    Returns the path written, or None if *yaml_text* is falsy.
    """
    if not yaml_text:
        return None
    from datetime import datetime
    _MATSYA_OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    path = _MATSYA_OUTPUT_DIR / f'{stage_name}_{ts}.yaml'
    path.write_text(yaml_text)
    return path


# ═══════════════════════════════════════════════════════════════
# Stage config extraction
# ═══════════════════════════════════════════════════════════════

def _extract_stage_config(stage):
    # The solution method (egm / vfi) and the value grid live on node-targeted
    # entries in the spec-0.3 methodization YAML (spec 0.1d.1 / kernel-policy
    # spec 0.3): the solution method sits FLAT on the ``policy`` node
    # (``on: policy`` / ``method: !egm``), and the value grid FLAT on the
    # ``evaluate`` node (``on: evaluate`` / ``settings: {orders, bounds}``); cons
    # targets the evaluate sub-nodes with a comma-joined ``on:`` string. The old
    # single ``cntn_to_dcsn_builder`` node (with a ``schemes:`` list) is read as a
    # fallback so any pre-split methodization still works.
    #
    # ``load_methodization`` normalizes both surfaces to ``{'on': node, 'schemes':
    # [block]}``; each block carries ``method`` (``{'__yaml_tag__': 'egm'}``) and
    # optional ``settings``. The full list is read from ``stage._app_methods``
    # (attached in ``bind_stage``) because methodize drops node-targeted nodes it
    # cannot extract from the list-form equations, leaving ``stage.methods`` empty.
    entries = getattr(stage, '_app_methods', None)
    if not entries:
        entries = list((stage.methods or {}).values())

    def _tag(block):
        _m = block.get('method', {})
        return (_m.get('__yaml_tag__', '?') if isinstance(_m, dict) else str(_m))

    # --- solution method: the `policy` node (new), else `cntn_to_dcsn_builder` ---
    method = None
    for _e in entries:
        if _e.get('on') == 'policy':
            for _sch in _e.get('schemes', []):
                _t = _tag(_sch)
                if _t and _t not in ('?', 'unknown'):
                    method = _t
                    break
        if method is not None:
            break
    if method is None:
        for _e in entries:
            if _e.get('on') == 'cntn_to_dcsn_builder':
                for _sch in _e.get('schemes', []):
                    if _sch.get('scheme') == 'bellman_backward':
                        method = _tag(_sch)
                        break
            if method is not None:
                break
    if method is None:
        # A stage with no ``policy`` node makes no decision — it is an
        # expectation / transition-only stage (e.g. noport_stage) realised by the
        # expectation operator.
        method = 'expectation'

    calib = stage.calibration
    settings = stage.settings or {}

    # --- value grid: any node whose `on` mentions `evaluate` (new), else the
    #     legacy grid/interpolation scheme on `cntn_to_dcsn_builder` ---
    n, (lo, hi) = 100, (0.01, 10.0)

    def _resolve(_ss):
        _orders = [int(settings.get(str(o), o)) for o in _ss.get('orders', [])]
        _bounds = [(float(settings.get(str(p[0]), p[0])),
                    float(settings.get(str(p[1]), p[1])))
                   for p in _ss.get('bounds', [[]]) if len(p) == 2]
        _n = _orders[0] if _orders else 100
        _b = _bounds[0] if _bounds else (0.01, 10.0)
        return _n, _b[0], _b[1]

    _matched = False
    for _e in entries:
        if 'evaluate' not in str(_e.get('on', '')):
            continue
        for _sch in _e.get('schemes', []):
            _ss = _sch.get('settings', {})
            if 'orders' in _ss or 'bounds' in _ss:
                n, lo, hi = _resolve(_ss)
                _matched = True
                break
        if _matched:
            break
    if not _matched:
        for _e in entries:
            if _e.get('on') != 'cntn_to_dcsn_builder':
                continue
            for _sch in _e.get('schemes', []):
                if _sch.get('scheme') in ('grid', 'interpolation'):
                    n, lo, hi = _resolve(_sch.get('settings', {}))
                    _matched = True
                    break
            if _matched:
                break

    grid = np.linspace(lo, hi, n)
    return method, calib, settings, grid


# ═══════════════════════════════════════════════════════════════
# Matsya recipe (module-level, set from notebook)
# ═══════════════════════════════════════════════════════════════

FALLBACK_RECIPE = {
    "vfi_maximand":            "(c**(1-rho))/(1-rho) + V_cont(m_d - c)",
    "inv_euler":               "(dV_cont(a))**(-1/rho)",
    "cntn_to_dcsn_transition": "a + c",
    "marginal_bellman":        "c**(-rho)",
    "dcsn_to_cntn_transition": "m_d - c",
    "utility":                 "(c**(1-rho))/(1-rho)",
}

matsya_recipe = dict(FALLBACK_RECIPE)


def set_recipe(recipe):
    """Set the active matsya recipe (called from notebook after de-sugaring).

    Missing keys fall back to FALLBACK_RECIPE so callers need not
    supply every entry (e.g. Matsya may omit ``utility``).
    """
    global matsya_recipe
    matsya_recipe = {**FALLBACK_RECIPE, **dict(recipe)}


# ═══════════════════════════════════════════════════════════════
# Matsya CLI helper
# ═══════════════════════════════════════════════════════════════

def matsya_translate(prompt, *, refine=False, think=False, max_iter=3,
                     model='claude-opus-4-6', k=8, timeout=600):
    """Call econ-ark-matsya and return the generated YAML string, or None.

    Parameters
    ----------
    prompt : str
        The math-to-YAML prompt (may contain newlines — they are
        collapsed automatically).
    refine : bool
        If True, use ``--refine`` mode (YAML↔MDP round-tripping).
    think : bool
        If True, enable extended thinking via ``--think``.
    max_iter : int
        Max refinement iterations (only used when *refine* is True).
    model : str
        LLM model identifier.
    k : int
        Number of RAG chunks to retrieve.
    timeout : int
        Subprocess timeout in seconds.

    Returns
    -------
    str or None
        The extracted YAML block, or None if Matsya is unavailable.
    """
    import subprocess

    # Collapse newlines — the CLI embeds the query in a single-line
    # Python string on the remote host.
    flat = ' '.join(prompt.split())

    cmd = ['econ-ark-matsya', flat, '--llm',
           '--model', model, '--k', str(k)]
    if refine:
        cmd += ['--refine', '--max-iter', str(max_iter)]
    if think:
        cmd += ['--think']

    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if r.returncode != 0:
        return None

    text = r.stdout

    # --refine mode: look for "--- Final YAML ---"
    if refine:
        m = _re.search(r'---\s*Final YAML\s*---\s*\n(.*?)={10,}',
                        text, _re.DOTALL)
        if m and len(m.group(1).strip()) > 50:
            raw = m.group(1).strip()
            ym = _re.search(r'```ya?ml\s*\n(.*?)```', raw, _re.DOTALL)
            return ym.group(1).strip() if ym else raw

    # Standard / fallback: split on ===...=== separators
    parts = _re.split(r'={10,}', text)
    if len(parts) >= 3 and len(parts[2].strip()) > 50:
        raw = parts[2].strip()
        ym = _re.search(r'```ya?ml\s*\n(.*?)```', raw, _re.DOTALL)
        return ym.group(1).strip() if ym else raw

    return None


def matsya_desugar_recipe(stage_yaml_path, *, fallback=None,
                          model='claude-opus-4-6', k=5, timeout=120):
    """Ask Matsya to de-sugar a stage YAML into a beta-free solver recipe.

    Reads the stage YAML, builds a structured prompt, calls Matsya, and
    parses the returned JSON dict of Python expressions.  Falls back to
    *fallback* (or :data:`FALLBACK_RECIPE`) if Matsya is unavailable or
    returns invalid output.

    Returns
    -------
    tuple[dict, bool]
        ``(recipe, from_matsya)`` — the recipe dict and whether it came
        from the live Matsya service (True) or the fallback (False).
    """
    import json as _json
    import subprocess

    if fallback is None:
        fallback = FALLBACK_RECIPE

    # Read and strip comments from the stage YAML for the prompt.
    text = Path(stage_yaml_path).read_text()
    clean = '\n'.join(
        l for l in text.split('\n') if l.strip() and not l.strip().startswith('#')
    )

    query = (
        f"Here is the full dolo-plus cons_stage YAML:\n"
        f"```yaml\n{clean}\n```\n\n"
        f"In my solver code:\n"
        f"- V_cont(x) is the continuation value (this is V[>])\n"
        f"- dV_cont(x) is the marginal continuation value (this is dV[>])\n"
        f"- Beta is NOT in the recipe — a disc stage handles it\n"
        f"- The poststate grid variable is 'a', decision grid is 'm_d'\n\n"
        f"De-sugar all perch tags and return ONLY a JSON dict with keys:\n"
        f"  vfi_maximand, inv_euler, cntn_to_dcsn_transition, "
        f"marginal_bellman, dcsn_to_cntn_transition, utility\n\n"
        f"Rules:\n"
        f"- Valid Python, ** for exponentiation, no lambda\n"
        f"- Do NOT include beta — the disc stage multiplies continuation "
        f"by beta\n"
        f"- Use: a (poststate), m_d (decision), c (consumption), "
        f"rho (parameter)\n"
        f"- No prose, just JSON"
    )
    flat = ' '.join(query.split())

    try:
        r = subprocess.run(
            ['econ-ark-matsya', flat, '--llm',
             '--model', model, '--k', str(k)],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode == 0:
            parts = _re.split(r'={10,}', r.stdout)
            if len(parts) >= 3:
                answer = parts[2].strip()
                jm = _re.search(r'\{[^{}]*\}', answer, _re.DOTALL)
                if jm:
                    recipe = _json.loads(jm.group())
                    # Validate every expression compiles.
                    for kk, v in recipe.items():
                        compile(v, f'<recipe:{kk}>', 'eval')
                    return recipe, True
    except (FileNotFoundError, subprocess.TimeoutExpired,
            _json.JSONDecodeError, SyntaxError):
        pass

    return dict(fallback), False


def matsya_ask(prompt, *, model='claude-opus-4-6', k=8, think=False,
               timeout=300):
    """Ask Matsya a free-form question and return the full markdown answer.

    Unlike :func:`matsya_translate` (which extracts only YAML),
    this returns the raw answer text — typically markdown with
    embedded LaTeX equations — suitable for rendering via
    ``IPython.display.Markdown``.

    Parameters
    ----------
    prompt : str
        Free-form question (may contain LaTeX, newlines, etc.).
    model : str
        LLM model identifier.
    k : int
        Number of RAG chunks to retrieve.
    think : bool
        If True, enable extended thinking via ``--think``.
    timeout : int
        Subprocess timeout in seconds.

    Returns
    -------
    str or None
        The answer markdown, or None if Matsya is unavailable.
    """
    import subprocess

    flat = ' '.join(prompt.split())
    cmd = ['econ-ark-matsya', flat, '--llm',
           '--model', model, '--k', str(k)]
    if think:
        cmd += ['--think']

    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if r.returncode != 0:
        return None

    text = r.stdout

    # The answer section follows the second ===...=== separator.
    parts = _re.split(r'={10,}', text)
    if len(parts) >= 3:
        answer = parts[2].strip()
        if answer:
            return answer

    return None


# ═══════════════════════════════════════════════════════════════
# Operator: EGM consumption (beta-free)
# ═══════════════════════════════════════════════════════════════

def make_egm_cons_operator(stage, grid, calib, settings, verbose=True):
    """EGM operator for consumption stage.

    Beta-free: V = u + V_cont(a_policy).
    The disc operator scales the continuation before this stage sees it,
    so dV_cont already includes beta.

    ``verbose`` controls the one-line construction notice; it defaults to True
    to preserve the existing dispatcher behaviour, and is set to False by the
    notebook-facing ``make_egm_cons_builder`` so it does not leak stray output.
    """
    n_a = int(settings.get('n_a', 100))
    a_max = float(settings.get('a_max', grid[-1]))
    a_grid = np.linspace(1e-6, a_max, n_a)
    _ns = _ns_with_ascii(calib)

    if verbose:
        print(f"    {stage.name} (egm): EGM via recipe")

    def S_egm(V_cont: ValueFn) -> ValueFn:
        dV_cont = V_cont.dV
        ns = {**_ns, 'V_cont': V_cont, 'dV_cont': dV_cont, 'a': a_grid}

        # 1. InvEuler: c = (dV_cont(a))^(-1/rho)
        dV = dV_cont(a_grid)
        ns['dV'] = dV
        c_endo = eval(matsya_recipe['inv_euler'],
                      {'__builtins__': {}, 'np': np}, ns)

        # 2. cntn_to_dcsn_transition: m_d = a + c
        ns['c'] = c_endo
        m_endo = eval(matsya_recipe['cntn_to_dcsn_transition'],
                      {'__builtins__': {}, 'np': np}, ns)

        # 3. Interpolate to regular m_grid
        idx = np.argsort(m_endo)
        c_policy = np.clip(np.interp(grid, m_endo[idx], c_endo[idx]),
                           1e-10, grid - 1e-10)

        # 4. dcsn_to_cntn_transition: a = m_d - c
        ns_fwd = {**_ns, 'm_d': grid, 'c': c_policy, 'np': np}
        a_policy = np.clip(
            eval(matsya_recipe['dcsn_to_cntn_transition'],
                 {'__builtins__': {}, 'np': np}, ns_fwd),
            a_grid[0], a_grid[-1])

        # 5. Value: V = u + V_cont(a_policy)
        ns_u = {**_ns, 'c': c_policy, 'np': np}
        u = np.where(c_policy > 0,
                     eval(matsya_recipe['utility'],
                          {'__builtins__': {}, 'np': np}, ns_u),
                     -1e10)
        V = u + V_cont(a_policy)

        # 6. Envelope: dV = c^(-rho)
        dV_out = np.where(c_policy > 0,
                          eval(matsya_recipe['marginal_bellman'],
                               {'__builtins__': {}, 'np': np}, ns_u),
                          1e10)

        return ValueFn(grid, V, dV_out, {'c': c_policy, 'a': a_policy})

    S_egm._method = 'egm'
    S_egm._stage = stage.name
    return S_egm


# ═══════════════════════════════════════════════════════════════
# Operator: VFI consumption (beta-free)
# ═══════════════════════════════════════════════════════════════

def make_vfi_cons_operator(stage, grid, calib, settings):
    """VFI operator for consumption stage (no shocks).

    Beta-free: obj = u + V_cont(a).
    """
    # dcsn→cntn savings law: spec-0.3 key `dcsn_to_cntn`, legacy
    # `dcsn_to_cntn_transition`. _read_equation_block is sequence-aware.
    g_fns = compile_eqs_from_block(
        _read_equation_block(stage.data, 'dcsn_to_cntn', 'dcsn_to_cntn_transition'),
        calib)
    g_fn = list(g_fns.values())[0]
    # Flow utility: spec-0.3 backward block `cntn_to_dcsn` (named items
    # reward/dcsn_val), legacy `cntn_to_dcsn_builder.Bellman`.
    bl_fns = compile_eqs_from_block(
        _read_equation_block(stage.data, 'cntn_to_dcsn'), calib)
    u_fn = bl_fns.get('u')
    _ns_vfi = _ns_with_ascii(calib)

    print(f"    {stage.name} (vfi): {len(g_fns)} transition(s), "
          f"{len(bl_fns)} Bellman sub-eqs")

    def S_vfi(V_cont: ValueFn) -> ValueFn:
        V_out = np.full(len(grid), -1e10)
        c_pol = np.zeros(len(grid))
        for i, m_d_val in enumerate(grid):
            cc = np.linspace(1e-6, m_d_val - 1e-6, 200)
            if len(cc) == 0:
                continue
            aa = np.clip(g_fn(m_d=m_d_val, c=cc), grid[0], grid[-1])
            ns = {**_ns_vfi, 'V_cont': V_cont, 'm_d': m_d_val,
                  'c': cc, 'a': aa}
            if 'vfi_maximand' in matsya_recipe:
                obj = eval(matsya_recipe['vfi_maximand'],
                           {'__builtins__': {}, 'np': np}, ns)
            else:
                u_vals = (np.where(cc > 0, u_fn(c=cc), -1e10)
                          if u_fn else 0.0)
                obj = u_vals + V_cont(aa)
            obj = np.where(np.isfinite(obj), obj, -1e10)
            best = np.argmax(obj)
            V_out[i] = obj[best]
            c_pol[i] = cc[best]
        return ValueFn(grid, V_out, np.gradient(V_out, grid), {'c': c_pol})

    S_vfi._method = 'vfi'
    S_vfi._stage = stage.name
    return S_vfi


# ═══════════════════════════════════════════════════════════════
# Operator: VFI portfolio (unchanged — never had beta)
# ═══════════════════════════════════════════════════════════════

def make_vfi_port_operator(stage, grid, calib, settings):
    """VFI operator for portfolio stage (with shocks)."""
    _legacy_library()
    from dolo.numeric.distribution import Normal as MvNormal

    # dcsn→cntn returns+income law: spec-0.3 key `dcsn_to_cntn`, legacy
    # `dcsn_to_cntn_transition`. _read_equation_block is sequence-aware.
    g_fns = compile_eqs_from_block(
        _read_equation_block(stage.data, 'dcsn_to_cntn', 'dcsn_to_cntn_transition'),
        calib)
    g_fn = list(g_fns.values())[0]

    mu = np.array([float(calib['μ_Ψ']), float(calib['μ_θ'])])
    sig_Psi, sig_th = float(calib['σ_Ψ']), float(calib['σ_θ'])
    rho_z = float(calib.get('ρ_ζ', 0.0))
    Sigma = np.array([[sig_Psi**2, rho_z * sig_Psi * sig_th],
                      [rho_z * sig_Psi * sig_th, sig_th**2]])
    n_q = int(np.sqrt(int(settings.get('n_joint_nodes', 49))))
    disc = MvNormal(Σ=Sigma, Μ=mu).discretize(to='iid', N=n_q)
    Psi_n = np.exp(disc.points[:, 0])
    th_n = np.exp(disc.points[:, 1])
    weights = disc.weights

    print(f"    {stage.name} (vfi): {len(g_fns)} transition(s), "
          f"{len(weights)} quadrature points")

    def S_vfi_port(V_cont: ValueFn) -> ValueFn:
        n_k = len(grid)
        V_out = np.full(n_k, -1e10)
        s_pol = np.zeros(n_k)
        s_cands = np.linspace(0.0, 1.0, 50)

        for i, k_d in enumerate(grid):
            best_v, best_s = -1e10, 0.0
            for s in s_cands:
                m = g_fn(k_d=k_d, ς=s, Ψ=Psi_n, θ=th_n)
                m = np.clip(m, grid[0], grid[-1])
                EV = np.dot(weights, V_cont(m))
                if EV > best_v:
                    best_v, best_s = EV, s
            V_out[i] = best_v
            s_pol[i] = best_s

        return ValueFn(grid, V_out, np.gradient(V_out, grid),
                       {'varsigma': s_pol})

    S_vfi_port._method = 'vfi'
    S_vfi_port._stage = stage.name
    return S_vfi_port


# ═══════════════════════════════════════════════════════════════
# Operator: expectation (noport stage)
# ═══════════════════════════════════════════════════════════════

def make_expectation_noport_operator(stage, grid, calib, settings):  # noqa: ARG001 settings
    """Expectation-only operator for noport stage.

    V(k) = E_theta[ V_cont(k*R + theta) ]

    Compiles the transition from the YAML, discretizes univariate
    LogNormal theta via Gauss-Hermite.
    """
    _legacy_library()
    from dolo.numeric.distribution import Normal as MvNormal

    # dcsn→cntn law m = k_d*R + θ: spec-0.3 key `dcsn_to_cntn`, legacy
    # `dcsn_to_cntn_transition`. _read_equation_block is sequence-aware.
    g_fns = compile_eqs_from_block(
        _read_equation_block(stage.data, 'dcsn_to_cntn', 'dcsn_to_cntn_transition'),
        calib)
    g_fn = list(g_fns.values())[0]  # m = k_d*R + theta

    # Discretize univariate LogNormal theta
    mu_th = float(calib['μ_θ'])
    sig_th = float(calib['σ_θ'])
    n_nodes = int(settings.get('n_θ_nodes', 7))
    Sigma_1d = np.array([[sig_th**2]])
    mu_1d = np.array([mu_th])
    disc = MvNormal(Σ=Sigma_1d, Μ=mu_1d).discretize(to='iid', N=n_nodes)
    th_n = np.exp(disc.points[:, 0])
    weights = disc.weights

    print(f"    {stage.name} (expectation): {len(g_fns)} transition(s), "
          f"{len(weights)} quadrature points")

    def S_exp(V_cont: ValueFn) -> ValueFn:
        n_k = len(grid)
        V_out = np.zeros(n_k)
        dV_out = np.zeros(n_k)

        for i, k_d in enumerate(grid):
            m_vals = g_fn(k_d=k_d, θ=th_n)
            m_vals = np.clip(m_vals, V_cont.grid[0], V_cont.grid[-1])
            V_out[i] = np.dot(weights, V_cont(m_vals))
            dV_out[i] = np.dot(weights, V_cont.dV(m_vals))

        # Scale dV by R (chain rule: dV/dk = R * E[dV_cont])
        R = float(calib.get('R', 1.0))
        dV_out = R * dV_out

        return ValueFn(grid, V_out, dV_out, {})

    S_exp._method = 'expectation'
    S_exp._stage = stage.name
    return S_exp


# ═══════════════════════════════════════════════════════════════
# Operator: disc (discount factor)
# ═══════════════════════════════════════════════════════════════

def make_disc_operator(beta):
    """Discount operator: V(x) = beta * V_cont(x).

    Applied first in backward direction — wraps the continuation
    before economic stages see it.  This way EGM's inv_euler
    c = (dV_cont(a))^(-1/rho) with dV_cont = beta*dV_next gives
    c = (beta*dV_next)^(-1/rho), same math as beta baked in.
    """
    def S_disc(V_cont: ValueFn) -> ValueFn:
        return ValueFn(
            V_cont.grid,
            beta * V_cont.values,
            beta * V_cont.dvalues if V_cont.dvalues is not None else None,
            {},
        )

    S_disc._method = 'disc'
    S_disc._stage = 'disc'
    return S_disc


# ═══════════════════════════════════════════════════════════════
# Dispatcher
# ═══════════════════════════════════════════════════════════════

def make_stage_operator(stage):
    """Dispatch to the appropriate operator factory based on method tag."""
    method, calib, settings, grid = _extract_stage_config(stage)

    if method == 'egm':
        return make_egm_cons_operator(stage, grid, calib, settings)
    elif method == '!expectation' or method == 'expectation':
        return make_expectation_noport_operator(stage, grid, calib, settings)
    elif method == 'vfi' and stage.symbols.get('exogenous', []):
        return make_vfi_port_operator(stage, grid, calib, settings)
    elif method == 'vfi':
        return make_vfi_cons_operator(stage, grid, calib, settings)
    else:
        raise ValueError(f"Unsupported method '{method}' on {stage.name}")


# ═══════════════════════════════════════════════════════════════
# Inter-period connectors + period operator factory
# ═══════════════════════════════════════════════════════════════

def apply_inter_connector(solution: dict, inter_connector: dict) -> ValueFn:
    """Apply inter-period connector: look up VF by target field name."""
    target_field = list(inter_connector.values())[0]
    return solution[target_field]


def make_period_operator(period: dict, inter_connector: dict,
                         disc_operator=None):
    """Build a period operator from a structured period dict + inter-period connector.

    If disc_operator is provided, it is applied to the continuation
    BEFORE the economic stages see it (first in backward direction).

    The backward solve order is derived from the connector graph.
    """
    stages = period["stages"]
    connectors = period.get("connectors", [])

    # Build stage graph from symbols
    stage_graph = {}
    for name, obj in stages.items():
        if not hasattr(obj, 'symbols'):
            continue
        pre = obj.symbols.get('prestate', [])
        post = obj.symbols.get('poststates', [])
        stage_graph[name] = {
            'prestate': pre[0] if pre else None,
            'poststate': post[0] if post else None,
        }

    # Reverse connector lookup
    connector_reverse = {}
    for c in connectors:
        for src, tgt in c.items():
            connector_reverse[tgt] = src

    # Derive backward order from inter-period connector
    entry_field = list(inter_connector.keys())[0]

    backward_order = []
    current_field = entry_field
    visited = set()

    while current_field:
        found = None
        for name, info in stage_graph.items():
            if info['poststate'] == current_field and name not in visited:
                found = name
                break
        if found is None:
            break
        visited.add(found)
        backward_order.append(found)

        prestate = stage_graph[found]['prestate']
        current_field = connector_reverse.get(prestate, prestate)

    connector_info = (f", {len(connectors)} intra-connector(s)"
                      if connectors else "")
    disc_info = ", disc" if disc_operator else ""
    print(f"    backward order: {' → '.join(backward_order)}  "
          f"(entry: {entry_field!r}{connector_info}{disc_info})")

    # Build operators in backward order
    operators = [(name, make_stage_operator(stages[name]))
                 for name in backward_order]
    methods = {name: S._method for name, S in operators}

    def T_solve_period(V_cont: ValueFn) -> ValueFn:
        # Apply disc first (wraps continuation)
        V = disc_operator(V_cont) if disc_operator else V_cont
        stage_results = {}
        for name, S in operators:
            V = S(V)
            stage_results[name] = V
        for name, V_stage in stage_results.items():
            if name != backward_order[-1]:
                V.policy[f'_{name}'] = V_stage
        return V

    T_solve_period._is_period = True
    T_solve_period._backward_order = backward_order
    T_solve_period._methods = methods
    T_solve_period._cons_method = methods.get('cons_stage', '?')
    T_solve_period._port_method = methods.get('port_stage', '?')
    return T_solve_period
