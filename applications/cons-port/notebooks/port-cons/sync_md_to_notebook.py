#!/usr/bin/env python3
"""
Sync markdown files in md-cells/ back into the notebook.

The .md files are the source of truth for markdown content.
In the live notebook, each markdown section is a code cell that
calls ``display(Markdown(open('md-cells/XX.md').read_text()))``.
This script converts those code cells back to proper markdown
cells — needed as a **pre-build step** for the static site
(mkdocs-jupyter with ``execute: false``).

Usage:
    python sync_md_to_notebook.py          # preview (dry-run)
    python sync_md_to_notebook.py --apply  # write changes

Each .md file must have a header comment with the cell ID:
    <!-- notebook cell <index> | id: <cell_id> -->
"""

from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

NB_PATH   = Path(__file__).parent / 'solve_port_cons_ffp.ipynb'
MD_DIR    = Path(__file__).parent / 'md-cells'
HEADER_RE = re.compile(r'<!--\s*notebook cell \d+\s*\|\s*id:\s*(\S+)\s*-->')
AUTO_RE   = re.compile(r'<!--\s*auto-extracted[^>]*-->\s*\n?')


def load_md_files() -> dict[str, str]:
    """Load all .md files, keyed by cell ID from the header comment."""
    result = {}
    for mdfile in sorted(MD_DIR.glob('*.md')):
        if mdfile.name == 'README.md':
            continue
        text = mdfile.read_text()
        m = HEADER_RE.search(text)
        if not m:
            print(f'  SKIP {mdfile.name}: no cell-ID header found', file=sys.stderr)
            continue
        cell_id = m.group(1)
        # Strip the two header comment lines
        body = HEADER_RE.sub('', text, count=1).lstrip('\n')
        body = AUTO_RE.sub('', body, count=1).lstrip('\n')
        result[cell_id] = body
    return result


def source_to_list(text: str) -> list[str]:
    """Convert a string to the notebook source format (list of lines)."""
    if not text:
        return []
    lines = text.split('\n')
    result = [line + '\n' for line in lines[:-1]]
    if lines[-1]:
        result.append(lines[-1])
    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--apply', action='store_true',
                        help='Write changes to the notebook (default: dry-run)')
    args = parser.parse_args()

    with open(NB_PATH) as f:
        nb = json.load(f)

    md_sources = load_md_files()
    print(f'Loaded {len(md_sources)} markdown files from {MD_DIR.name}/')

    # Match cells by ID and convert code → markdown
    converted = 0
    for i, cell in enumerate(nb['cells']):
        cid = cell.get('id', '')
        if cid not in md_sources:
            continue

        new_src = md_sources[cid]
        first_line = new_src.strip().split('\n')[0][:60]

        if cell['cell_type'] == 'code':
            converted += 1
            print(f'  CONVERT cell {i} ({cid}): code → markdown: {first_line}...')
            if args.apply:
                cell['cell_type'] = 'markdown'
                cell['source'] = source_to_list(new_src)
                # Remove code-only fields
                cell.pop('execution_count', None)
                cell.pop('outputs', None)
                # Remove hide-input tag (not needed for markdown cells)
                tags = cell.get('metadata', {}).get('tags', [])
                if 'hide-input' in tags:
                    tags.remove('hide-input')
                if not tags:
                    cell.get('metadata', {}).pop('tags', None)

        elif cell['cell_type'] == 'markdown':
            old_src = ''.join(cell['source'])
            if old_src.rstrip() != new_src.rstrip():
                converted += 1
                print(f'  UPDATE  cell {i} ({cid}): {first_line}...')
                if args.apply:
                    cell['source'] = source_to_list(new_src)

    print(f'\n{converted} cell(s) to convert/update.')

    if converted == 0:
        print('Nothing to do.')
        return

    if not args.apply:
        print('Dry run — use --apply to write changes.')
        return

    with open(NB_PATH, 'w') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print(f'Wrote {NB_PATH.name}')


if __name__ == '__main__':
    main()
