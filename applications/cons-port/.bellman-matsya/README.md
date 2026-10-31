# This folder is a Matsya project

Matsya is a service of Project Bellman. From an economist's description of a dynamic model it writes the model in Bellman-SYM, the project's language for staged Bellman problems, checks what it wrote, and answers questions about the model. The work on this folder's model is kept on the service in a **session**, the numbered text of one model: your entries, Matsya's questions and answers, and the **jobs** started from it, each one attempt to write and check the model's declaration.

- Session: `21b3b5e6c7ad496f986b13d59740bb47`
- Service: `http://127.0.0.1:18710`

## The files

- `economics.md`: your description of the model, from which every job starts. The client reads it and never writes it.
- `declaration/`: the declaration as it stands: the stage files `stages/<key>/<key>.bl`, each of which states one decision problem, and the period, trellis, recipe, methods, calibration and settings files, which join the stages in time and bind their methods and values. `bellman-matsya project submit` sends these files as the job's starting declaration, the files its first cycle starts from; the notes beside the stage files are not sent.
- `report.md` and `model-prose.md`: the report of the job last written into this folder, and, when the job produced it, the model prose written from `economics.md`; `bellman-matsya project pull --replace` writes these files.
- `bellman-matsya-output/job-<number>/`: the products of a job as a model folder of their own, which `bellman-matsya project pull` writes without `--replace`.
- `.bellman-matsya/project.json`: the session's identifier, the service's address and the digest of `economics.md` as the session last received it, which the client writes.
- `.bellman-matsya/README.md`: this note, which `bellman-matsya project init` writes.
- `.bellman-matsya/writer-note.md`: the writer's note from the latest pull into this folder that produced one. It is kept apart from an author's stage page.

Everything else, the session's entries and the jobs with their records, is kept on the service. `.bellman-matsya/project.json` names the service's address and holds no Matsya token; commit `.bellman-matsya/` with the folder, or add it to the folder's `.gitignore` when the folder's repository is public.

## The commands used most

Run them in this folder.

- `bellman-matsya project status` prints the session: its entries; its jobs, each by its label, such as `household · stage · version 2 · job 3 · converged`, which names the model, the job's target, the version of the text the job read, the job's number and its state; and each question awaiting a reply, with the command that answers it.
- `bellman-matsya project submit` appends `economics.md` to the session when it has changed since the session last received it, and starts a job with the files of `declaration/` as its starting declaration. The job's target, the level of the declaration it returns, is read from those files: `recipe` with a methods, calibration, settings or recipe file, `trellis` with `trellis.yml`, `period` with a period file, and `stage` otherwise; `--target` names another.
- `bellman-matsya project pull` writes the products of the session's latest job that holds a record: with `--replace` into this folder, each file of the job's declaration replacing the file of the same path, the files the job did not write kept and `economics.md` left as it is; otherwise into `bellman-matsya-output/job-<number>/`.
- `bellman-matsya ask 21b3b5e6c7ad496f986b13d59740bb47 "<question>"` asks matsya-master, the service's conversation side, a question about this model.

Project, job, session, ask, index and search commands print structured answers with `--json` and refuse what they cannot do with one sentence. `bellman-matsya docs` lists the pages of the user guide installed with the client, and `bellman-matsya docs --all` prints them all.
