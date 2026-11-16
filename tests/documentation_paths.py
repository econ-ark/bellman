"""The paths of the folders and the pages of the documentation that the tests
of this folder read, the places that their searches of the repository read,
and the pattern of the front matter of a page."""

import re

from application_files import ROOT

# the folder of the documentation, the folder of its hooks and the folder of
# its wiki of concepts
DOCS = ROOT / "docs"


HOOKS = DOCS / "_hooks"


WIKI = DOCS / "wiki"


# the methods page, which the generator `docs/_hooks/reference_pages.py`
# writes, as a path from the root of the repository
METHODS_PAGE = "docs/Bellman-Sym/reference/methods.md"


# the folders and the file whose text files the searches of the repository
# read: the pages, the lessons with their recorded outputs, the applications,
# and `AGENTS.md`, the instructions for agents, to which `CLAUDE.md` is a
# symbolic link
SEARCHED_PLACES = ("docs", "tutorials", "applications", "AGENTS.md")


# the changelog, which the searches pass over, since each dated entry keeps
# the names of its day
FILES_LEFT_OUT_OF_SEARCHES = ("docs/changelog.md",)


# the front matter of a page: the text between the line `---` that opens the
# page and the next line `---`
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
