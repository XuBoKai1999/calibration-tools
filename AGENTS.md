# Repository instructions

開始工作前依序讀取 `arch.md`、`steps.md`、`chat/handoff.md`，之後只檢查當前任務直接相關的 source/data；除非確有必要或使用者要求，不得全面重讀 repository。

- 如無必要勿增實體；不要重設計無關且正常運作的架構。
- 只做當前任務，不提前實作後續 roadmap。
- `past/*/source/` 是 immutable originals：不得重新命名、修改、覆寫、normalize 或刪除。
- 真實 runtime／historical data 不得 commit。
- canonical format 必須由真實歷史資料推導，不得憑空設計。
- 未知資訊不得靜默丟棄；標記為 unresolved，等待人工判讀。
- substantial work 後更新 `chat/handoff.md`。
- 每次 final response 仍須以相同全文寫入下一個 `chat/NNN.txt`；不寫 commentary、tool output 或額外敏感資料。





## Development principles

### Keep the design minimal

Follow the principle:

> Do not introduce a new entity unless it is necessary.

Prefer extending an existing module, file, abstraction, or data structure when it already has a clear responsibility for the new behavior.

Do not create new files, classes, layers, managers, registries, wrappers, or abstractions merely for organizational symmetry.

Before adding a new entity, check whether the responsibility already belongs naturally to an existing one.

This principle applies to implementation structure, not to required project-level documentation defined below.

---

## Persistent project context

Conversation context is temporary. Important project state must therefore be persisted in the repository.

The repository should remain usable across separate agent conversations without requiring the previous conversation window.

---

## `chat/`

Maintain `chat/` as a sequential archive of agent responses.

Its primary purpose is to make previous conversation output easy to transfer into another GPT or agent conversation when needed.

Therefore, do not treat `chat/` merely as a filtered decision log.

After each substantive response, save the response text into `chat/`.

Use sequential zero-padded filenames:

```text
chat/001.md
chat/002.md
chat/003.md
...
```

Before writing a new entry:

1. inspect the existing filenames in `chat/`;
2. determine the highest existing sequence number;
3. use the next number.

For example, if `chat/005.md` already exists, the next response should normally be stored as:

```text
chat/006.md
```

Preserve enough of the response that it can later be given directly to another GPT as conversation context.

Do not overwrite earlier chat records.

Trivial acknowledgements or responses containing no useful project content may be omitted, but prefer preservation when uncertain.

`chat/` is chronological history and transferable conversation context.

It is not the authoritative description of the current project state.

---

## `handoff.md`

Maintain `handoff.md` as the compact current-state handoff for a new agent session.

Unlike `chat/`, it is not chronological.

It should contain only information that is currently relevant, including:

- current goal;
- current implementation status;
- important active design decisions;
- unresolved issues;
- known bugs or risks;
- immediate next actions;
- files relevant to the current work.

Remove or replace obsolete information when decisions change.

The goal is that a fresh agent conversation can resume the project without first rereading the entire repository or the complete `chat/` history.

A new session should normally begin with:

1. `AGENTS.md`
2. `handoff.md`
3. `steps.md`
4. `arch.md`

Then inspect only the code or documentation relevant to the current task.

Read historical files under `chat/` only when additional historical context is actually needed.

---

## `manual/`

Maintain a `manual/` directory as the user-facing documentation area for the software.

The exact internal structure of `manual/` should remain proportional to the size and complexity of the project.

The agent may choose either:

```text
manual/
  manual.md
```

or, when separation is genuinely useful:

```text
manual/
  getting-started.md
  input-format.md
  output-format.md
  materials.md
  examples.md
  ...
```

Do not split documentation into multiple files merely for neatness.

Conversely, do not force unrelated or excessively large documentation into one file merely to minimize file count.

Apply the same principle:

> Do not introduce a new documentation entity unless the separation has a concrete benefit.

The manual should describe the software as it currently works, including where relevant:

- available features;
- supported workflows;
- commands;
- APIs;
- input formats;
- output formats;
- configuration;
- examples;
- limitations.

Do not describe planned functionality as already implemented.

---

## `arch.md`

Maintain `arch.md` as the authoritative description of the current software architecture.

Update it whenever a change affects:

- module responsibilities;
- program structure;
- data flow;
- file layout;
- major abstractions;
- public interfaces;
- ownership of functionality between components.

It should describe the current architecture and accepted design decisions.

Remove obsolete architecture rather than accumulating outdated alternatives.

---

## `steps.md`

Maintain `steps.md` as the concise implementation roadmap.

Update it whenever:

- a step is completed;
- a new required step is discovered;
- priorities change;
- a planned step becomes unnecessary;
- the implementation strategy changes.

Keep it operational and concise.

Do not turn `steps.md` into a development diary.

---

## Documentation synchronization

Project documentation must evolve together with the implementation.

When new ideas are accepted or implementation changes the project design, update the relevant documentation during the same task rather than postponing documentation indefinitely.

After substantive work, check whether any of the following need updating:

1. `chat/` — archive the response;
2. `handoff.md` — current working state changed;
3. `arch.md` — architecture changed;
4. `steps.md` — roadmap changed;
5. `manual/` — user-visible behavior changed.

Avoid changing documentation when nothing meaningful has changed.

---

## Context-loading policy

Do not reread the entire repository automatically at the beginning of every conversation.

Use progressive context loading.

Start from:

```text
AGENTS.md
handoff.md
steps.md
arch.md
```

Then inspect relevant source files.

Use `chat/` as recoverable historical conversation context when necessary.

The intended hierarchy is:

```text
chat/       = chronological transferable conversation history
handoff.md  = current short-term project state
arch.md     = current architecture
steps.md    = current roadmap
manual/     = current user-facing documentation
source code = implementation truth
```
