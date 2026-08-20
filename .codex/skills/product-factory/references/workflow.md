# Product Factory workflow reference

## Stage and gate map

| Stage | Primary output | Gate after stage |
|---|---|---|
| `prd` | Confirmable PRD archive | `requirement_confirmation` |
| `tech-selection` | Architecture and stack decision | — |
| `development-spec` | Implementable technical contract | — |
| `development-validation-1` | Feasibility/test evidence | `functional_acceptance` |
| `frontend-guide` | Project frontend rules | — |
| `visual-style` | Comparable visual directions | `visual_acceptance` |
| `integration` | Product code and integration report | — |
| `development-validation-2` | Integrated acceptance evidence | — |
| `launch-guide` | Environment/deploy/rollback guide | `release_decision` |
| `production-validation` | Real online validation evidence | — |

## Decision responsibilities

- Requirement confirmation: product owner confirms scope, non-goals, assumptions, and acceptance criteria.
- Functional acceptance: product/QA owner confirms behavior is worth continuing, not merely that files exist.
- Visual acceptance: design/product owner chooses a direction and verifies interaction/visual quality.
- Release decision: authorized owner confirms credentials, target environment, costs, migration, monitoring, rollback, and timing.

Rejected gates remain blocking. Revise the relevant artifact or implementation and collect a new explicit decision. Do not reinterpret silence as approval.

## Evidence language

Use exactly distinguishable outcomes: passed, failed, blocked, and not run. A generated test plan is not a test run. A local build is not an online validation. An HTTP 200 alone is not full functional acceptance.

## Version 0.1 rerun limitation

The CLI does not yet invalidate downstream artifacts automatically. When revising a stage after later work exists, first identify every downstream artifact based on the changed assumption, preserve user data, then rerun or update those artifacts explicitly. Never silently delete files.
