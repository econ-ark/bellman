"""Execute the lessons of the tutorials collection and record what each one read.

A lesson is a notebook under ``tutorials/``, a folder named
``.ipynb_checkpoints`` excepted. Its name is its path under ``tutorials/``
without the suffix, such as ``getting-started/01-the-stage``. The second
markdown cell of a lesson lists the files the lesson reads, each as a code
span holding its path from the repository root. These files are the lesson's
inputs, with one file every lesson executes without listing it: the set-up
module ``tutorials/checkout.py``, which its first code cell imports. The
package lays a drawing out itself, with the Graphviz libraries inside the
Python package ``pygraphviz``; the tool stops before executing where that
package is not installed.

The record is ``tutorials/lessons.json``. For each lesson it holds the
lesson's path, the SHA-256 digest of the notebook after its last execution,
the status of that execution, ``completed`` or ``failed``, with its failures,
and each input's path with the digest the file had when the lesson was
executed. A change to an input or to the notebook therefore shows as a
difference of digests, and the lesson is executed again.

``--record`` executes every lesson, or the lessons named, each in a fresh
kernel whose working directory is the lesson's folder and whose environment
sets ``BELLMAN_DDSL_ROOT`` to the checkout holding this file and sets
``BELLMAN_LESSONS_HEADLESS``, under which a lesson's interactive view,
``checkout.explore``, writes its two files and starts no server; it writes
the executed notebook in place and the lesson's entry in the record. ``--check``
executes nothing: it recomputes the digests of the notebooks and of their
inputs, prints the lessons whose record no longer describes them, and exits
with status 1 when there is one.

A failure is a code cell with an error output that is not tagged
``raises-exception``, a cell so tagged that raised no error, an execution
stopped by a time limit or by the kernel's end, an input missing or changed
during the execution, and a second markdown cell that lists no file. A lesson
changed on disk while it was executed is not written, and the tool stops.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import nbformat

HERE = Path(__file__).resolve().parent


def repository_root():
    """The checkout holding this file: the nearest folder above it that holds
    packages/bellman."""
    for candidate in HERE.parents:
        if (candidate / 'packages/bellman').is_dir():
            return candidate
    raise RuntimeError(f'No folder above {HERE} holds packages/bellman.')


ROOT = repository_root()
TUTORIALS = ROOT / 'tutorials'
RECORD = TUTORIALS / 'lessons.json'
# the set-up module that the first code cell of every lesson imports
SETUP = 'tutorials/checkout.py'
# a code span: text between two single backticks on one line
CODE_SPAN = re.compile(r'(?<!`)`([^`\n]+)`(?!`)')
TIME_LIMIT_SECONDS = 600
# the short form of a drawing, which a cell shows alone where the kernel's
# environment cannot lay the drawing out
SHORT_FORM_OF_A_DRAWING = re.compile(r'Drawing of \d+ boxes')


def digest(path):
    """The SHA-256 digest of a file's bytes, as hexadecimal text."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lessons():
    """The path of every lesson, in the order of their names."""
    return sorted(path for path in TUTORIALS.rglob('*.ipynb')
                  if '.ipynb_checkpoints' not in path.relative_to(TUTORIALS).parts)


def lesson_name(path):
    """The lesson's path under tutorials/ without the suffix .ipynb."""
    return path.relative_to(TUTORIALS).with_suffix('').as_posix()


def lesson_path(name):
    """The notebook of the lesson a user names, written with or without the
    folder tutorials/ and the suffix .ipynb."""
    name = name.removeprefix('tutorials/').removesuffix('.ipynb')
    return TUTORIALS / (name + '.ipynb')


def listed_files(notebook):
    """The paths the second markdown cell of a notebook lists as code spans,
    each once, in the cell's order; no path when the notebook has fewer than
    two markdown cells."""
    markdown = [cell for cell in notebook.cells if cell.cell_type == 'markdown']
    if len(markdown) < 2:
        return []
    return list(dict.fromkeys(CODE_SPAN.findall(markdown[1].source)))


