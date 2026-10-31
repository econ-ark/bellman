"""Bellman Workbench (model interface specification 0.3).

The package holds eight Python files. `model.py` is the backend: it reads
the model folder as the factory reads it, elaborates a buffer, and answers
the graph collection, the card and the kernel of a piece, the source spans
of the blocks and git's state; it imports no Solara. `recipe.py` reads the
sources of the folder's trellis, the recipe or a trellis file, binds a
buffer as the occurrence the head names, and shows the recipe as a table;
`trellis.py` reads, elaborates, binds and draws the trellis, restricted as
the view's bar asks; `creation.py` reads the templates of a stage from the
application corpus, writes the files the forms "new trellis", "add stage",
"add period" and "new variant" ask for, each YAML file edited as text by
the package's writers of `bellman.trellis`, and lists the checklist of the
entries answers.yml marks (unit C; unit K, K-D29); none of the three
imports Solara. `app.py`
is the Solara page over the backend: the four regions, the elaboration
task and the session's state.
`command.py` is the console command `bellman-workbench <folder>`, which
starts Solara's server on the page. `matsya_client.py` holds `ask`, the one
function by which the page reaches Matsya's command-line client, and
`switched_off`, the setting that removes Matsya from the page, and imports
no Solara; `matsya_window.py` is Matsya's column at the right of the window
(unit M; spec 0.4 §5.6).
"""
