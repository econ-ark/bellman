const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const source = readFileSync(path.join(__dirname, "../extension.js"), "utf8");
const manifest = JSON.parse(readFileSync(path.join(__dirname, "../package.json"), "utf8"));

function loadCommand({ file, folder, line = 0, scheme = "file", untitled = false, remoteName,
                       paths = path.posix, openResult = true, openError } = {}) {
  const links = [];
  const errors = [];
  const commands = new Map();
  const disposable = () => ({ dispose() {} });
  const editor = file ? {
    document: { uri: { scheme, fsPath: file }, isUntitled: untitled },
    selection: { active: { line } },
  } : undefined;
  const vscode = {
    DecorationRangeBehavior: { ClosedClosed: 0 },
    StatusBarAlignment: { Right: 1 },
    SemanticTokensLegend: class {},
    window: {
      activeTextEditor: editor,
      visibleTextEditors: [],
      createTextEditorDecorationType: disposable,
      createStatusBarItem: () => ({ ...disposable(), show() {}, hide() {} }),
      onDidChangeActiveTextEditor: disposable,
      onDidChangeTextEditorSelection: disposable,
      showErrorMessage: async message => { errors.push(message); },
    },
    workspace: {
      getWorkspaceFolder: uri => {
        assert.equal(uri, editor.document.uri);
        return folder ? { uri: { scheme: "file", fsPath: folder } } : undefined;
      },
      onDidChangeConfiguration: disposable,
      onDidChangeTextDocument: disposable,
    },
    languages: {
      registerFoldingRangeProvider: disposable,
      registerDocumentSemanticTokensProvider: disposable,
    },
    commands: {
      registerCommand: (name, callback) => {
        commands.set(name, callback);
        return disposable();
      },
    },
    env: {
      remoteName,
      openExternal: async target => {
        assert.equal(typeof target, "string", "Preserve the encoded query as a string.");
        links.push(new URL(target));
        if (openError) throw openError;
        return openResult;
      },
    },
  };
  const module = { exports: {} };
  new Function("require", "module", "exports", source)(name => {
    if (name === "vscode") return vscode;
    if (name === "node:path") return paths;
    throw new Error(`Unexpected module: ${name}`);
  }, module, module.exports);
  module.exports.activate({ subscriptions: [] });
  return { run: commands.get("dynspec.openWorkbench"), links, errors };
}

test("the command opens the active file and one-based cursor line", async () => {
  assert.ok(manifest.contributes.commands.some(command =>
    command.command === "dynspec.openWorkbench"));
  const run = loadCommand({ folder: "/models", file: "/models/stages/cons.bl", line: 41 });
  await run.run();
  assert.equal(run.links[0].protocol, "bellman:");
  assert.equal(run.links[0].host, "open");
  assert.deepEqual(Object.fromEntries(run.links[0].searchParams), {
    folder: "/models", file: "stages/cons.bl", line: "42",
  });
  assert.deepEqual(run.errors, []);
});

test("query values preserve spaces, Unicode and reserved URL characters", async () => {
  const folder = "/models/ρ & savings + 50%";
  const file = "stage #1?x=2&line=99.bl";
  const run = loadCommand({ folder, file: `${folder}/${file}` });
  await run.run();
  assert.deepEqual(Object.fromEntries(run.links[0].searchParams), { folder, file, line: "1" });
  assert.equal(run.links[0].hash, "");
  assert.equal([...run.links[0].searchParams].length, 3);
});

test("a file outside the workspace uses its own folder on POSIX and Windows", async () => {
  for (const [paths, file, folder] of [
    [path.posix, "/other models/cons.bl", "/other models"],
    [path.win32, "C:\\other models\\cons.bl", "C:\\other models"],
    [path.win32, "\\\\server\\models\\cons.bl", "\\\\server\\models\\"],
  ]) {
    const run = loadCommand({ paths, file });
    await run.run();
    assert.deepEqual(Object.fromEntries(run.links[0].searchParams), {
      folder, file: "cons.bl", line: "1",
    });
  }
  const run = loadCommand({ paths: path.win32, folder: "C:\\models", file: "C:\\models\\stages\\cons.bl" });
  await run.run();
  assert.equal(run.links[0].searchParams.get("file"), "stages/cons.bl");
});

test("missing, untitled and remote documents do not open links", async () => {
  for (const options of [
    {},
    { file: "/models/new.bl", untitled: true },
    { file: "/models/cons.bl", scheme: "vscode-remote" },
    { file: "/models/cons.bl", remoteName: "ssh-remote" },
  ]) {
    const run = loadCommand(options);
    await run.run();
    assert.equal(run.links.length, 0);
    assert.deepEqual(run.errors, ["Open a saved local file to use Bellman Workbench."]);
  }
});

test("a refused or failed external open is reported to the user", async () => {
  const refused = loadCommand({ file: "/models/cons.bl", openResult: false });
  await refused.run();
  assert.deepEqual(refused.errors, ["Could not open Bellman Workbench. Install the desktop application first."]);
  const failed = loadCommand({ file: "/models/cons.bl", openError: new Error("No application registered") });
  await failed.run();
  assert.deepEqual(failed.errors, ["Could not open Bellman Workbench: No application registered"]);
});
