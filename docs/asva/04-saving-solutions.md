---
audience: user
type: user-guide
topic: [numerical-representation]
---
# Saving solutions

> [!summary]
> `save_solution` writes a solution, a structure of dictionaries and lists whose leaves are arrays, numbers and strings, to a folder: the arrays to a compressed NumPy archive, and the rest of the structure with the reader's metadata to a JSON file. `load_solution` reads the folder back and returns the structure and the metadata. Neither file is a Python pickle, the format in which Python stores its own objects and which only Python reads, so the folder can also be read without asva, by any program that reads the two formats.

> [!info]- Relationship with other documents
> **Builds on** — [The runner](02-the-runner.md): the module `asva.run.io` among the modules of the runner.
> **See also** — [The cross-entropy method](06-cross-entropy-method.md) §5: the checkpoints of an estimation, which are written separately.

## 1 Writing a solution

```python
save_solution(path, solution, metadata=None)
```

`path` is a folder, `solution` any structure of the reader's, for instance a list holding, for each period of a trellis, a dictionary of the arrays that the reader's solver computed, and `metadata` a dictionary of the reader's own, such as the method and the grid sizes. `save_solution` creates the folder with any missing parent, writes two files into it, replacing files of the same names, and returns the folder as a `pathlib.Path`:

| File | Holds |
|---|---|
| `solutions.npz` | every array of the solution, compressed, under its dotted path: the array at `solution["periods"][0]["c"]` under the key `periods.0.c` |
| `metadata.json` | `skeleton`, the structure with each array replaced by a reference to its key and every other leaf in place; `user_metadata`, the dictionary given as `metadata`; `array_keys`, the keys of the archive in alphabetical order |

A NumPy number among the leaves is written as a Python number.

## 2 Reading it back

`load_solution(path)` returns the pair `(solution, metadata)`: the structure with its arrays read from the archive, and the dictionary given as `metadata` when the solution was written. A structure of dictionaries with string keys and of lists is read back as it was written. Three differences follow from the JSON format. A dictionary key is read back as a string, so a dictionary keyed by the integers 0, 1, … is read back keyed by `"0"`, `"1"`, …; a solution with string keys avoids the difference. A tuple is read back as a list. An array inside a tuple is not placed in the archive, since only dictionaries and lists are searched for arrays; it is written into the JSON file as a list of numbers.

```python
import numpy as np
from asva.run.io import save_solution, load_solution

solution = {
    "periods": [{"c": np.array([0.5, 0.75, 1.0]), "note": "terminal"}],
    "solve_seconds": 1.25,
}
folder = save_solution("results/run_001", solution, metadata={"method": "EGM", "n_a": 3})
print(sorted(p.name for p in folder.iterdir()))

back, metadata = load_solution(folder)
print(back["periods"][0]["c"], back["periods"][0]["note"], back["solve_seconds"], metadata)
```

```text
['metadata.json', 'solutions.npz']
[0.5  0.75 1.  ] terminal 1.25 {'method': 'EGM', 'n_a': 3}
```
