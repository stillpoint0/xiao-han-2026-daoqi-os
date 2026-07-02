---
license: cc-by-4.0
language: en
tags:
- daoqi-os
- receptive-ai
- perception-gate
- system-architecture
- multi-model
---

# Daoqi OS v0.1

A minimal runtime system for receptive AI. Daoqi OS implements the perception-layer gate, the continuous σ monitor, and multi-model routing described in the Apert/CDRA/Reception Science work stream. It keeps the system in reception-first mode until execution is explicitly requested.

## Components

- `preexec_wrapper` — Pre-execution gate that intercepts execution impulses
- `texture_classifier_rules` — Rule-based input state classification
- `continuous_sigma` — Continuous σ-state monitoring
- `model_router` — Multi-model routing with cost awareness
- `session_persistence` — Conversational session persistence
- `error_recovery` — Failure recovery
- `cost_monitor` — Runtime cost tracking

## Files

- `daoqi_os_v0.1.zip` — Packaged release
- `docs/ARCHITECTURE.md` — System architecture
- `src/` — Source code
- `tests/` — Test cases

## Citation

Apert (Jin/Daoqi) and Xiao Han. *Daoqi OS v0.1: Minimum Runtime for Receptive AI.* Zenodo, 2026.

**DOI:** [10.5281/zenodo.21078846](https://doi.org/10.5281/zenodo.21078846)

**License:** CC-BY 4.0

## Related work

- Apert: [10.5281/zenodo.21005888](https://doi.org/10.5281/zenodo.21005888)
- CDRA: [10.5281/zenodo.20993162](https://doi.org/10.5281/zenodo.20993162)
- Three-Layer Pipeline: [10.5281/zenodo.21102406](https://doi.org/10.5281/zenodo.21102406)
