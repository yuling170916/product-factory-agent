# Product Factory repository instructions

- Preserve the ten-stage workflow and four human gates defined in `src/product_factory/stages.py`.
- Never auto-approve requirement, functional, visual, permission, or release decisions.
- Treat deployment and other external writes as opt-in operations that require an explicit command.
- Keep the core runtime dependency-free. Prefer Python standard-library features.
- Run `python3 -m unittest discover -s tests -v` after behavior changes.
- Update the Chinese README and the Codex skill when workflow semantics change.
