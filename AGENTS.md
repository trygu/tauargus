# Tau-Argus Rewrite — Agent Instructions

You are helping port **Tau-Argus** (a Statistical Disclosure Control tool) to
open-source solvers, a cloud-native portable build, and a Python CLI that
replaces the Swing/Java frontend.

## Read this first, every session
- **`PROGRESS.md`** is the single source of truth: goals, architecture map,
  verified builds, the current task, blockers, and the "Next Move" section.
  Read it top-to-bottom before doing anything.
- When you make meaningful progress (a build verified, a blocker cleared, a
  decision made), **update `PROGRESS.md`** so a fresh session can resume. Keep
  the "Verified builds" checkboxes and "Next Move" current.

## Repository layout
- `native/` — the real SDC engine, 5 **git submodules** (C/C++):
  `core` (static), `csp` (HiGHS-backed LP), `hitas` (links csp),
  `crp` (controlled rounding, being ported SCIP→HiGHS), `rounder` (links crp).
  Build work happens *inside* each submodule — commit there, then bump the
  submodule pointer in the parent.
- `src/tauargus/` — the legacy Java/Swing frontend (to be deleted, Task 8).
- `data/` — sample `.asc` / `.arb` / `.ttf` files for end-to-end verification.

## Build commands (macOS/Apple Silicon, this machine)
- HiGHS + SCIP via brew: `-DHighs_DIR=$(brew --prefix)/lib/cmake/Highs`
- A module builds with:
  `cmake -S native/<mod> -B native/<mod>/build -DHighs_DIR=$(brew --prefix)/lib/cmake/Highs && cmake --build native/<mod>/build`
- Header: HiGHS C API is `<highs/interfaces/highs_c_api.h>` (NOT `highs/highs_c_api.h`).

## Working agreement
- The product is the **headless Python CLI + batch (`.arb`) path**, not GUI.
- All solver backends converge on **HiGHS** (drop CPLEX/XPRESS/old-SCIP).
- Prefer editing existing files; follow each file's conventions.
- Don't commit unless asked. When asked, commit **submodules first**, then the
  parent (submodule pointer + `PROGRESS.md` + any new top-level files).
