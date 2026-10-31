"""Git and the export record of Bellman Workbench, without a browser
(model interface specification 0.3, §5; unit C): the changes git reports
under a folder, the commit of named paths, the push with the credentials
git holds, the place of a folder and a repository made with its
destination; the tab's folder, git's line and the commit form, rendered by
Solara's test renderer; and the export record.

The tests named `test_item_<n>_*` close the claims of C's acceptance items
3 and 4 that hold without a browser; `test_page_creation.py` closes them
through the page. A test runs in the test repository `repository`, a bare
repository and its clone with one commit pushed. The fixtures and the
helpers are those of `workbench_support.py`.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

import ipyvuetify as v
import solara
from workbench_support import (
    CONS,
    DEMO_STAGES,
    filled,
    git,
    refusing_server,
    wait_until,
    written_from_the_forms,
)

from bellman_workbench import app, creation, model


def test_item_3_the_tree_letters_equal_git_status(repository):
    """The letters the tree carries for each file of the folder equal the
    two letters `git status --porcelain --untracked-files=all` writes for
    it: a modified file, a deleted one, a staged new one and an untracked
    one (spec 0.3 §2.1 and §5)."""
    work, _ = repository
    folder_path = work / "model"
    folder_path.mkdir()
    for name in ("a.yml", "b.yml"):
        (folder_path / name).write_text(f"{name[0]}: 1\n", encoding="utf-8")
    git(work, "add", "model")
    git(work, "commit", "-q", "-m", "the model")
    (folder_path / "a.yml").write_text("a: 2\n", encoding="utf-8")
    (folder_path / "b.yml").unlink()
    (folder_path / "c.yml").write_text("c: 1\n", encoding="utf-8")
    git(work, "add", "model/c.yml")
    (folder_path / "d.yml").write_text("d: 1\n", encoding="utf-8")
    porcelain = git(work, "status", "--porcelain", "--untracked-files=all").splitlines()
    expected = {line[3:].removeprefix("model/"): line[:2] for line in porcelain}
    assert expected == {"a.yml": " M", "b.yml": " D", "c.yml": "A ", "d.yml": "??"}
    folder = model.open_folder(folder_path)
    assert model.git_marks(folder) == expected
    tree = {entry["path"]: entry["git"] for entry in model.folder_tree(folder)}
    assert {path: mark for path, mark in tree.items() if mark} == {
        path: mark for path, mark in expected.items() if path != "b.yml"
    }


def test_item_3_a_commit_of_named_files_leaves_unrelated_staged_work(repository):
    """With unrelated work staged in the repository, the commit of the
    changes git reports under the folder, a modified file, a deleted file,
    a staged rename named by both its paths and an untracked file, records
    those alone; the unrelated work stays staged (spec 0.3 §5, C-R5)."""
    work, _ = repository
    folder_path = work / "model"
    folder_path.mkdir()
    for name in ("a.yml", "b.yml", "c.yml"):
        (folder_path / name).write_text(f"{name[0]}: 1\n", encoding="utf-8")
    git(work, "add", "model")
    git(work, "commit", "-q", "-m", "the model")
    (folder_path / "a.yml").write_text("a: 2\n", encoding="utf-8")
    (folder_path / "b.yml").unlink()
    git(work, "mv", "model/c.yml", "model/r.yml")
    (folder_path / "e.yml").write_text("e: 1\n", encoding="utf-8")
    (work / "unrelated.md").write_text("staged and not the model's\n", encoding="utf-8")
    git(work, "add", "unrelated.md")
    folder = model.open_folder(folder_path)
    changes = model.git_changes(folder)
    assert {(change.mark, change.path, change.original) for change in changes} == {
        (" M", "a.yml", None),
        (" D", "b.yml", None),
        ("R ", "r.yml", "c.yml"),
        ("??", "e.yml", None),
    }
    paths = [path for change in changes for path in (change.path, change.original) if path]
    result = model.git_commit(folder, "the model changed", paths)
    assert result.ok and "the model changed" in result.sentence
    recorded = git(work, "show", "--name-status", "--format=", "HEAD").splitlines()
    assert sorted(recorded) == [
        "A\tmodel/e.yml",
        "D\tmodel/b.yml",
        "M\tmodel/a.yml",
        "R100\tmodel/c.yml\tmodel/r.yml",
    ]
    assert git(work, "diff", "--cached", "--name-only").split() == ["unrelated.md"]
    assert model.git_changes(folder) == ()


def test_item_3_a_named_path_is_that_file_and_no_pattern(repository):
    """With `b.yml` modified and `a.yml` untracked, the commit of the
    untracked `[ab].yml`, a name git reads by default as a pattern that
    matches both, records `[ab].yml` alone; `b.yml` stays modified and
    `a.yml` untracked (spec 0.3 §5)."""
    work, _ = repository
    folder_path = work / "model"
    folder_path.mkdir()
    (folder_path / "b.yml").write_text("b: 1\n", encoding="utf-8")
    git(work, "add", "model")
    git(work, "commit", "-q", "-m", "the model")
    (folder_path / "b.yml").write_text("b: 2\n", encoding="utf-8")
    (folder_path / "[ab].yml").write_text("ab: 1\n", encoding="utf-8")
    (folder_path / "a.yml").write_text("a: 1\n", encoding="utf-8")
    folder = model.open_folder(folder_path)
    assert model.git_commit(folder, "the file [ab].yml", ["[ab].yml"]).ok
    recorded = git(work, "show", "--name-status", "--format=", "HEAD").splitlines()
    assert recorded == ["A\tmodel/[ab].yml"]
    changes = {(change.mark, change.path) for change in model.git_changes(folder)}
    assert changes == {(" M", "b.yml"), ("??", "a.yml")}


def test_item_3_a_push_reaches_the_destination_with_the_machines_credentials(repository):
    """A push of the current branch reaches the test repository's
    destination with what git holds and nothing the Workbench supplies,
    and answers git's own report, which git writes to its standard error
    (C-R6)."""
    work, bare = repository
    folder = model.open_folder(work)
    (work / "notes.md").write_text("notes\n", encoding="utf-8")
    assert model.git_commit(folder, "notes", ["notes.md"]).ok
    pushed = model.git_push(folder)
    assert pushed.ok and pushed.sentence.startswith(f"To {bare}") and "->" in pushed.sentence
    branch = git(work, "symbolic-ref", "--short", "HEAD").strip()
    assert git(bare, "rev-parse", branch) == git(work, "rev-parse", "HEAD")


def test_item_3_a_push_that_would_prompt_fails_with_gits_sentence(
    repository, tmp_path, monkeypatch
):
    """A push to a destination that asks for a user name fails at once with
    git's own sentence and asks nothing (spec 0.3 §5; C-R10). The askpass
    program the environment names, as the terminals of VS Code and Cursor
    name one, is not run."""
    work, _ = repository
    # an askpass program that writes the file `asked` beside itself and
    # prints a user name
    askpass = tmp_path / "askpass" / "askpass.sh"
    askpass.parent.mkdir()
    askpass.write_text(
        '#!/bin/sh\ntouch "$(dirname "$0")/asked"\necho bellman-workbench-tests\n',
        encoding="utf-8",
    )
    askpass.chmod(0o755)
    monkeypatch.setenv("GIT_ASKPASS", str(askpass))
    with refusing_server() as url:
        git(work, "remote", "set-url", "origin", url)
        pushed = model.git_push(model.open_folder(work))
    assert not pushed.ok
    assert not (askpass.parent / "asked").exists()
    assert "could not read Username" in pushed.sentence
    assert "terminal prompts disabled" in pushed.sentence


def test_git_place_names_the_root_the_branch_and_the_destination(repository, tmp_path):
    """The place of a folder inside the test repository is the repository's
    root, its current branch and that branch's push destination; a folder
    no repository holds has none of the three (spec 0.3 §4, D10)."""
    work, bare = repository
    (work / "model").mkdir()
    branch = git(work, "symbolic-ref", "--short", "HEAD").strip()
    place = model.git_place(model.open_folder(work / "model"))
    assert place == model.GitPlace(work.resolve(), branch, str(bare))
    (tmp_path / "plain").mkdir()
    plain = model.git_place(model.open_folder(tmp_path / "plain"))
    assert plain == model.GitPlace(None, None, None)


def test_init_repository_names_the_destination_and_refuses_a_password(tmp_path, git_identity):
    """A folder no repository holds is made a repository whose current
    branch pushes to the destination given, so that its first commit and
    push run as in any checkout; a destination whose URL carries a password,
    an https URL with user information, the form a token is often written
    in, or git's remote-helper form, `https::https://…`, which the check of
    user information does not refuse, is refused before git runs, while the
    login name of an ssh destination is accepted, and so is an IPv6 host in
    brackets, whose "::" is not that form (spec 0.3 §5: no credential
    held)."""
    bare = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    assert model.init_repository(fresh, str(bare)).ok
    folder = model.open_folder(fresh)
    assert model.git_place(folder).root == fresh.resolve()
    assert model.git_place(folder).destination == str(bare)
    (fresh / "a.yml").write_text("a: 1\n", encoding="utf-8")
    assert model.git_commit(folder, "the first commit", ["a.yml"]).ok
    assert model.git_push(folder).ok
    refused = tmp_path / "refused"
    refused.mkdir()
    result = model.init_repository(refused, "https://me:token@example.org/model.git")
    assert not result.ok and "password" in result.sentence
    assert not (refused / ".git").exists()
    result = model.init_repository(refused, "https://ghp_abc@github.com/me/model.git")
    assert not result.ok and "user information before '@'" in result.sentence
    assert not (refused / ".git").exists()
    result = model.init_repository(refused, "https::https://ghp_abc@github.com/me/model.git")
    assert not result.ok and "remote-helper form" in result.sentence
    assert not (refused / ".git").exists()
    refusal = model.destination_refusal("::https://ghp_abc@github.com/me/model.git")
    assert refusal is not None and "remote-helper form" in refusal
    assert model.destination_refusal("git@github.com:econ-ark/model.git") is None
    assert model.destination_refusal("ssh://git@github.com/econ-ark/model.git") is None
    assert model.destination_refusal("git@[::1]:me/model.git") is None
    assert model.destination_refusal("ssh://git@[::1]/me/model.git") is None
    assert not model.holds_password("git@github.com:econ-ark/model.git")
    assert not model.holds_password("https://github.com/econ-ark/model.git")


def test_every_reader_of_the_model_folder_reads_the_tabs_folder():
    """app.py reads the process's folder, FOLDER, in one place alone: the
    default of the tab's folder `tab_folder`; every other reader of the
    model folder reads `tab_folder.value`, the form "new trellis" among
    them, whose parent folder is by default the folder that holds the tab's
    (C-R7, amended by unit L, Task 13), so that a tab that opened a new
    folder reads that folder everywhere."""
    tree = ast.parse(Path(app.__file__).read_text(encoding="utf-8"))
    readers = set()
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.ClassDef)):
            scope = statement.name
        elif isinstance(statement, ast.Assign):
            scope = " ".join(t.id for t in statement.targets if isinstance(t, ast.Name))
        else:
            scope = type(statement).__name__
        for node in ast.walk(statement):
            if (
                isinstance(node, ast.Name)
                and node.id == "FOLDER"
                and isinstance(node.ctx, ast.Load)
            ):
                readers.add(scope)
    assert readers == {"tab_folder"}


def test_git_line_shows_commit_and_push_inside_a_repository_alone(repository, tmp_path, app_state):
    """Git's line holds `commit` and `push`, text buttons (design pass 8
    §§5.3 and 6; unit M, Task 7), where a repository holds the tab's
    folder, and neither where none does, since neither would act (spec 0.3
    §10)."""
    work, _ = repository
    app_state(work)
    _, rendered = solara.render(app.GitLine(), handle_error=False)
    try:
        buttons = rendered.find(v.Html, tag="button").widgets
        assert [button.children for button in buttons] == [["commit"], ["push"]]
        assert all("bl-text-button" in button.class_.split() for button in buttons)
    finally:
        rendered.close()
    (tmp_path / "plain").mkdir()
    app_state(tmp_path / "plain")
    _, rendered = solara.render(app.GitLine(), handle_error=False)
    try:
        assert rendered.find(v.Html, tag="button").widgets == []
    finally:
        rendered.close()


def test_the_commit_form_names_each_change_and_a_rename_by_both_paths(repository, app_state):
    """The commit form lists the changes git reports under the tab's
    folder, each named; a rename is named by its new path and then its
    original, and a change left out is no longer named (spec 0.3 §5)."""
    work, _ = repository
    folder_path = work / "model"
    folder_path.mkdir()
    (folder_path / "c.yml").write_text("c: 1\n", encoding="utf-8")
    git(work, "add", "model")
    git(work, "commit", "-q", "-m", "the model")
    git(work, "mv", "model/c.yml", "model/r.yml")
    (folder_path / "e.yml").write_text("e: 1\n", encoding="utf-8")
    app_state(folder_path)
    app.open_commit("the model changed")
    assert app.form_open.value == "commit"
    paths = app.commit_paths()
    assert sorted(paths) == ["c.yml", "e.yml", "r.yml"]
    assert paths.index("c.yml") == paths.index("r.yml") + 1
    _, rendered = solara.render(app.CommitForm(), handle_error=False)
    try:
        # each change a checkbox, `aria-checked` whether it is named (unit L,
        # Task 23; design pass 4 §2), a row of the list (design pass 8 §6)
        rows = [
            row
            for row in rendered.find(v.Html, tag="button").widgets
            if "bl-commit-tick" in row.class_.split()
        ]
        assert [row.attributes["aria-checked"] for row in rows] == ["true", "true"]
        changed = [change.path for change in app.commit_changes.value]
        rows[changed.index("e.yml")].fire_event("click", {})
        assert sorted(app.commit_paths()) == ["c.yml", "r.yml"]
    finally:
        rendered.close()


def test_a_refused_commit_keeps_the_form_with_gits_sentence(repository, app_state):
    """A commit that git refuses, here through a pre-commit hook that exits
    with 1, leaves the commit form open with git's sentence as its refusal,
    its message and its names kept, and the repository holds no new commit;
    where the hook prints nothing, git's sentence is empty and the form
    says that git wrote no reason, as the list under the error mark does;
    and where the form is closed when that hook refuses the commit, the
    form stays closed, the list under the error mark says that git wrote
    no reason and the repository holds no new commit (spec 0.3 §5: git's
    sentence shown; AMD-MI-002 §6a rule 1: git's refusal of a commit
    stands in the list)."""
    work, _ = repository
    hook = work / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    hook.write_text(
        "#!/bin/sh\necho 'the hook refuses every commit' >&2\nexit 1\n", encoding="utf-8"
    )
    hook.chmod(0o755)
    (work / "notes.md").write_text("notes\n", encoding="utf-8")
    head = git(work, "rev-parse", "HEAD")
    app_state(work)
    app.open_commit("notes")
    assert app.commit_paths() == ["notes.md"]
    app.submit_commit()
    wait_until(lambda: not app.git_task.pending, 30.0, "the commit")
    assert app.form_open.value == "commit"
    assert app.form_error.value == app.git_task.value.sentence.strip()
    assert "the hook refuses every commit" in app.form_error.value
    assert app.commit_message.value == "notes"
    assert app.commit_paths() == ["notes.md"]
    assert git(work, "rev-parse", "HEAD") == head
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    app.submit_commit()
    wait_until(lambda: not app.git_task.pending, 30.0, "the commit")
    assert (app.form_open.value, app.git_task.value.sentence) == ("commit", "")
    assert app.form_error.value.startswith("git refused the commit and wrote no reason")
    assert git(work, "rev-parse", "HEAD") == head
    assert app.git_answer.value["refused"]
    assert app.form_error.value in [refusal.sentence for refusal in app.standing_refusals()]
    app.close_form()
    # the answer is emptied, so that the sentence asserted below is this run's
    app.git_answer.value = None
    app.git_task(kind="commit", message="notes", paths=("notes.md",))
    wait_until(lambda: not app.git_task.pending, 30.0, "the commit")
    assert app.git_task.finished, app.git_task.exception
    assert app.form_open.value is None
    assert app.git_answer.value["refused"]
    assert any(
        refusal.sentence.startswith("git refused the commit and wrote no reason")
        for refusal in app.standing_refusals()
    )
    assert git(work, "rev-parse", "HEAD") == head


def test_new_trellis_waits_while_git_runs_and_its_hover_names_the_wait(repository, app_state):
    """While a git command runs, the folder's icon button `New trellis`
    does not act, `aria-disabled`, and its hover names what it waits for,
    `git is running`; once the command has ended, it acts again with the
    hover that says what it writes (design pass 8 §5.5: a disabled
    control's hover names what it waits for; unit M, Task 6)."""
    work, _ = repository
    hook = work / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    # a hook that holds the commit for two seconds and then refuses it
    hook.write_text("#!/bin/sh\nsleep 2\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    (work / "notes.md").write_text("notes\n", encoding="utf-8")
    app_state(work)

    def new_trellis() -> tuple:
        # the button's mark of a control that does not act, and its hover
        _, rendered = solara.render(app.FolderActions(), handle_error=False)
        try:
            button = rendered.find(v.Html, class_="bl-new-trellis").widget
            return button.attributes.get("aria-disabled"), button.attributes["title"]
        finally:
            rendered.close()

    acting = (None, "Write a model folder beside this one")
    assert new_trellis() == acting
    app.git_task(kind="commit", message="notes", paths=("notes.md",))
    assert app.git_task.pending
    assert new_trellis() == ("true", app.GIT_RUNNING)
    wait_until(lambda: not app.git_task.pending, 30.0, "the commit")
    assert new_trellis() == acting


def test_item_4_each_export_is_ignored_and_has_its_record(repository):
    """Two exports of `declaration/stages/cons/cons.bl` under one path and
    one commit, the file and then an unsaved buffer one comment longer,
    each bound with the calibration, methods and settings the
    demonstration fills its slots with, write the view's two files and
    the record beside them; the records name the same commit, the status
    line's digests and the source files with their digests, and differ in
    the digest of the text and in the marks `unsaved` and `uncommitted`;
    git ignores the folder of the views (spec 0.3 §5; C item 4)."""
    work, _ = repository
    created = creation.create_trellis(work, "lifecycle-demo", list(DEMO_STAGES), "demo_period", 6)
    recipe = created.folder / "declaration/spec.yml"
    recipe.write_text(filled(recipe.read_text(encoding="utf-8")), encoding="utf-8")
    folder = model.open_folder(created.folder)
    named = [change.path for change in model.git_changes(folder)]
    assert model.git_commit(folder, "the demonstration's folder", named).ok
    relpath = CONS
    text = (created.folder / relpath).read_text(encoding="utf-8")
    calibration, methods, settings = (
        created.folder / name
        for name in (
            "declaration/calibration/portfolio.yml",
            "declaration/stages/cons/methods.yml",
            "declaration/settings/cons_wide.yml",
        )
    )
    digests = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (calibration, methods, settings, recipe)
    }
    records = []
    for buffer, unsaved in ((text, False), (text + "# one more line\n", True)):
        stage = model.elaborate_buffer(buffer, str(created.folder / relpath)).stage
        bound = stage.calibrate(str(calibration)).methodize(str(methods)).configure(str(settings))
        path = model.export_view(
            folder,
            bound,
            buffer,
            relpath,
            unsaved=unsaved,
            occurrence="periods[0] / cons",
            direction="backward",
            source_digests=digests,
        )
        records.append((path, json.loads(path.read_text(encoding="utf-8"))))
    (first_path, first), (second_path, second) = records
    assert first_path == second_path and first_path.parent == created.folder / "model-explorer"
    assert first["commit"] == second["commit"] == git(work, "rev-parse", "HEAD").strip()
    assert first["generated"].keys() == second["generated"].keys()
    assert len(first["generated"]) == 2
    assert first["inputs"]["text"]["sha256"] != second["inputs"]["text"]["sha256"]
    assert (first["uncommitted"], second["uncommitted"]) == (False, True)
    assert (first["occurrence"], first["direction"]) == ("periods[0] / cons", "backward")
    assert set(first["inputs"]) == {"text", "calibration", "methods", "settings"}
    assert {entry["path"]: entry["sha256"] for entry in first["source_files"]} == {
        Path(name).relative_to(created.folder).as_posix(): digest
        for name, digest in digests.items()
    }
    assert set(first["package"]) == {"bellman", "bellman-workbench"}
    for name in (*second["generated"], second_path.name):
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", f"model-explorer/{name}"], cwd=created.folder
        )
        assert ignored.returncode == 0
    assert model.git_changes(folder) == ()


def test_an_export_outside_a_repository_is_marked_uncommitted(tmp_path):
    """An export in a folder no repository holds names no commit and marks
    the text, the source file and the record uncommitted, since no commit
    holds any of its inputs (spec 0.3 §5)."""
    folder_path = written_from_the_forms(tmp_path / "plain")
    folder = model.open_folder(folder_path)
    assert folder.git_root is None
    relpath = CONS
    text = (folder_path / relpath).read_text(encoding="utf-8")
    recipe = folder_path / "declaration/spec.yml"
    path = model.export_view(
        folder,
        model.elaborate_buffer(text, str(folder_path / relpath)).stage,
        text,
        relpath,
        unsaved=False,
        occurrence=None,
        direction="backward",
        source_digests={str(recipe): hashlib.sha256(recipe.read_bytes()).hexdigest()},
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["commit"] is None
    assert record["uncommitted"] is True
    assert record["inputs"]["text"]["uncommitted"] is True
    assert [entry["uncommitted"] for entry in record["source_files"]] == [True]
