# Mixed Workflow

Provider map:

- `llm1 = anthropic`
- `llm2 = kimi`
- `llm3 = kimi`
- `llm35 = anthropic`
- `llm4 = anthropic`
- `llm5 = anthropic`

Prompts are shared from:

- [prompts](/e:/AI4Learning-Backend/manim/MVP/prompts)

Common commands:

```powershell
python pipeline/mixed_workflow/run_mvp.py --run-dir cases/demo_001 --no-render
python pipeline/mixed_workflow/run_llm1.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm2.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm3.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm35.py --run-dir cases/demo_001
python pipeline/mixed_workflow/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
python pipeline/mixed_workflow/run_llm5.py --run-dir cases/demo_001
```
