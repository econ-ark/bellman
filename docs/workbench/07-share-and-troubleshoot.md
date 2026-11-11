---
audience: user
type: user-guide
topic: [user-interface]
---

# Share a project and get help

Share the model files and the recipe your colleague should open. Add the commit identifier when the files are in Git, and include an exported view when the diagram itself matters.

## 1 Review and commit changes

In a folder under Git, Workbench shows Git's change marks beside files and offers **commit** and **push** under **More** at the bottom of the window.

If you create a Git repository outside Workbench, close the model window and open it again. In the browser version, stop and restart the Workbench command for that folder.

1. Save the files you intend to share. Review their changes in your Git client, including any new files.
2. Open **More → commit**. Check the branch shown in the form and untick any file you want to leave out. The form lists new, changed and deleted files from the open model folder.
3. Enter a **Message**, then choose **Commit**. The commit records the selected files as saved on disk. Other files previously staged in Git stay staged.
4. To send the branch to its configured remote, choose **push**. Workbench uses the credentials available to Git. Check the status line for Git's response.

The commit is local until it is shared. If Git refuses a push, open **Problems** for its message. Set up the destination or credentials in your usual Git client, then retry. [Workbench reference](../overview/07-workbench.md#6-creating-a-model-and-keeping-it-in-git)

## 2 Export a diagram

1. Open the stage or trellis you want to share. After a change to a bound input, reopen the saved occurrence and check the value before exporting.
2. Choose **More → export view**. The status line names the export record under `model-explorer/`.
3. Share the `.graph.json`, `.edge-overlays.json` and `.export.json` files together. The record identifies the source files and their fingerprints, the installed Bellman and Workbench versions, and the Git commit when there is one. Workbench keeps these exports outside Git by default. Share them alongside the revision.

For a trellis, the export contains all periods. The record also identifies any restriction applied to the view in Workbench. Save and commit the model first if you want an export tied to a reproducible revision. The export record marks inputs read from unsaved or uncommitted work.

For a paper figure, select a box in a saved stage and choose **Paper** when offered. Workbench creates a Markdown description and an SVG drawing under `paper/`. [Workbench reference](../overview/07-workbench.md#3-typing-and-selecting)

If you need two exports for a comparison, copy the complete first set to a separate location before exporting the second. A later export can reuse the same filenames.

## 3 Start an inspection notebook

With a recipe or trellis selected, choose **Notebook** in **Files**. Workbench creates `notebooks/<folder>.ipynb` and names it in the status line. Open it in Jupyter to inspect the saved model. Its cells read the selected recipe or trellis, list the stage occurrences and methods, and record the input fingerprints when you run them.

Keep and edit the notebook in your project. Workbench leaves an existing notebook in place. Use your numerical workflow for the solution.

## 4 Hand the model to a colleague

Send the whole model folder or the repository revision. Name the recipe to open, such as `declaration/spec.yml` or a named variant. Keep the files the recipe reads at their relative paths. Include any dependencies it reads outside the model folder. [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md)

If you generated files with Matsya, review them and adopt the intended declaration before committing it. Share the economic assumptions and any notebook used for numerical results alongside the declaration. [Building a model with Matsya](01-matsya.md)

## 5 Find and resolve a problem

| What you see | What to do |
|---|---|
| The desktop app cannot start Workbench. | Read the error and its log path. Use **Settings → Workbench command…** to select the installed executable, then reopen the project. |
| The browser cannot open Workbench. | Check the terminal that started it. If its port is occupied, start it with an available port, for example `bellman-workbench . --port 8766`. |
| The page says `No stage file.` | Open the model folder that contains your declaration. If you are starting from an empty folder, begin with a model description or create a trellis. |
| A diagram is dimmed or a file has an orange error mark. | Open **Problems** and follow the source link. Workbench keeps the previous diagram while the new text has an error. |
| A save reports that the file changed on disk. | Choose **Compare**, then choose which version to keep. [Open and edit a project](02-open-and-edit.md#3-save-an-edit) |
| Git refuses a commit or push. | Read Git's message in **Problems**. Resolve the reported issue in Git before retrying. |

When reporting a problem, include the Workbench version, the file and line if shown, and the exact diagnostic. For a startup failure, include the relevant part of the log. [Installation troubleshooting](../overview/00-install.md#5-if-something-does-not-open)
