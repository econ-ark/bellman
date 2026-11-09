# Bellman Workbench desktop

For setup and first use, see [Install Bellman Workbench](../../docs/overview/00-install.md).

The desktop application opens the installed Workbench page in its own window. Python and the `bellman-workbench` package must already be installed. The application starts a local server for each model folder and stops that server when its window closes.

The opening screen has **Start** and **Recent projects** sections. **Open Project…** chooses a model folder; **Open File…** chooses a stage or recipe. Both use the native file chooser. Cancelling restores the actions, and opening a project displays progress until its window is ready. Recent projects lists up to eight successfully opened folders, newest first, with their paths; selecting one opens it again. Missing folders remain listed and show an error if selected. Command configuration remains in Settings.

Use **File → Welcome** to return to the opening screen and see the latest projects. If a file chooser is cancelled, the control that opened it keeps keyboard focus.

The same actions are available through **File → Open Project…** (⌘O on macOS, Ctrl+O elsewhere) or **Open File…** (add Shift), or through a link of this form:

```text
bellman://open?folder=<absolute-folder>&file=<relative-file>&line=<positive-line>
```

URL-encode each value. A link received while that folder is open selects the file and line in an existing window showing it. Creating a trellis can change a window's displayed folder; later links use that current folder. If two existing windows come to show the same folder, both keep their text and later links consistently reuse one. Unsaved files keep the Workbench's normal navigation behaviour. A close request asks before discarding unsaved changes.

The installer registers `.bl` files. Open a `spec.yml` or `spec.<name>.yml` recipe through the file dialog or a link. The application does not associate every YAML file with Bellman.

## Choose the installed commands

When `bellman-workbench` is on the command search path, no setting is needed. Desktop launch environments often have a shorter search path than terminals: use **Settings → Workbench command** to choose the executable inside the Python environment containing Bellman. Settings are saved in `commands.json` in the operating system's application configuration directory. The recent-project list is stored separately in `recent-projects.json`.

Use **Settings → Editor command** to choose the `code` or `cursor` command-line executable. This saves the command with `--goto`. On Windows, select `Code.exe` or `Cursor.exe`; batch scripts are refused. Newly opened model windows then offer **open in editor** beside the source block. An editor runs separately from the Workbench's server and remains open when its model window closes.

An executable plus additional arguments can instead be set as JSON lists in the environment, or as `workbench_command` and `editor_command` in `commands.json`:

```sh
export BELLMAN_DESKTOP_COMMAND='["/path/to/python", "-m", "bellman_workbench.command"]'
export BELLMAN_WORKBENCH_EDITOR='["code", "-g"]'
```

The environment overrides the saved command. Commands receive arguments directly; no command shell evaluates them. Incoming links cannot change these commands. Server logs are kept in the application's log directory and their path is included in startup errors.

## Updates

Reopening the application starts the configured Workbench again. If its command uses an editable repository checkout, changes in that checkout then appear without rebuilding the native application. Changes in another checkout are not included automatically, and newly required Python dependencies must be installed in the selected environment. Keep the configured checkout available until the command is changed.

Changes to the native application itself, including its menus or icon, require rebuilding and replacing the application. No automatic application updater is configured.

## Build and check

The opening screen’s `assets/logo.svg` copies the [Workbench mark](../bellman-workbench/bellman_workbench/public/brand/logo.svg); keep them in sync when the mark changes. The typography follows the Project Bellman brand guide, kept with the brand package: PP Monument Extended for the name, PP Monument for headings, Archivo for controls and IBM Plex Mono for paths and shortcuts. `assets/fonts/` includes the open Archivo and IBM Plex Mono fonts and their licences.

For a local build with the brand headings, copy `PPMonumentExtended-Regular.otf` and `PPMonumentNormal-Regular.otf` from your licensed brand-font folder into `assets/fonts/` before building. The brand package keeps local copies under `theme/docs/_assets/brand/fonts/`. These commercial files are ignored by Git and must never be committed. Builds without them use Archivo as the fallback. The installed local macOS build includes them; a public distribution needs the appropriate font licence.

The layout was informed by the official [JetBrains welcome screen](https://www.jetbrains.com/help/clion/welcome-screen.html) and [VS Code welcome page](https://code.visualstudio.com/docs/editing/getting-started/tips-and-tricks#getting-started): small opening actions, visible keyboard shortcuts and a list of recent projects.

The application icon uses the Project Bellman two-triangle mark from the brand package's vector source, `Bellman Logo Wire A.svg`. Its continuous outlines keep the module joins aligned at every icon size. The PNG, macOS and Windows icons use its [ice-faced variant](../../docs/_assets/brand/logo.svg). Regenerate them with `npm run tauri -- icon ../../docs/_assets/brand/logo.svg --fit contain --output <temporary-directory>`, then copy the six existing desktop icon files into `src-tauri/icons/`.

Install the [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) and a current stable Rust compiler. From this directory:

```sh
npm ci
cargo test --manifest-path src-tauri/Cargo.toml
npm run build
```

The application and platform installers are under `src-tauri/target/release/bundle/`. The repository's **Build desktop Workbench** workflow can be run manually to create macOS, Linux and Windows build artifacts. It does not publish a release or establish that the installers have passed a manual installation check.

To test a local build against the current Workbench, set `BELLMAN_DESKTOP_COMMAND` to its environment's executable, set `BELLMAN_WORKBENCH_MATSYA=off`, then run `npm run dev -- /path/to/model`. A built binary also accepts a model folder, stage file, recipe file or encoded `bellman://` URL as its argument.

A public macOS distribution requires developer signing and notarization credentials; Windows signing is likewise a separate release step. A locally built application is not a signed public release. The built bundle must be registered with the operating system to test links opened by other applications.
