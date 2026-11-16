---
audience: user
type: user-guide
topic: [user-interface]
---

# Inspect a model

Use the [semantic graph](../wiki/semgraph.md) to trace how a stage uses its inputs and how one stage supplies the next. Open a specific occurrence to check the parameter values and methods used at that point in the model.

## 1 Choose a stage and period

Open **Trellis** to see the model’s periods and stages together. A [trellis](../wiki/trellis.md) is a diagram of periods joined by connections. The period labels show positions, not ages; the viewer is not given terminal age. In a long model, use the period selector above the graph to restrict the view. Choose **all** to show every period again.

Double-click a stage card in the trellis, or select it and choose **Open the stage** in **Details**. This opens the stage file and its graph for that occurrence, meaning that stage at that position in the trellis. Check the path in the main bar for the recipe, period and stage.

You can also open a stage file from **Files**. If the current recipe uses it, Workbench initially shows its first occurrence. When the path offers a list of positions, choose another one to inspect its bindings. Use **Stage** for the open stage and **Trellis** to return to the period view.

## 2 Choose a graph

In the graph bar, choose **Initial** from **Graph** to see the fields named at arrival, decision and continuation, along with the blocks that read and write them. In the trellis, this view lets you trace a connection between particular fields.

Choose **Operator** to see the builders, which are groups of operations. With **Direction** set to **Backward**, follow continuation values through the calculations that produce earlier values. With **Forward**, follow the operations that act on probability measures. Use the chevrons on the frames to open the operations inside a builder or stage.

In a stage’s **Operator** view, the **Operative builders** switch at the foot of the graph shows the operations that a bound method adds, where available. Switch it off to see the declared builders from the stage file. [Methodization](../Bellman-Sym/04-methodization.md) explains how methods attach to the authored equations.

Use **Zoom in**, **Zoom out** and **Fit** at the foot of the graph. Drag the background to pan, or use the layout button to switch between top-to-bottom and left-to-right views. With focus in the graph, use **Tab** to reach a box and **Enter** to select it. Open **Legend** in **Details** to identify the marks and layers. Where the stage graph offers **Perch overlays**, use them to see which fields are available at each information set.

## 3 Read the equations and their sources

1. Select a box and open **Details** from the main bar if the panel is folded. A builder’s signature lists its inputs and outputs. Use the source links to read the corresponding equations. Selecting a field in **Initial** shows its declared set and role, such as state, control or value.
2. Select a connection in the trellis to see the stages it joins, its branch where applicable, and the paired fields. Follow a source link when the pairing is written in a file. Check that the quantities agree in economic meaning and units, as when end-of-period saving supplies the next period’s opening wealth. Widen the period selection if a route ends at a marker for a stage outside the view.
3. Under the stage editor, open **Inspector** and choose **Fields**, **Parameters**, **Settings** or **Methods**. **Fields** lists the declarations at each information set. The other tabs show the parameter values, numerical settings and attached methods for the selected occurrence. Where a row links to a source, follow it to see the file that supplies the value or method.

<a id="4-check-what-the-model-still-needs"></a>

## 4 Required inputs and checks

Open **Problems** at the upper right of the graph. The list separates errors from checks. **Unjoined fields** identifies internal arrivals that still need a connection. **Headers to check** flags value inputs listed in a header that no equation reads. Follow the file and line link when one is available. Expand **More** in the status line to see the file or buffer Workbench read, the occurrence it used, and the fingerprints of its source files. A fingerprint identifies the specific text Workbench read.

Inspect the terminal period, indexed 0, in **Backward**. Supply data for every value-type field the terminal stage takes in when you make the model numerical. The value field `V[>]` needs its representing function and any derivatives the block reads; a constant such as age or a borrowing bound needs its own value. These data are supplied by the user, not stored in the trellis file. A bequest equation and a successfully constructed graph leave those inputs explicit. A zero terminal value is a choice you supply. [Inter-period connectors and terminal data](../Bellman-Sym/07-trellis.md#2-inter-period-connectors)