def setup_files():
    """The files every lesson executes besides those it lists, each from the
    repository root: the set-up module."""
    return [SETUP]


def input_digests(paths):
    """Each path with the digest of the file it names from the repository
    root, or None when it names no file."""
    return {path: digest(ROOT / path) if (ROOT / path).is_file() else None for path in paths}


def read_record():
    """The record as the file holds it; empty when there is no file."""
    return json.loads(RECORD.read_text(encoding='utf-8')) if RECORD.exists() else {}


def write_record(record):
    """Write the entries of the lessons that exist, in the order of their names."""
    names = {lesson_name(path) for path in lessons()}
    kept = {name: record[name] for name in sorted(record) if name in names}
    RECORD.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def set_checkout_variable():
    """Set BELLMAN_DDSL_ROOT to this checkout for the kernels the tool starts;
    stop when the variable already names another checkout."""
    named = os.environ.get('BELLMAN_DDSL_ROOT')
    if named is not None and Path(named).resolve() != ROOT:
        raise RuntimeError(f'BELLMAN_DDSL_ROOT names {named}, not the checkout of this tool, {ROOT}.')
    os.environ['BELLMAN_DDSL_ROOT'] = str(ROOT)


def set_headless_variable():
    """Set BELLMAN_LESSONS_HEADLESS for the kernels the tool starts, so that a
    lesson's checkout.explore writes its files and starts no server."""
    os.environ['BELLMAN_LESSONS_HEADLESS'] = '1'


def verify_layout_program():
    """Stop unless a drawing can be laid out, with the message the package
    gives where the Python package pygraphviz is not installed. Without it a
    cell holding a drawing would show its short form and no picture. The
    package's drawing module answers, read from this checkout in the
    environment that runs the tool; `cell_failures` reads what the kernel's
    environment gave."""
    sys.path.insert(0, str(ROOT / 'packages/bellman'))
    from bellman.display import drawing
    if drawing.pygraphviz is None:
        raise RuntimeError(drawing.NO_LAYOUT)


def cell_failures(notebook):
    """The failures an executed notebook shows: an error output in a cell not
    tagged raises-exception, a cell so tagged without an error output, and a
    drawing that a cell shows as its short form with no picture."""
    failures = []
    for cell in notebook.cells:
        if cell.cell_type != 'code':
            continue
        errors = [output for output in cell.outputs if output.output_type == 'error']
        tagged = 'raises-exception' in cell.metadata.get('tags', [])
        if errors and not tagged:
            failures += [f'cell {cell.get("id")}: {error.ename}: {error.evalue}' for error in errors]
        if tagged and not errors:
            failures.append(f'cell {cell.get("id")}: tagged raises-exception but raised no error')
        for output in cell.outputs:
            data = output.get('data', {})
            shown = ''.join(data.get('text/plain', '')).strip()
            if SHORT_FORM_OF_A_DRAWING.fullmatch(shown) and 'image/svg+xml' not in data:
                failures.append(f'cell {cell.get("id")}: a drawing is shown without its picture; '
                                'install the Python package pygraphviz in the environment of the kernel')
    return failures


