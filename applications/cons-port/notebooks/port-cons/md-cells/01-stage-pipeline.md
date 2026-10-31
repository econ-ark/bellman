<!-- notebook cell 1 | id: kfg8kf7efb9 -->
<!-- auto-extracted from solve_port_cons_ffp.ipynb -->

### Stage pipeline

A single syntactic stage can be represented in several increasingly committed forms. We start with a purely symbolic and typed declaration of structure, then progressively bind to it (i) numerical parameter values, (ii) approximation methods for functions, and (iii) numerical approximation settings.

Only after those syntax-layer commitments do we compile executable callables for the stage, and finally apply it to produce solved objects and simulations.

It helps to read the pipeline as "one new commitment per step":

1. Symbolic: what the stage says (symbols for variables, parameters, and settings; equations; spaces), with no numbers and no solver choices.
2. Parameterized: the math is pinned down by binding calibrated parameter values (changing these changes the model).
3. Methodized: how we intend to solve it by attaching methods to functions (interpolation grids, EGM, VFI, quadrature, etc.).
4. Configured: how accurately we approximate it by binding numerical settings (grid sizes, tolerances, bounds).
5. Callable: an executable operator built from grids/interpolants/quadrature nodes—ready to be applied.
6. Solved: result objects (value + policy) produced by iterating the operator backwards.
7. Simulated: forward use of the policy to generate agent paths or distributions.

The key distinction is that steps 1–4 live in the syntax layer (they specify meaning + intended numerical treatment), while steps 5–7 live in computational representation and application (they build and use concrete executable objects). The Bellman calculus system specifies the structure of the syntactic layer of a stage, but it does not specify the structure of objects in the computational layer.[^1]

[^1]: Bellman calculus does specify thin syntax about how stages are composed into periods, periods into sequences, etc., but it does not specify the details of how grids are built, how interpolants are computed, etc.


