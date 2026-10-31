"""
ffp_plots — Dual-theme (light/dark) plotting for the FFP notebook.

Generates value-function and policy-function 2x2 figures in both
light and dark colour schemes.  The notebook displays them via
base64-encoded HTML with CSS class switching (.nb-plot--light /
.nb-plot--dark), so the correct version appears automatically
when the reader toggles the site theme.
"""

from __future__ import annotations

import base64
import io

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import rcParams

# ── Theme palettes ──────────────────────────────────────────────

PALETTES = {
    False: dict(                              # light
        colors=['#3b82f6', '#f97316', '#10b981', '#a855f7'],
        bg='#ffffff', txt='#374151', grd='#e5e7eb', spn='#d1d5db'),
    True: dict(                               # dark
        colors=['#60a5fa', '#fb923c', '#34d399', '#c084fc'],
        bg='#1a1a2e', txt='#e2e8f0', grd='#334155', spn='#475569'),
}


# ── Low-level helpers ───────────────────────────────────────────

def _apply_theme(ax, dark):
    """Style a single Axes for the given theme."""
    p = PALETTES[dark]
    ax.set_facecolor(p['bg'])
    ax.tick_params(colors=p['txt'], labelsize=8)
    for lbl in (ax.xaxis.label, ax.yaxis.label, ax.title):
        lbl.set_color(p['txt'])
    ax.grid(True, alpha=0.4, color=p['grd'], linewidth=0.5)
    for s in ax.spines.values():
        s.set_color(p['spn'])
        s.set_linewidth(0.6)


def _add_legend(ax, dark, **kwargs):
    p = PALETTES[dark]
    defaults = dict(fontsize=7, framealpha=0.6, edgecolor='none',
                    facecolor=p['bg'], labelcolor=p['txt'])
    defaults.update(kwargs)
    ax.legend(**defaults)


def _setup_rc():
    rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Source Sans Pro', 'Helvetica Neue', 'Arial'],
        'font.size': 9,
    })


def _figure(dark):
    """A 2x2 figure on the theme's background, with the theme's palette."""
    _setup_rc()
    p = PALETTES[dark]
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))
    fig.patch.set_facecolor(p['bg'])
    return fig, axes, p


