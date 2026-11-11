---
audience: user
type: user-guide
topic: [user-interface]
---

# Open and edit a project

Open a model folder to work with its source files and diagrams together. In an existing model, `declaration/` holds the files Bellman reads. The **model folder** is the folder above it, where you can also keep the model description, notebooks and results. [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md)

## 1 Open a project

- **Desktop.** Choose **Open Project…** for a model folder or **Open File…** for a `.bl` stage file or a recipe such as `spec.yml`. Both actions are also in the **File** menu. Press **Command+O** on macOS or **Ctrl+O** on Windows and Linux for a project, and add **Shift** to open a file. To return to a folder, select it under **Recent projects** on the opening screen.
- **Browser.** With the Bellman Python environment active, run `bellman-workbench /path/to/model`. Keep that terminal open, and choose a file from **Files** in the browser. The default address is `http://localhost:8765/`. [Install Bellman Workbench](../overview/00-install.md)

Open the folder above `declaration/` to see the whole project. Workbench opens the recipe or trellis when the folder contains one, and otherwise opens the first stage file. A **recipe** names the files used to assemble the model. A **trellis** describes its periods and their connections. [Recipes and model files](../Bellman-Sym/reference/model-directory-layout.md#22-what-a-recipe-names) · [Trellises](../Bellman-Sym/07-trellis.md)

A desktop link can open a file at a particular line. Use the form `bellman://open?folder=<absolute-folder>&file=<relative-file>&line=<line-number>`. URL-encode each value, use a file path relative to the model folder, and count lines from one. A link to a folder already open in Workbench uses its existing window. In the browser, add `?file=<relative-file>&line=<line-number>` to the address of the running project.

## 2 Set up the window

| Area | What to use it for |
|---|---|
| **Files** | Open a file or find changes marked `unsaved`. |
| Editor | Edit the open file and switch between its tabs. |
| **Inspector** | Read the open file's fields or the files named by its recipe. |
| **Semantic graph** and **Details** | Select a box to inspect its operation and find the corresponding source. |
| **Matsya** | Discuss a model or request a declaration. [Building a model with Matsya](01-matsya.md) |

Use **Files**, **Inspector**, **Details** and **Matsya** in the main bar to open or close their areas. Drag a divider to resize adjacent areas. Double-click its handle to reset it. Workbench remembers sizes and folds for each folder in the browser. Use **Tab** to reach the main controls and **Enter** to activate a focused button.

In the desktop app, **Settings → Workbench command…** chooses the `bellman-workbench` executable in your Bellman Python environment. **Settings → Editor command…** chooses the VS Code or Cursor executable. Open a new model window after changing it. With a source block selected, **Open in editor** opens its line in the configured editor. [Install Bellman Workbench](../overview/00-install.md#3-build-and-install-the-desktop-application)

Use **Types** to show or fold the detailed annotations in stage headers. Use **Notes** to show explanatory annotations as written. A note glyph also previews its text on hover. The minimap at the right of the editor takes you to the selected line. These controls change the display.

## 3 Save an edit

1. Select a file in **Files**, then edit its text. Its tab and tree entry show `unsaved` while the edit remains in the editor.
2. Click **Save**, or press **Command+S** on macOS or **Ctrl+S** on Windows and Linux from the editor. Save each open file marked `unsaved`.
3. If another application or tab changed the file on disk, choose **Compare** to see the difference. **Reload** replaces the editor text with the disk version. **Overwrite** saves the editor text over the disk version.

Use Undo in the editor to take back edits. A file tab can close once its edits are saved or undone. When you close a desktop model window with unsaved changes, **Discard and close** closes it and drops the edits.

## 4 Find a line or diagnose an edit

Open **Go to** from the main bar, or press **Command+P** on macOS or **Ctrl+P** on Windows and Linux. Type `@policy` to find a block or graph box, `:20` to go to a line, `#argmax` to search the open text, or `>high contrast` to find the command that makes line numbers easier to see. Use the arrow keys to browse the results, **Enter** to go to one or run it, and **Escape** to close the list.

**Back** and **Forward** revisit places in the open model. If an edit underlines a line or leaves the previous diagram dimmed, open **Problems** at the upper right of the graph. Follow the diagnostic's file or line link to correct the source. **Escape** closes the list and returns focus to **Problems**. [Workbench reference](../overview/07-workbench.md#3-typing-and-selecting)