<div style="text-align:center; margin:24px 0;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 395" style="width:280px; height:auto; color:inherit;">
  <defs>
    <style>
      .lc0 { stroke-linecap: round; }
      .lc0, .lc1, .lc2 { fill: none; stroke: currentColor; }
      .lc0, .lc2 { stroke-width: 1px; }
      .lc3 { font-family: Georgia, serif; font-style: italic; font-size: 7.5px; opacity: 0.4; fill: currentColor; }
      .lc4, .lc5, .lc6 { font-family: Menlo, Consolas, monospace; font-weight: 700; }
      .lc7, .lc8, .lc10, .lc11, .lc12, .lc13 { fill: currentColor; }
      .lc7, .lc14 { font-family: Inter, Helvetica, sans-serif; }
      .lc7, .lc10, .lc12 { font-size: 8.5px; }
      .lc1 { opacity: .22; stroke-dasharray: 3 3; stroke-width: .6px; }
      .lc8 { font-family: Inter, 'Helvetica Neue', sans-serif; font-size: 10.5px; font-weight: 500; }
      .lc11 { font-family: 'JetBrains Mono', Menlo, Consolas, monospace; font-size: 9.5px; }
      .lc12 { font-family: Georgia, serif; font-style: italic; }
    </style>
  </defs>
  <circle class="lc2" cx="36" cy="42" r="3.5"/>
  <text class="lc11" transform="translate(50 46)"><tspan x="0" y="0">SYNTAX</tspan></text>
  <line class="lc0" x1="36" y1="46" x2="36" y2="68"/>
  <text class="lc12" transform="translate(44 60)"><tspan x="0" y="0">parse</tspan></text>
  <circle class="lc13" cx="36" cy="74" r="3.5"/>
  <text class="lc8" transform="translate(50 78)"><tspan x="0" y="0">1 Symbolic stage</tspan></text>
  <text class="lc10" transform="translate(50 90)"><tspan class="lc14" x="0" y="0">structured syntax &#xB7;</tspan><tspan class="lc5" x="72" y="0">.mod file</tspan></text>
  <line class="lc0" x1="36" y1="96" x2="36" y2="114"/>
  <text class="lc12" transform="translate(44 108)"><tspan x="0" y="0">calibrate</tspan></text>
  <circle class="lc13" cx="36" cy="120" r="3.5"/>
  <text class="lc8" transform="translate(50 124)"><tspan x="0" y="0">2 Parameterized stage</tspan></text>
  <text class="lc10" transform="translate(50 136)"><tspan class="lc14" x="0" y="0">parameters mapped &#xB7;</tspan><tspan class="lc4" x="83" y="0">stage.param</tspan></text>
  <line class="lc0" x1="36" y1="142" x2="36" y2="160"/>
  <text class="lc12" transform="translate(44 154)"><tspan x="0" y="0">methodize</tspan></text>
  <circle class="lc13" cx="36" cy="166" r="3.5"/>
  <text class="lc8" transform="translate(50 170)"><tspan x="0" y="0">3 Methodized stage</tspan></text>
  <text class="lc10" transform="translate(50 182)"><tspan class="lc14" x="0" y="0">methods mapped &#xB7;</tspan><tspan class="lc6" x="73" y="0">stage.methods</tspan></text>
  <line class="lc0" x1="36" y1="188" x2="36" y2="206"/>
  <text class="lc12" transform="translate(44 200)"><tspan x="0" y="0">configure</tspan></text>
  <circle class="lc13" cx="36" cy="212" r="3.5"/>
  <text class="lc8" transform="translate(50 216)"><tspan x="0" y="0">4 Configured stage</tspan></text>
  <text class="lc10" transform="translate(50 228)"><tspan class="lc14" x="0" y="0">settings mapped &#xB7;</tspan><tspan class="lc4" x="70" y="0">stage.settings</tspan></text>
  <line class="lc1" x1="14" y1="242" x2="246" y2="242"/>
  <line class="lc0" x1="36" y1="234" x2="36" y2="258"/>
  <text class="lc12" transform="translate(44 252)"><tspan x="0" y="0">build</tspan></text>
  <circle class="lc13" cx="36" cy="264" r="3.5"/>
  <text class="lc8" transform="translate(50 268)"><tspan x="0" y="0">5 Callable stage</tspan></text>
  <text class="lc7" transform="translate(50 280)"><tspan x="0" y="0">grids, interpolants </tspan></text>
  <line class="lc0" x1="36" y1="286" x2="36" y2="329"/>
  <line class="lc1" x1="14" y1="300" x2="246" y2="300"/>
  <text class="lc12" transform="translate(44 323)"><tspan x="0" y="0">solve</tspan></text>
  <circle class="lc13" cx="36" cy="335" r="3.5"/>
  <text class="lc8" transform="translate(50 339)"><tspan x="0" y="0">6 Solved stage</tspan></text>
  <text class="lc7" transform="translate(50 351)"><tspan x="0" y="0">policy + value mapped </tspan></text>
  <line class="lc0" x1="36" y1="357" x2="36" y2="365"/>
  <text class="lc12" transform="translate(44 369)"><tspan x="0" y="0">simulate</tspan></text>
  <circle class="lc13" cx="36" cy="375" r="3.5"/>
  <text class="lc8" transform="translate(50 379)"><tspan x="0" y="0">7 Simulated stage</tspan></text>
  <text class="lc3" transform="translate(196.36 235.52)"><tspan x="0" y="0">Syntax layer</tspan></text>
  <text class="lc3" transform="translate(162.89 252.13)"><tspan x="0" y="0">Comp. representation</tspan></text>
  <text class="lc3" transform="translate(196 310)"><tspan x="0" y="0">Application</tspan></text>
</svg>
<p style="font-size:12px; opacity:0.5; margin-top:6px;">
Steps 1–4: syntax layer &nbsp;|&nbsp; Step 5: callable representation &nbsp;|&nbsp; Steps 6–7: application.
<a href="#appendix-seven-lives-detail">Detailed table →</a>
</p>
</div>

> Source files for building a stage are organised in a library directory containing stage syntax templates, method YAMLs, a shared calibration.yaml, and a shared settings.yaml. However, the source files themselves should not be thought of as a stage, but rather as a collection of files that can be used to build a stage (we return to the reason behind this distinction below).