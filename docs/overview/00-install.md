---
title: Install Bellman Workbench
audience: user
type: user-guide
---
# Install Bellman Workbench

Bellman Workbench lets you edit Bellman-SYM model files and inspect their diagrams. You can use it in a browser or in the **desktop application**, which opens the same interface in its own window.

**Installing the desktop application does not install Python or Bellman.** Both versions need the Python packages `bellman` and `bellman-workbench`, installed together as below. You do not need the desktop application to use the browser version.

No ready-made desktop installer is currently published on the [download page](https://github.com/econ-ark/bellman/releases). You can use the browser version now, or build the desktop application in §3.

## 1 Install the Python packages

Install [Python](https://www.python.org/downloads/) **3.12 or later** and [Git](https://git-scm.com/downloads), then open Terminal on macOS/Linux or PowerShell on Windows. Download the source:

```sh
git clone https://github.com/econ-ark/bellman.git
cd bellman
```

Create a **virtual environment**, a folder that keeps this installation's Python packages together, and install both packages. Keep this terminal in the `bellman` folder for the commands below.

On **macOS or Linux**:

```sh
python3 --version
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e "packages/bellman[explore]" -e packages/bellman-workbench
```

If `python3 --version` reports a version older than 3.12, use the newer Python executable in the next line, for example `python3.13 -m venv venv`.

On **Windows**:

```powershell
py -3 --version
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -e "packages/bellman[explore]" -e packages/bellman-workbench
```

If `py -3 --version` reports a version older than 3.12, select your installed newer version when creating the environment, for example `py -3.13 -m venv venv`.

The commands install Bellman, the Workbench interface and their Python dependencies. The `-e` option uses the code in your downloaded folder, so keep that folder and `venv/` in place.

## 2 Open the browser version

On **macOS or Linux**:

```sh
venv/bin/bellman-workbench applications/portfolio-choice
```

On **Windows**:

```powershell
.\venv\Scripts\bellman-workbench.exe applications/portfolio-choice
```

Your browser opens at [localhost:8765](http://localhost:8765/). The command starts a server on your own computer; keep the terminal open while you work, and press **Ctrl+C** there to stop it. Replace `applications/portfolio-choice` with your own model folder when ready.

Choose a `.bl` model file in the file tree to edit it and see its diagram. For example, open `declaration/stages/port/port.bl` in the supplied portfolio model. **Save** writes the edited text to disk. See [Bellman Workbench](07-workbench.md) for the editor, diagrams and other controls.

## 3 Build and install the desktop application

Complete §1 first. Install [Node.js 22](https://nodejs.org/en/download) with npm, Rust and the [Tauri prerequisites for your operating system](https://v2.tauri.app/start/prerequisites/). Tauri is the software used to build the desktop application. From the `bellman` folder:

```sh
cd packages/bellman-desktop
npm ci
npm run build
```

The application and installers are written under `packages/bellman-desktop/src-tauri/target/release/bundle/`, relative to the repository root. On macOS, copy **Bellman Workbench.app** from its `macos/` subfolder into **Applications** and launch it. This local build is not a signed public release. Desktop installation has been checked on macOS; Windows and Linux installation checks remain outstanding.

On first launch:

1. Choose **Settings → Workbench command…** and select the executable inside the environment created in §1: `venv/bin/bellman-workbench` on macOS/Linux, or `venv\Scripts\bellman-workbench.exe` on Windows. Select this file, not the Python executable.
2. Choose **File → Open Project…** and select your model folder, for example `applications/portfolio-choice`. The folder normally contains `declaration/`; see [Model directory layout](../Bellman-Sym/reference/model-directory-layout.md).
3. Alternatively, use **File → Open File…** for a `.bl` file or a model recipe, `spec.yml` or `spec.<name>.yml`, which names the files used to assemble a model. Previously opened folders appear under **Recent projects**.

The application starts the Workbench server for you; no terminal command is needed for later launches. Closing a model window stops its server. The editor and diagrams work as described in §2.

## 4 Update an installation

Close the Workbench's model windows or stop its browser command. In the downloaded `bellman` folder, run:

```sh
git pull --ff-only
```

Then repeat the two `pip install` commands in §1 and reopen the Workbench. If Git reports conflicting local edits, keep those edits and resolve them before updating.

An installed desktop application uses updates from the Python environment selected in **Settings → Workbench command…** when a new model window opens. Changes to the desktop application itself, such as its menus or opening screen, require repeating §3 and replacing the installed application. There is no automatic updater.

## 5 If something does not open

| What happens | What to check |
|---|---|
| The desktop application cannot start `bellman-workbench` | Select the executable from §3 in **Settings → Workbench command…**, then open the project again. |
| Python reports that `bellman` is missing | Install both packages with the command in §1, using the same environment. |
| The page says `No stage file.` | Open a model folder containing `.bl` files, such as the supplied example in §2. |

For **paper** exports and other static diagrams, also install [Graphviz](https://graphviz.org/download/), or install Node.js and run `npm ci` in the repository root. This extra step is not needed for the interactive Workbench graph.
