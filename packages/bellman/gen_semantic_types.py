#!/usr/bin/env python3
"""Generate only the internal additions on the existing expression bases.

Run with --check to compare the listing and generated region without writing.
Old source constructors and grammar digests are never regenerated here.
"""
import argparse
import pathlib
import re

import pyasdl
from pyasdl import FieldQualifier

HERE = pathlib.Path(__file__).parent
SYNTAX = HERE / "bellman" / "syntax"
START = "# BEGIN GENERATED SEMANTIC CONSTRUCTORS\n"
END = "# END GENERATED SEMANTIC CONSTRUCTORS\n"


def parse(path):
    return pyasdl.parse(re.sub(r"--[^\n]*", "", path.read_text()))


def emit():
    old = parse(SYNTAX / "grammars" / "dynspec_full.asdl")
    new = parse(SYNTAX / "grammars" / "semantic.asdl")
    old_names = {c.name for t in old.body for c in t.value.types}
    names = set()
    out = []
    for sort in new.body:
        if sort.name == "binding":
            profile = tuple((f.kind, f.name, f.qualifier) for f in sort.value.fields)
            if profile != (("resolved_input", "variable", None), ("setexpr", "domain", None)):
                raise ValueError("binding must remain (resolved_input variable, setexpr domain)")
            continue
        if sort.name not in ("expr", "setexpr"):
            raise ValueError(f"no existing expression base for {sort.name}")
        for constructor in sort.value.types:
            name = constructor.name
            if name in old_names or name in names:
                raise ValueError(f"duplicate constructor {name}")
            names.add(name)
            base = "T.expr, T.setexpr" if name == "Unresolved" else f"T.{sort.name}"
            equality = ", eq=False" if name == "Lambda" else ""
            out.extend([f"@dataclass(frozen=True, slots=True, repr=False{equality})",
                        f"class {name}(_Expression, {base}):"])
            for field in constructor.fields:
                annotation = {"expr": "T.expr", "setexpr": "T.setexpr",
                              "reference": "Identity | str", "string": "str",
                              "binding": "tuple[ResolvedName, T.setexpr]"}[field.kind]
                if field.qualifier is FieldQualifier.SEQUENCE:
                    annotation = f"tuple[{annotation}, ...]"
                default = " = ()" if name == "Apply" and field.name == "args" else ""
                out.append(f"    {field.name}: {annotation}{default}")
            if name == "Lambda":
                out.extend(["", "    def __eq__(self, other):",
                            "        if type(self) is not type(other):",
                            "            return NotImplemented",
                            "        return alpha_equivalent(self, other)",
                            "", "    def __hash__(self):",
                            "        return hash(_alpha_key(self))"])
            out.extend(["", ""])
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = HERE / "bellman" / "typing" / "typed_expressions.py"
    source = target.read_text()
    before, rest = source.split(START)
    current, after = rest.split(END)
    generated = emit()
    if args.check:
        if current != generated:
            raise SystemExit("typed_expressions.py does not match semantic.asdl; regenerate")
        print("typed_expressions.py matches semantic.asdl; no old constructors regenerated")
    else:
        target.write_text(before + START + generated + END + after)
        print("typed_expressions.py: internal constructors regenerated on the existing expression bases")


if __name__ == "__main__":
    main()
