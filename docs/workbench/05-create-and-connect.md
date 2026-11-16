---
audience: user
type: user-guide
topic: [user-interface]
---

# Create and connect stages

A **trellis** is a diagram of periods joined by connections. A **stage occurrence** is one use of a stage in one period. To connect two occurrences, pair a continuation state field of the writing stage with an arrival state field of the reading stage. The [stage](../Bellman-Sym/01-stage.md) defines the equations. The [connector](../Bellman-Sym/06-period.md#2-connectors) identifies which state field supplies which.

Repeated occurrences have separate stage objects. In a [modular model](../bellman-calculus/APPX-H-MODULARITY.md), occurrences of one declaration retain its operators and calibration sources. Quantities that differ with age are supplied as fields; numerical methods and settings may differ by occurrence. Recipe ranges also permit positional calibration without enforcing this condition.

## 1 Create the model folder

1. Save any unsaved work before switching folders. In **Files**, choose **New trellis**. Enter a **Name**, the number of **Periods**, and a **Parent folder** outside any existing model folder. The form shows the destination. **Period label (optional)** names the repeated period.
2. Under **Templates**, choose the stages to start with. Each chosen stage has a key, the name used in the recipe and period lists. Keep **Every period** for a repeated stage or choose **Terminal period** for a stage such as a bequest. When using templates in a model with several periods, keep at least one stage on **Every period**. For an empty model folder, leave the templates unselected.
3. Choose **Write the folder**. The Workbench opens `declaration/spec.yml` in the new folder. The recipe names the trellis and its stage files. The trellis lists its periods and starts with empty connector mappings for you to fill. If you chose templates, their files are copied into the folder.

See [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md) for the files that make up a model.

## 2 Write or reuse a stage

**Write a stage from scratch.** With a recipe in the model folder, choose **New stage** in **Files**, enter a unique **Stage key**, and choose **Write the stage**. Save pending edits to the recipe or the checklist file `answers.yml` first if the form names them. The Workbench opens `declaration/stages/<key>/<key>.bl`, with starter block headers, and saves its row in the active recipe. Declare the fields and equations in the stage file. Add its key to the intended period's `stages` list to give it an occurrence. If the graph or the Recipe table is unavailable during this step, edit that list in the period or trellis file directly. A recipe and the periods it names must agree on the stage keys. [Periods written out and repeated](../Bellman-Sym/07-trellis.md#4-periods-written-out-and-repeated).

**Place an existing stage or copy a template.**

1. Open **Trellis**, set **Graph** to **Operator**, and set **Direction** to **Forward**. Open the target period and choose **+ Stage**, then choose an item from the list. You can also open **Stages** above the graph and drag an item onto the period. With the recipe open, **Stage** under the Inspector's **Recipe** table offers the same choices, with **Period file** where there is more than one template.
2. Choose a stage already in the folder to list it in the period, or choose a template to copy its declaration and companion files and add a recipe row. If the template's key is taken, enter another key in **Add stage** and choose **Add the stage**. The **library** section shows reusable stages from your configured library. Choose **from a folder…** to copy from a stage folder or a `.bl` file on disk. A trellis that lists its stages directly as records offers stages from the current folder.
3. Check the status line for the affected periods. Several periods can share the same stage list, so adding a stage to that list can place it in all of them. Check the new card for unjoined fields and add the intended connections.

The Workbench reads a stage library from `BELLMAN_STAGE_LIBRARY`, a list of local folder paths separated by the operating system's path separator, or from `~/.bellman/library/` by default. The copy in the model is a separate file from the library stage.

## 3 Add a period

1. In **Trellis → Operator → Forward**, choose **+ Period** before the earliest period or between two periods. If the target period is outside the current range, select **all** in the period selector, then **Fit**. Open a collapsed period with its chevron. You can also drop a stage from **Stages** on that control to select it for the new period.
2. In **Add period**, enter a **Label**, choose at least one stage, and select **Add the period**. The form writes `declaration/period.<label>.yml` immediately. It adds the reference to the trellis in the editor. Save that tab to keep the reference. In a trellis that lists stage records directly, the control inserts a period with the neighbouring period's stages.
3. Inspect the new joins. Inserting between two periods increases the indices of periods on the earlier side and adjusts the recipe's corresponding ranges. Check positional calibration ranges and the terminal data you supply at realization. Where stages compute age backward, a changed horizon changes the ages reached by that recurrence; the position labels do not compute them. To add a period after the terminal period, edit the trellis file directly. [Trellis syntax and period numbering](../Bellman-Sym/07-trellis.md).

## 4 Connect two stages

1. In **Trellis → Operator → Forward**, show both occurrences. To add a connection, drag an unused continuation plug of the writing stage to the arrival socket of a different stage in the same period or the next period in economic time. The terminal period is `periods[0]`, so a connection from `periods[1]` to `periods[0]` goes forward.
2. In **Join**, check the proposed field pairs and their declared sets. Choose the missing pairs and tick the ones you want to write. The Workbench proposes equal-name matches where the model can infer them. **Join** writes the ticked pairs into the period's `connectors` or the trellis's `inter_connectors`. When working with individual field ports, a direct drag can write one pair.
3. Select the resulting cable, the line connecting the occurrences, and read **Details**. It shows the field pairs, their declared sets, their origin, and the source of authored pairs. Check every period or pair of periods that uses the same mapping before saving it.

For a branch-specific example, work in a copy of **Retirement Choice**. Add an earlier period with `ret_choice` and `worker_cons` as in §3, then place the existing `retiree_cons` in that period as in §2. Drag the `retire` plug of `ret_choice` to `retiree_cons` in the new period. In the row for arrival field `a_ret`, choose continuation field `a_r`, then select **Join**. **Details** identifies the retire route and the written pair. Check the new retiree stage's inter-period connections separately.

The gesture needs a `connectors` list for a join within a period or an `inter_connectors` mapping for a join between periods. If the relevant entry is missing, add a place for the pairs in the source first. The language reference shows how to write an empty mapping and how a single inter-period mapping applies to repeated period pairs. [Connectors within a period](../Bellman-Sym/06-period.md#2-connectors) and [Inter-period connectors](../Bellman-Sym/07-trellis.md#2-inter-period-connectors).

An incomplete pairing can write the ticked pairs as a draft. **Problems** identifies the route and the fields still needed for a complete connection. For a refused edit, follow the source link in **Problems**. If **take the line out** is offered, it restores the previous text while the file still holds the edit. When a refusal prevents the graph from being rebuilt, the previous graph stays dimmed.

## 5 Change, remove, and save a connection

- Select a cable and drag a highlighted end to the new stage. If **Join** opens, check which pairs the move removes and which it writes. A move can replace an inferred match with an authored pair.
- To remove an authored connection, select its cable and choose **Remove** in **Details**, or press Backspace or Delete with focus on the forward graph. If **Details** says **joined by the names**, the connection has no authored entry. Use **Rename** there to change the arrival field's name, or move the join to write an explicit replacement.
- Inspect the edited source line and the affected periods before saving. Command+Z on macOS or Ctrl+Z on Windows and Linux reverses the latest edit in the editor. For a graph gesture that changes several files, undo from one of the affected tabs while the files still hold the gesture's edits. **Save** writes the open file. Open and save each file marked **unsaved** to keep the whole change. New stage and period files created by placement are already on disk.
- After undo, let the graph finish updating before dragging the same connection again.

A move is refused if it would leave an authored backward value pairing, such as an age pairing, without the state connection it belongs to. Edit the coupled state and value pairings in the connector source, then inspect the complete connection again. The graph gesture does not rewrite backward pairings for you.

## 6 Remove a stage or period

Select a stage card in the forward trellis. In **Details**, **Remove from periods …** removes the stage from the period list shown. A shared period file can affect several occurrences. **Remove stage** removes it from the active recipe and the periods that use it. To remove a period, select its frame and choose **Remove period** where offered. Check the affected files, mappings and period ranges in the status line.

Workbench marks unused files **deleted on save** when a removal would leave them without a reference. Review those marks before saving. Use **Keep** to withdraw a file removal offered in **Files**, or undo the model edit before saving. A file that another recipe still uses stays in the project.
