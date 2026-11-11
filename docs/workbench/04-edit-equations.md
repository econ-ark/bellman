---
audience: user
type: user-guide
topic: [user-interface]
---

# Edit equations and inputs

Edit a stage’s equations in its `.bl` file. Workbench reads the current text and updates the semantic graph, so you can inspect the economic consequences of a change before saving it.

## 1 Find and edit an equation

1. Open the stage file in **Files**, or double-click the stage at the period you want to inspect in **Trellis**. Once saved, the revised equation applies at every occurrence that uses the same file.
2. Select the relevant box in the stage graph, then choose its source link in **Details** to open the defining line in the editor.
3. Edit the equation in the editor. If it now reads or writes a different field, check its declaration and the block’s header, which lists the fields the block reads or writes. [Field equations](../Bellman-Sym/03-field-equations.md) describes the syntax.

For example, the [consumption and savings stage](../Bellman-Sym/03-field-equations.md#1-consumption-and-savings) defines saving by `a = m_d - c`, where `m_d` is cash on hand at the decision and `c` is consumption. After changing that budget equation, use **Initial** to check the fields it reads and writes, then trace where saving is used in the [model graph](03-inspect-a-model.md).

## 2 Check the graph after editing

Pause after typing to let Workbench read the new text. When the reading succeeds, the graph updates from the editor. If the text is refused, the editor marks the line and **Problems** lists the reason. When a previous graph is available, Workbench dims it and labels it **last constructed**. Use the marked source line to correct the current text.

A stage can construct in one direction and have a refused graph in the other. Check **Forward** and **Backward** when an equation affects both. Construction and binding let you inspect the equations and their supplied values and methods. Computing a numerical policy or simulating the model requires a separate step.

## 3 Edit field declarations

In **Inspector → Fields**, choose the table for arrival, decision, or continuation. Select a field name to find its declaration. Where a set or role is editable, enter the new set or choose a role. To add a field, complete **New field** and **Set**, choose its role, then select **+**. In a branching stage, use the table for the branch you intend to change.

These actions edit the source in the editor. Check **Problems**, then save the file to keep the change. See [Stage fields](../Bellman-Sym/01-stage.md) for the declaration rules.

## 4 Change parameter values and methods

Open the stage as an occurrence of the recipe you intend to change. In **Inspector**, use the relevant tab to find the source for that occurrence.

| Tab | What you can edit |
|---|---|
| **Parameters** | Enter a value in an editable row and press **Enter**. The source is a calibration file. The stage’s declaration gives the parameter’s allowed set. |
| **Settings** | Enter a value of the kind the settings file expects and press **Enter**. For example, keep an integer setting as an integer. |
| **Methods** | Where a YAML entry has a picker, choose a method from the choices admitted for that computation. Open the methods file in the editor to change options such as a grid. |

Confirming a row writes its source file without pressing **Save** in the editor. Save or discard any unsaved edits to that file before using the row. If the tab names no source, open the recipe and use its **Recipe** tab or edit its text to attach the appropriate file. [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md) · [Methodization](../Bellman-Sym/04-methodization.md)

A `.bl` file whose first nonblank line is `@methods:` followed by the stage name is a [methods addition](../wiki/addition.md). Workbench opens it as text and lists additions kept beside their stage files in the **Recipe** tab’s methods choices. When the recipe selects an addition, the package reads it with the stage. The **Methods** tab displays any methods it binds as text. To change the addition, edit and save the file itself. Matsya’s **Build declaration** refuses a model whose selected files include a methods addition.

To trace an executable routine, follow the method's source link in **Methods** and check the handler named there. A tag displayed in the graph identifies the bound method. The method file or addition gives the declaration you need to trace its implementation.

## 5 Undo and save

Use **Command+Z** on macOS or **Ctrl+Z** on Windows and Linux to undo an edit in the editor. If you made an unsaved change through the graph, undo it from the editor tab of a file that the change edited.

Choose **Save** to write the open editor tab. If an edit changed several files, save each tab marked **unsaved**. For a value already written through an Inspector row, restore the earlier value in its source file.
