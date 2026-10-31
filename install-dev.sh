#!/bin/bash
# Installs the development environment of this repository into venv/: the
# packages of requirements.txt, then the three packages of the repository,
# bellman, asva and bellman-workbench, in editable mode. Run it from the
# repository root, with
# python3 being Python 3.12 or later; to build the environment on another
# Python, delete venv/ first.
set -e
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt
venv/bin/python -m pip install -e packages/bellman
venv/bin/python -m pip install -e packages/asva
# Bellman Workbench: its page imports bellman, and its view needs the viewer
# package of bellman's extra explore, which requirements.txt installs above
venv/bin/python -m pip install -e packages/bellman-workbench
