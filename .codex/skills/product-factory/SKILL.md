---
name: product-factory
description: Turn an approved PRD into a locally and online-verifiable product through a gated ten-stage engineering workflow. Use when Codex must derive technical documents, generate and integrate frontend/backend code, prepare frontend and release guides, run development or production validation, or resume a Product Factory workspace while preserving human approval gates for requirements, functionality, visual design, permissions, and release.
---

# Product Factory

Advance one product workspace through the repository's deterministic workflow. Treat the PRD, manuals, specs, prior artifacts, and recorded human decisions as the source of truth.

## Start or resume

1. Locate the repository root and read `README.md` for CLI setup.
2. For a new product, require an already determined PRD. Initialize with `product-factory init`.
3. For an existing workspace, inspect `product-factory status` and `.product-factory/state.json`.
4. Run only to the next human gate with `product-factory run`.

Read [references/workflow.md](references/workflow.md) before interpreting a gate, changing stage semantics, or handling a failed/rejected stage.

## Preserve the control boundary

- Let the CLI own stage order, cursor state, required outputs, and decisions.
- Never edit `.product-factory/state.json` directly.
- Never approve a human gate on the user's behalf.
- Do not claim a test, build, deployment, or online check passed without recorded evidence.
- Do not deploy, publish to GitHub, write to production, request permissions, or incur cost unless the user explicitly authorizes that specific external action.
- Keep secrets out of PRDs, artifacts, prompts, logs, and the repository.

## Execute a stage

Use the current stage Spec in `specs/`, all fixed manuals in `manuals/`, `prd.md`, `factory.config.json`, and completed upstream artifacts. Create every output required by `src/product_factory/stages.py`. When information is missing, record a blocker instead of inventing a result.

For development stages, work only inside `product/`, run proportionate local validation, and put exact commands and outcomes in the stage report. For visual selection, propose comparable options and wait for a person to choose. For production validation, require an approved release decision and a real target; otherwise report the stage as blocked or unverified.

## Report progress

State the completed stage, created artifacts, validation evidence, unresolved risks, and the exact pending human gate. A paused workflow is a successful control outcome, not an error.