def execute(path):
    """Execute one lesson in a fresh kernel, write it in place, and return its
    entry in the record."""
    from nbclient import NotebookClient
    from nbclient.exceptions import CellTimeoutError, DeadKernelError

    original = path.read_bytes()
    notebook = nbformat.reads(original.decode('utf-8'), as_version=4)
    sources = [cell.source for cell in notebook.cells]
    listed = listed_files(notebook)
    inputs = listed + [name for name in setup_files() if name not in listed]
    before = input_digests(inputs)
    failures = [] if listed else ['the second markdown cell lists no file']
    failures += [f'input missing: {name}' for name, value in before.items() if value is None]
    print(f'Executing {path.relative_to(ROOT)} in a fresh kernel.', flush=True)
    client = NotebookClient(notebook, timeout=TIME_LIMIT_SECONDS, allow_errors=True,
                            resources={'metadata': {'path': str(path.parent)}})
    try:
        client.execute()
    except (CellTimeoutError, DeadKernelError) as stopped:
        failures.append(f'execution stopped: {type(stopped).__name__}: {stopped}')
    failures += cell_failures(notebook)
    if [cell.source for cell in notebook.cells] != sources:
        failures.append('a cell source changed during the execution')
    after = input_digests(inputs)
    failures += [f'input changed during the execution: {name}'
                 for name in inputs if after[name] != before[name] and before[name] is not None]
    if path.read_bytes() != original:
        raise RuntimeError(f'The lesson changed on disk during its execution; nothing written: {path}')
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    status = 'failed' if failures else 'completed'
    print(f'{lesson_name(path)}: {status}' + ''.join(f'\n  {failure}' for failure in failures), flush=True)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path),
            'status': status, 'failures': failures, 'inputs': before}


def record(paths, jobs=1):
    """Execute the lessons at `paths`, `jobs` of them at a time in separate
    processes (each lesson in its own fresh kernel), and write each entry into
    the record as soon as its lesson is executed."""
    set_checkout_variable()
    set_headless_variable()
    verify_layout_program()
    entries = read_record()
    if jobs <= 1 or len(paths) <= 1:
        for path in paths:
            entries[lesson_name(path)] = execute(path)
            write_record(entries)
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=min(jobs, len(paths))) as pool:
            running = {pool.submit(execute, path): path for path in paths}
            for finished in as_completed(running):
                entries[lesson_name(running[finished])] = finished.result()
                write_record(entries)
    print(f'Record written to {RECORD.relative_to(ROOT)}.', flush=True)


def reasons_to_execute(path, entry):
    """Why the lesson at `path` must be executed again; none when its entry
    still describes it."""
    if entry is None:
        return ['no record']
    reasons = [] if entry['status'] == 'completed' else ['its last execution failed']
    if digest(path) != entry['sha256']:
        reasons.append('the notebook differs from its executed version in the record')
    for name, value in input_digests(entry['inputs']).items():
        if value is None:
            reasons.append(f'input missing: {name}')
        elif value != entry['inputs'][name]:
            reasons.append(f'input changed: {name}')
    return reasons


def check(paths):
    """Print each lesson's state against the record and return 1 when a lesson
    must be executed again or the record holds a lesson that no longer exists,
    else 0."""
    entries = read_record()
    stale = sorted(set(entries) - {lesson_name(path) for path in lessons()})
    due = 0
    for path in paths:
        reasons = reasons_to_execute(path, entries.get(lesson_name(path)))
        due += bool(reasons)
        print(f'{lesson_name(path)}: ' + ('execute again: ' + '; '.join(reasons) if reasons else 'up to date'))
    for name in stale:
        print(f'{name}: recorded, but the lesson no longer exists; --record removes the entry')
    print(f'{len(paths)} lessons checked, {due} to be executed again, {len(stale)} entries without a lesson.')
    return 1 if due or stale else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--record', action='store_true',
                        help='execute the lessons named, or all, and write their entries in the record')
    action.add_argument('--check', action='store_true',
                        help='report the lessons whose record no longer describes them; execute nothing')
    parser.add_argument('--jobs', type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)),
                        help='lessons executed at a time, each in its own process (default: half the processors, at most 8)')
    parser.add_argument('names', nargs='*',
                        help='lesson names, such as getting-started/01-the-stage (default: every lesson)')
    arguments = parser.parse_args()
    paths = [lesson_path(name) for name in arguments.names] or lessons()
    unknown = [name for name, path in zip(arguments.names, paths) if path not in lessons()]
    if unknown:
        parser.error('no lesson of this name: ' + ', '.join(unknown))
    if arguments.record:
        record(paths, jobs=arguments.jobs)
    else:
        sys.exit(check(paths))


if __name__ == '__main__':
    main()
