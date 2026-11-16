# Additions read by the tests

This folder holds methods files, refusals files and two small models that the tests of the package read and that no application holds.

- **Refusals files.** Each folder named after an application, such as `cons-port/`, holds a file `refusals.bl`. Its items are additions to one stage file of that application, each written as an author might write it by mistake. Read into its stage file, each refusals file is refused, and each item but one is refused for the reason that the comment above it gives, with the refusal rule. The exception is the first item of `smooth-ambiguity-savings/refusals.bl`, which the package admits, as its comment says.
- **Two methods files of consumption-savings-iid.** The folder `consumption-savings-iid/` also holds `methods.bl` and `methods.additions.bl`. The application's own methods file holds the union of the two, and the tests read the two files in that order.
- **Two models written for the tests.** The folder `models-for-the-tests/` holds `buffer-stock-pension/`, the buffer-stock stage with a pension account over six periods, and `retirement-choice-pension/`, the retirement choice with a pension account over fifteen periods. Each holds a stage file, its additions and a trellis file.

`expected.json` is a stored record of runs. A run reads a stage file with its additions in order; most runs read a stage file of an application with its methods file. For each run the record gives the application or the model (`study`), the stage file (`stage`), the additions in the order read (`additions`), the number of places of the stage with the additions (`places`), and the places that the additions create (`created`). Its field `from_message` is false in every run, and no test reads it.

The tests of `packages/bellman/tests/test_two_levels_and_several_methods_files.py` read the refusals files, the two methods files of `consumption-savings-iid/`, the stage files and additions of the two models, and `expected.json`. The tests of `packages/bellman/tests/test_recipes.py` read the trellis files of the two models and the stage file of the retirement choice.