def _label_panel(ax, dark, title, xlabel, ylim=None, **legend):
    """The title, x label and y range of one panel, then its theme and
    legend."""
    ax.set_title(title, fontsize=10, fontweight='600')
    ax.set_xlabel(xlabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    _apply_theme(ax, dark)
    _add_legend(ax, dark, **legend)


def _finish(fig, p, title):
    fig.suptitle(title, fontsize=12, fontweight='700', color=p['txt'], y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


# ── Figure builders ─────────────────────────────────────────────

def make_value_fig(trellis_co, trellis_br, trellis_bv, trellis_er, trellis_po, H,
                   *, dark=False):
    """2x2 value-function figure."""
    fig, axes, p = _figure(dark)
    c = p['colors']
    hs = [0, H // 2, H]

    # (0,0) Cons-only V(k)
    ax = axes[0, 0]
    for i, h in enumerate(hs):
        V = trellis_co['solutions'][h]['k']
        ax.plot(V.grid, V.values, color=c[i], lw=1.6, label=f'h = {h}')
    _label_panel(ax, dark, 'Cons-only: V(k)', 'k')

    # (0,1) Beginning-returns V(k) — EGM vs VFI
    ax = axes[0, 1]
    for i, h in enumerate(hs):
        Ve = trellis_br['solutions'][h]['k']
        Vv = trellis_bv['solutions'][h]['k']
        ax.plot(Ve.grid, Ve.values, '-', color=c[i], lw=1.6,
                label=f'h = {h} EGM')
        ax.plot(Vv.grid, Vv.values, '--', color=c[i], lw=1.2,
                alpha=0.7, label=f'h = {h} VFI')
    _label_panel(ax, dark, 'Beg-returns: V(k)', 'k', fontsize=6.5, ncol=2)

    # (1,0) End-returns V(m)
    ax = axes[1, 0]
    for i, h in enumerate(hs):
        V = trellis_er['solutions'][h]['m']
        ax.plot(V.grid, V.values, color=c[i], lw=1.6, label=f'h = {h}')
    _label_panel(ax, dark, 'End-returns: V(m)', 'm')

    # (1,1) Port-only V(k)
    ax = axes[1, 1]
    for i, h in enumerate(hs):
        V = trellis_po['solutions'][h]['k']
        ax.plot(V.grid, V.values, color=c[i], lw=1.6, label=f'h = {h}')
    _label_panel(ax, dark, 'Port-only: V(k)', 'k')

    return _finish(fig, p, 'Value Functions \u2014 Four Configurations')


def make_policy_fig(trellis_co, trellis_br, trellis_bv, trellis_er, trellis_po, H,
                    *, dark=False):
    """2x2 policy-function figure."""
    fig, axes, p = _figure(dark)
    c = p['colors']
    hs = [0, H // 2, H]

    # (0,0) Cons-only c(m)
    ax = axes[0, 0]
    for i, h in enumerate(hs):
        V = trellis_co['solutions'][h]['k']
        if hasattr(V, 'policy') and 'c' in V.policy:
            ax.plot(V.grid, V.policy['c'], color=c[i], lw=1.6,
                    label=f'h = {h}')
    _label_panel(ax, dark, 'Cons-only: c(m)', 'm')

    # (0,1) Beginning-returns c(m) — EGM vs VFI
    ax = axes[0, 1]
    for i, h in enumerate(hs):
        ce = trellis_br['solutions'][h].get('m')
        cv = trellis_bv['solutions'][h].get('m')
        if ce and hasattr(ce, 'policy') and 'c' in ce.policy:
            ax.plot(ce.grid, ce.policy['c'], '-', color=c[i], lw=1.6,
                    label=f'h = {h} EGM')
        if cv and hasattr(cv, 'policy') and 'c' in cv.policy:
            ax.plot(cv.grid, cv.policy['c'], '--', color=c[i], lw=1.2,
                    alpha=0.7, label=f'h = {h} VFI')
    _label_panel(ax, dark, 'Beg-returns: c(m)', 'm', fontsize=6.5, ncol=2)

    # (1,0) End-returns varsigma(k)
    ax = axes[1, 0]
    for i, h in enumerate(hs):
        Vk = trellis_er['solutions'][h].get('k')
        if Vk and hasattr(Vk, 'policy') and 'varsigma' in Vk.policy:
            ax.plot(Vk.grid, Vk.policy['varsigma'], color=c[i], lw=1.6,
                    label=f'h = {h}')
    _label_panel(ax, dark, r'End-returns: $\varsigma(k)$', 'k', ylim=(-0.05, 1.05))

    # (1,1) Port-only varsigma(k)
    ax = axes[1, 1]
    for i, h in enumerate(hs):
        V = trellis_po['solutions'][h]['k']
        if hasattr(V, 'policy') and 'varsigma' in V.policy:
            ax.plot(V.grid, V.policy['varsigma'], color=c[i], lw=1.6,
                    label=f'h = {h}')
    _label_panel(ax, dark, r'Port-only: $\varsigma(k)$', 'k', ylim=(-0.05, 1.05))

    return _finish(fig, p, 'Policy Functions \u2014 Four Configurations')


# ── Semiconjugacy demo figure ──────────────────────────────────

def make_semiconj_fig(V_br, V_beg_recovered, V_m_beg,
                      V_er, V_end_recovered,
                      n, beta, *, dark=False):
    """2x2 figure: direct vs semiconjugacy-recovered value & consumption."""
    fig, axes, p = _figure(dark)
    c_dir, c_rec = p['colors'][0], p['colors'][1]  # blue, orange

    # (0,0) Beg-returns V(k)
    ax = axes[0, 0]
    ax.plot(V_br.grid, V_br.values, '-', color=c_dir, lw=1.6,
            label='direct')
    ax.plot(V_beg_recovered.grid, V_beg_recovered.values, '--',
            color=c_rec, lw=1.4, label='recovered')
    _label_panel(ax, dark, 'Beg-returns: V(k)', 'k')

    # (0,1) End-returns V(m)
    ax = axes[0, 1]
    ax.plot(V_er.grid, V_er.values, '-', color=c_dir, lw=1.6,
            label='direct')
    ax.plot(V_end_recovered.grid, V_end_recovered.values, '--',
            color=c_rec, lw=1.4, label='recovered')
    _label_panel(ax, dark, 'End-returns: V(m)', 'm')

    # (1,0) Beg-returns c(m)
    ax = axes[1, 0]
    V_cons_dir = V_br.policy.get('_cons_stage')
    if V_cons_dir is not None and hasattr(V_cons_dir, 'policy'):
        if 'c' in V_cons_dir.policy:
            ax.plot(V_cons_dir.grid, V_cons_dir.policy['c'], '-',
                    color=c_dir, lw=1.6, label='direct')
    if hasattr(V_m_beg, 'policy') and 'c' in V_m_beg.policy:
        ax.plot(V_m_beg.grid, V_m_beg.policy['c'], '--',
                color=c_rec, lw=1.4, label='recovered')
    _label_panel(ax, dark, 'Beg-returns: c(m)', 'm')

    # (1,1) End-returns c(m)
    ax = axes[1, 1]
    if hasattr(V_er, 'policy') and 'c' in V_er.policy:
        ax.plot(V_er.grid, V_er.policy['c'], '-',
                color=c_dir, lw=1.6, label='direct')
    if hasattr(V_end_recovered, 'policy') and 'c' in V_end_recovered.policy:
        ax.plot(V_end_recovered.grid, V_end_recovered.policy['c'], '--',
                color=c_rec, lw=1.4, label='recovered')
    _label_panel(ax, dark, 'End-returns: c(m)', 'm')

    return _finish(fig, p, f'Order Semiconjugacy \u2014 Direct vs Recovered '
                           f'({n} steps, \u03b2 = {beta:.2f})')


def display_semiconj_plots(V_br, V_beg_recovered, V_m_beg,
                           V_er, V_end_recovered,
                           n, beta):
    """Display dual-theme semiconjugacy plots in a notebook."""
    from IPython.display import HTML, display

    args = (V_br, V_beg_recovered, V_m_beg,
            V_er, V_end_recovered, n, beta)

    b64_l = fig_to_b64(make_semiconj_fig(*args, dark=False))
    b64_d = fig_to_b64(make_semiconj_fig(*args, dark=True))

    # Save PNGs for external use (slides, docs)
    for name, dark in [('figures/semiconj_dark.png', True),
                       ('figures/semiconj_light.png', False)]:
        fig = make_semiconj_fig(*args, dark=dark)
        fig.savefig(name, dpi=150, facecolor=fig.get_facecolor(),
                    bbox_inches='tight', pad_inches=0.15)
        plt.close(fig)

    # Save split halves for slides (1×2 each)
    for dark in [True, False]:
        suffix = 'dark' if dark else 'light'
        fig = make_semiconj_fig(*args, dark=dark)
        # Top row: value functions
        for ax in fig.axes[2:]:
            ax.set_visible(False)
        fig.suptitle('')
        fig.savefig(f'figures/semiconj_values_{suffix}.png', dpi=150,
                    facecolor=fig.get_facecolor(),
                    bbox_inches='tight', pad_inches=0.15)
        plt.close(fig)
        # Bottom row: policies
        fig = make_semiconj_fig(*args, dark=dark)
        for ax in fig.axes[:2]:
            ax.set_visible(False)
        fig.suptitle('')
        fig.savefig(f'figures/semiconj_policies_{suffix}.png', dpi=150,
                    facecolor=fig.get_facecolor(),
                    bbox_inches='tight', pad_inches=0.15)
        plt.close(fig)

    display(HTML(dual_img_html(b64_l, b64_d, 'Semiconjugacy comparison')))


# ── Encoding / HTML helpers ─────────────────────────────────────

def fig_to_b64(fig):
    """Render a matplotlib Figure to a base64 PNG string and close it."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150,
                facecolor=fig.get_facecolor(),
                bbox_inches='tight', pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def dual_img_html(b64_light, b64_dark, alt='plot'):
    """Return an HTML string with light/dark <img> tags for CSS switching."""
    return (
        f'<img class="nb-plot nb-plot--light" alt="{alt}" '
        f'src="data:image/png;base64,{b64_light}"/>'
        f'<img class="nb-plot nb-plot--dark" alt="{alt}" '
        f'src="data:image/png;base64,{b64_dark}"/>'
    )


def display_dual_plots(trellis_co, trellis_br, trellis_bv, trellis_er, trellis_po, H):
    """Generate and display dual-theme value + policy plots in a notebook.

    Also saves light/dark PNGs to the working directory.
    """
    from IPython.display import HTML, display

    args = (trellis_co, trellis_br, trellis_bv, trellis_er, trellis_po, H)

    b64_vl = fig_to_b64(make_value_fig(*args, dark=False))
    b64_vd = fig_to_b64(make_value_fig(*args, dark=True))
    b64_pl = fig_to_b64(make_policy_fig(*args, dark=False))
    b64_pd = fig_to_b64(make_policy_fig(*args, dark=True))

    # Save PNGs for external use
    for name, dark in [('figures/plot_values_light.png', False),
                       ('figures/plot_values_dark.png', True),
                       ('figures/plot_policies_light.png', False),
                       ('figures/plot_policies_dark.png', True)]:
        fig = (make_value_fig(*args, dark=dark) if 'values' in name
               else make_policy_fig(*args, dark=dark))
        fig.savefig(name, dpi=150, facecolor=fig.get_facecolor(),
                    bbox_inches='tight', pad_inches=0.15)
        plt.close(fig)

    display(HTML(dual_img_html(b64_vl, b64_vd, 'Value functions')))
    display(HTML(dual_img_html(b64_pl, b64_pd, 'Policy functions')))
    print('Plots saved (4 PNGs) and displayed with light/dark theme switching.')
