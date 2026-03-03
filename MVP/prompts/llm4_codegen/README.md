# LLM4 Shared Prompt Library

This directory no longer defines a standalone `LLM4 codegen` stage.

It is kept only as shared reference material for:

- `LLM4B scene_codegen`
- `LLM4C motion_codegen`
The reusable files here are:

- `layout_contract.md`
- `lifecycle_rules.md`
- `execution_helpers.py`
- `component_reference_notice.md`

Do not point `LLMClient.load_stage_system_prompt(...)` at this directory directly.
