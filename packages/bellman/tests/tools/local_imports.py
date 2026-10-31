"""Count imports inside functions and classes, report cycles among modules, and
check every import against the order of the folders.

This script measures four facts of a package under `packages/bellman/`. First,
for every `.py` file, it counts the `ast.Import` and `ast.ImportFrom` nodes
that lie inside a `FunctionDef`, `AsyncFunctionDef` or `ClassDef` body, and
those that do not (module-level, including imports under `if` or `try` at the
top of the file). Second, it builds the directed graph of imports among the
package's own modules — from the imports at the module heads and from those
inside bodies alike, since an import inside a body is as much an edge of the
graph as one at the head — resolving relative imports, and prints the cycles
of that graph as lists of module names. The package root
`bellman/__init__.py` is excluded from the graph; it exports nothing, and the
three namespaces resolve their names on first use through their tables.
Third, it prints each import of a module in one of the
folders that reads a later folder, the package root or a module that stands
at the root, `bellman/refusals.py` excepted, which every folder may read.
The order of the folders is read from the table of the folders in
`packages/bellman/README.md`, the first column of its rows in order: the rule
of the structure review of 24 September 2026, §5.1. The script refuses to run,
saying why, when the README has no heading of the folders, when the table
names no folder, or when it leaves out a folder of the package, whose imports
the order could not place. Fourth, it reads the export table `_EXPORTS` of
every package under the root that holds one, `bellman.stage`, `bellman.period`
and `bellman.trellis`, and prints each entry that names no module of the
package, or a module that does not define the name, and each name two tables
map to different modules; the tables are read by no import statement, so the
order of the folders does not see them.

`--package` names the package to measure by its dotted name, `bellman` by
default, the whole of the layout; one of the folders, `bellman.stage` for
instance, measures that folder alone. A module whose name is the package or
lies under it is measured, and an import of a module outside it is no edge.

With `--strict` the script exits 1 when any nested import exists, when the
graph has a cycle, when an import reads against the order of the folders, or
when a table entry names no module or no defined name; it exits 0 otherwise.
Without `--strict` it always exits 0 after printing.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # the repository root, above packages/bellman/tests/tools/
IMPORT_ROOT = ROOT / "packages" / "bellman"
README = IMPORT_ROOT / "README.md"
PACKAGE_PREFIX = "bellman"
DEFAULT_PACKAGE = "bellman"
# the module at the root that every folder may read
READ_BY_EVERY_FOLDER = "refusals"


def folder_order(readme=README):
    """The folders of the package in their order: the first column of the
    rows of the table under the README's heading of the folders, each a
    folder's name in backticks, up to the first row that names none.

    Refuses a README without that heading, a table that names no folder,
    and a table that leaves out a folder of the package (`package_folders`),
    since the imports of a folder the order does not hold would escape the
    check."""
    lines = Path(readme).read_text(encoding="utf-8").splitlines()
    start = next((index for index, line in enumerate(lines)
                  if line.startswith("## ") and "The folders" in line), None)
    if start is None:
        raise SystemExit(f"{readme} has no heading of the folders, a line opening with "
                         f"'## ' that names 'The folders'")
    found = []
    for line in lines[start + 1:]:
        if line.startswith("#"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.startswith("|") or not cells or set(cells[0]) <= set("-: "):
            continue
        name = cells[0]
        if found and not (name.startswith("`") and name.endswith("`")):
            break
        if name.startswith("`") and name.endswith("`"):
            found.append(name.strip("`"))
    if not found:
        raise SystemExit(f"{readme} lists no folders under its heading of the folders")
    missing = [name for name in package_folders() if name not in found]
    if missing:
        which = "a folder" if len(missing) == 1 else "folders"
        raise SystemExit(f"the table of the folders in {readme} leaves out "
                         f"{', '.join(missing)}, {which} of the package; the order of the "
                         f"folders is read from that table, so every folder stands in it")
    return tuple(found)


def package_folders():
    """The folders of the package: the directories directly under
    `packages/bellman/bellman/` that hold a Python module, by name."""
    return sorted(path.name for path in package_directory(DEFAULT_PACKAGE).iterdir()
                  if path.is_dir() and path.name != "__pycache__"
                  and any(path.rglob("*.py")))


def export_tables(package=DEFAULT_PACKAGE):
    """The export table of each package beneath the root that holds one: for
    every `__init__.py` under `package`, other than `bellman/__init__.py`
    itself, that assigns `_EXPORTS` a dictionary of string constants, (the
    package's dotted name, {name: the dotted module name}), in the order of
    the files."""
    found = []
    for path in python_files(package):
        if not is_package_init(path):
            continue
        if module_name(path) == PACKAGE_PREFIX:
            # the root is left out, as `build_graph` leaves it out too
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for statement in tree.body:
            if not (isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Dict)):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "_EXPORTS"
                       for target in statement.targets):
                continue
            entries = {key.value: value.value
                       for key, value in zip(statement.value.keys, statement.value.values)
                       if isinstance(key, ast.Constant) and isinstance(value, ast.Constant)}
            found.append((module_name(path), entries))
    return found


def defined_names(path):
    """The names a module defines at its top level: its functions, its
    classes and the targets of its assignments; a name an import binds is
    not a definition."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(statement.name)
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            names.update(node.id for target in targets for node in ast.walk(target)
                         if isinstance(node, ast.Name))
    return names


def table_defects(tables):
    """Each entry of the export tables that names no module of the package or
    a module that does not define the name, and each name that two tables
    map to different modules: (namespace, name, what is wrong), in the order
    of the tables and their entries."""
    found = []
    first_module = {}
    for namespace, entries in tables:
        for name, dotted in entries.items():
            path = IMPORT_ROOT.joinpath(*dotted.split(".")).with_suffix(".py")
            if not path.is_file():
                path = IMPORT_ROOT.joinpath(*dotted.split(".")) / "__init__.py"
            if not path.is_file():
                found.append((namespace, name, f"names no module {dotted}"))
            elif name not in defined_names(path):
                found.append((namespace, name, f"{dotted} defines no {name}"))
            elif name in first_module and first_module[name] != dotted:
                found.append((namespace, name,
                              f"stands in another table under {first_module[name]}; a name in two "
                              f"tables names one module"))
            else:
                first_module.setdefault(name, dotted)
    return found


def package_directory(package):
    """The directory of the package named by its dotted name."""
    return IMPORT_ROOT.joinpath(*package.split("."))


def python_files(package):
    """Every .py file under the package, sorted by path relative to the
    repository root."""
    files = [path for path in package_directory(package).rglob("*.py")
             if "__pycache__" not in path.parts]
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def module_name(path):
    """The dotted module name of a file under packages/bellman/."""
    relative = path.relative_to(IMPORT_ROOT)
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_package_init(path):
    """True when the file is a package __init__.py."""
    return path.name == "__init__.py"


def classify_imports(tree):
    """Nested and module-level import counts, and every import node of the
    file, at its head or inside a body, for the graph."""
    nested = 0
    module_level = 0
    nodes = []

    def walk(node, enclosed):
        nonlocal nested, module_level
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                if enclosed:
                    nested += 1
                else:
                    module_level += 1
                nodes.append(child)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                walk(child, True)
            else:
                walk(child, enclosed)

    walk(tree, False)
    return nested, module_level, nodes


def package_parts(mod, init):
    """The package that a relative import is resolved against."""
    parts = mod.split(".")
    if not init:
        parts = parts[:-1]
    return parts


def resolve_from(mod, init, node):
    """The package modules an ImportFrom node names, relative imports resolved."""
    if node.level:
        parts = package_parts(mod, init)
        climb = node.level - 1
        if climb:
            if climb > len(parts):
                return []
            parts = parts[: len(parts) - climb]
        if node.module:
            return [".".join(parts + node.module.split("."))]
        return [".".join(parts + [alias.name]) for alias in node.names]
    if node.module:
        return [node.module]
    return []


def imported_modules(mod, init, node):
    """The module names an import statement names."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    bases = resolve_from(mod, init, node)
    if node.level and node.module is None:
        return bases
    named = list(bases)
    for alias in node.names:
        for base in bases:
            named.append(f"{base}.{alias.name}")
    return named


def cycles_of(graph):
    """The strongly connected components that are cycles, each a sorted list
    of module names; the list of cycles is sorted by its first name."""
    index = 0
    stack = []
    indices = {}
    lowlinks = {}
    on_stack = set()
    components = []

    def strongconnect(node):
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for successor in graph.get(node, ()):
            if successor not in indices:
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[successor])
        if lowlinks[node] == indices[node]:
            component = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.append(member)
                if member == node:
                    break
            components.append(component)

    for node in graph:
        if node not in indices:
            strongconnect(node)
    cycles = []
    for component in components:
        looping = len(component) > 1 or component[0] in graph.get(component[0], ())
        if looping:
            cycles.append(sorted(component))
    cycles.sort(key=lambda names: names[0])
    return cycles


def build_graph(rows):
    """The import graph among the measured package's own modules, excluding
    `bellman/__init__.py`, which resolves public names on first use."""
    own = {row["module"] for row in rows if row["module"] != PACKAGE_PREFIX}
    graph = {name: set() for name in own}
    for row in rows:
        if row["module"] == PACKAGE_PREFIX:
            continue
        for imported in row["imported"]:
            if imported in own and imported != row["module"]:
                graph[row["module"]].add(imported)
            elif imported in own and imported == row["module"]:
                graph[row["module"]].add(imported)
    return {name: frozenset(targets) for name, targets in graph.items()}


def read_targets(mod, init, node):
    """What an import statement reads, each as the folder or the root module
    it stands in: a folder's name, `refusals`, or `root` for the package root
    and every other module at the root."""
    if isinstance(node, ast.Import):
        dotted = [alias.name for alias in node.names]
    else:
        bases = resolve_from(mod, init, node)
        if not bases:
            return []
        dotted = bases
        if bases == [PACKAGE_PREFIX]:
            # `from bellman import x`: a folder or a root module by name
            dotted = [f"{PACKAGE_PREFIX}.{alias.name}" for alias in node.names]
    found = []
    for name in dotted:
        parts = name.split(".")
        if parts[0] != PACKAGE_PREFIX:
            continue
        found.append(parts[1] if len(parts) > 1 else "root")
    return found


def order_violations(rows, order):
    """Each import of a module in a folder that reads a later folder, the
    package root or a module at the root other than `refusals`: (path, line,
    what it reads)."""
    found = []
    for row in rows:
        parts = row["module"].split(".")
        # the package root and the modules at the root stand above every
        # folder; every folder is in the order, which `folder_order` checks
        if len(parts) < 2 or parts[1] not in order:
            continue
        own = order.index(parts[1])
        for node, target in row["targets"]:
            if target == READ_BY_EVERY_FOLDER or (target in order and order.index(target) <= own):
                continue
            what = f"the later folder {target}" if target in order else "the root"
            found.append((row["path"], node.lineno, what))
    return found


def analyse(package=DEFAULT_PACKAGE):
    """One record per module: counts, module name, the modules it imports, at
    its head and inside its bodies alike, and what each import reads."""
    rows = []
    for path in python_files(package):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        nested, module_level, nodes = classify_imports(tree)
        mod = module_name(path)
        init = is_package_init(path)
        imported, targets = [], []
        for node in nodes:
            imported.extend(imported_modules(mod, init, node))
            targets.extend((node, target) for target in dict.fromkeys(read_targets(mod, init, node)))
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "module": mod,
                "nested": nested,
                "module_level": module_level,
                "imported": imported,
                "targets": targets,
            }
        )
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    order = folder_order()
    parser.add_argument(
        "--package",
        default=DEFAULT_PACKAGE,
        help=f"the package to measure, by its dotted name (default {DEFAULT_PACKAGE}, "
             f"the whole layout; one of the folders {', '.join(order)} measures that "
             f"folder alone)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a nested import, a cycle, an import against the order of the folders or "
             "a table entry without its definition exists",
    )
    arguments = parser.parse_args(argv)
    rows = analyse(arguments.package)
    print("path\tnested\tmodule_level\ttotal")
    nested_total = 0
    for row in rows:
        total = row["nested"] + row["module_level"]
        nested_total += row["nested"]
        print(f"{row['path']}\t{row['nested']}\t{row['module_level']}\t{total}")
    tables = export_tables(arguments.package)
    defects = table_defects(tables)
    print("tables")
    if not tables:
        print("none")
    for namespace, entries in tables:
        wrong = [defect for defect in defects if defect[0] == namespace]
        for _, name, what in wrong:
            print(f"{namespace}\t{name}\t{what}")
        if not wrong:
            print(f"{namespace}\t{len(entries)} names\tevery entry names a module that defines it")
    graph = build_graph(rows)
    cycles = cycles_of(graph)
    print("cycles")
    if cycles:
        for cycle in cycles:
            print(repr(cycle))
    else:
        print("none")
    violations = order_violations(rows, order)
    print(f"imports against the order {', '.join(order)}")
    if violations:
        for path, line, what in violations:
            print(f"{path}:{line}\treads {what}")
    else:
        print("none")
    if arguments.strict and (nested_total or cycles or violations or defects):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
