# ManimLayout-1K

ManimLayout-1K is a lightweight codebase for extracting layout-aware training data from 3Blue1Brown-style Manim source code.

The repository contains the core scripts we used to:

- extract reusable Manim components from source code
- normalize and "wash" selected components into cleaner standalone modules
- statically parse scene construction logic
- approximate object layouts with heuristic bounding boxes
- export scene-step records in JSONL format for downstream layout modeling

## Repository Structure

- `extract_manim_core.py`: extract core classes from upstream Manim / 3b1b code
- `batch_washing_pipeline.py`: batch semantic normalization pipeline for selected components
- `static_code_parser.py`: AST-based static scene parser
- `static_layout_solver.py`: heuristic layout and bounding-box solver
- `format_to_jsonl.py`: convert parsed scene steps into JSONL records
- `batch_generate_dataset.py`: batch dataset generation entry point
- `dataset_validator.py`: validate generated dataset records
- `extract_jsonl_from_source.py`: single-source extraction helper
- `extracted_core/`: extracted class definitions used as intermediate assets
- `washed_manim_components/`: cleaned / standardized component implementations
- `reconstructed_core/`: manually reconstructed example core modules

## Notes

- Large generated datasets, temporary logs, and local secrets are intentionally excluded from this public repository.
- The original `videos-master` source tree is also excluded; this repository focuses on the processing pipeline and curated artifacts.
- Some scripts use absolute paths from the original local environment and may need small path adjustments before reuse elsewhere.

## Suggested Next Step

To make the project easier for others to run, the next cleanup pass should add:

- a `requirements.txt` or `pyproject.toml`
- path configuration via CLI flags or environment variables
- a small public sample dataset for demonstration
