# Notebook markdown cells

Each `.md` file corresponds to one markdown cell in
`solve_port_cons_ffp.ipynb`. The files are the editable
source of truth for all prose in the notebook.

## Structure

```
md-cells/
  00-modular-portfolio-choice-and-consumption.md   ← cell 0
  01-stage-pipeline.md                             ← cell 1
  02-the-cons-port-and-disc-stages.md              ← cell 2
  ...
  17-appendix-seven-lives-detail.md                ← cell 36
  README.md                                        ← this file
```

Each file has a header comment mapping it to a notebook cell:
```html
<!-- notebook cell 0 | id: zm5f1s5z2r -->
```

## Sync workflow

1. **Edit** any `.md` file in this folder.
2. **Preview** what will change:
   ```bash
   python sync_md_to_notebook.py
   ```
3. **Apply** changes to the notebook:
   ```bash
   python sync_md_to_notebook.py --apply
   ```

The sync matches files to cells by ID. Code cells, outputs,
and notebook metadata are never touched.
