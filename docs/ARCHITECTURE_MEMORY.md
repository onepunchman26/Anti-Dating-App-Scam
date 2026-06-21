# Architecture Memory

This document preserves the long-term architecture direction for AI-SlowMatch / Anti-Dating-App-Scam so future Codex sessions do not need chat history to understand the project.

## Why Move Away From FastAPI-First Design

The first working scaffold used FastAPI because it is a fast way to expose risk analysis, trust ladder evaluation, and journaling behind stable contracts. That remains useful, but it should not be the product center.

The project is a local-first relationship safety tool, not a centralized platform. A server-first design can accidentally suggest cloud storage, account systems, platform matchmaking, or always-online data flows. Those are not the current goals.

The conceptual center should be:

```text
desktop GUI
  -> user-owned local documents
  -> provider-agnostic AI engine
  -> schema-valid and optionally signed risk reports
```

FastAPI may remain as an optional local API for automation, local integrations, or tests. It should not define the user experience or data ownership model.

## Why The Python Core Engine Remains Useful

Python is still the right early engine language because:

- AI provider SDKs and testing tools are mature in Python.
- The existing risk analyzer, trust ladder engine, safety policy, and mock provider are already Python modules.
- Python is fast to iterate while the product vocabulary, schemas, and safety boundaries are still changing.
- The core engine can remain UI-independent and later be called from PySide6, Tauri sidecars, tests, or an optional local API.

The engine should avoid GUI assumptions. GUI code should call engine functions, not the other way around.

## Why PySide6 Is The Current GUI Phase

PySide6 gives the project a local desktop GUI without introducing a web build pipeline too early. It fits the short-term goal:

- local conversation input;
- local consent checkbox;
- risk report panel;
- trust ladder view;
- provider settings;
- report export and verification views.

PySide6 is not necessarily the final shell. It is a practical bridge from backend prototype to local desktop tool.

## Why Tauri Plus Python Sidecar Is A Future Direction

Tauri can eventually provide a smaller, more polished, cross-platform shell with controlled local file access and stronger packaging options. A Python sidecar allows the existing engine to keep running while the UI shell evolves.

The migration should be gradual:

1. Keep the Python engine stable and UI-independent.
2. Add a Tauri GUI shell only after schemas and workflows settle.
3. Call Python through a controlled sidecar bridge.
4. Move security-sensitive layers to Rust/Tauri only where there is a clear benefit.

## Why C Is Not Suitable As The Main Project Language

C is powerful but not a good primary language for this project phase. The main work involves AI adapters, JSON Schema validation, GUI iteration, document workflows, testing, and safety logic. C would slow iteration and increase memory-safety risk without solving the core product problem.

C may be useful for specialized dependencies in the ecosystem, but it should not be the main application language.

## Why C++/Qt May Be Considered Later

C++/Qt could produce a mature native desktop app and has strong GUI tooling. However, it is not first priority because:

- the AI and schema layers are still changing;
- Python already has working core modules;
- PySide6 gives access to Qt while preserving Python speed;
- moving to C++ too early would increase build and packaging complexity.

C++/Qt can be reconsidered if the project needs deeper native performance, mature desktop packaging, or long-term Qt investment.

## Why JSON And JSON Schema Are Core

JSON should be the primary data format because it is easy to inspect, validate, test, sign, export, and pass across Python, Tauri, Rust, and provider adapters.

JSON Schema should define:

- personal relationship profile documents;
- risk reports;
- trust ladder records;
- provider outputs where possible.

Schema validation creates durable boundaries between AI output and trusted application data.

## Why XML Is Optional Only

XML can be supported later for import/export interoperability, but it should not be the core format. XML signatures, namespaces, and validation rules add complexity that is not needed for the current prototype.

Use XML only when a future integration requires it.

## Digital Signature Versus Encryption

A digital signature and encryption solve different problems.

A signature proves integrity and source under a known key. It helps answer: "Has this report changed since it was signed, and was it signed by this key?"

Encryption protects confidentiality. It helps answer: "Can unauthorized people read this file?"

The project may eventually need both, but signed reports should not be described as private or encrypted unless encryption is actually implemented.

## What Signed Reports Prove

A signed report can prove:

- the report conforms to the project schema at signing time;
- the canonical report content has not changed after signing;
- the report was signed by a specific local key if the verifier trusts that key.

A signed report cannot prove:

- the submitted conversation is authentic;
- the submitted conversation is complete;
- any real person committed wrongdoing;
- AI output is objectively true;
- a relationship is safe forever.

Required disclaimer:

> A valid signature means this report has not been modified after signing and conforms to the project schema. It does not prove that the submitted conversation is authentic, complete, or that any real person has committed wrongdoing.
