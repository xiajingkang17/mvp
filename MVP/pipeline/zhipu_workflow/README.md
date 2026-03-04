# Zhipu Workflow

Provider map:
- `llm1 = zhipu`
- `llm2 = zhipu`
- `llm3 = zhipu`
- `llm35 = zhipu`
- `llm4 = zhipu`
- `llm5 = zhipu`

Prompts are shared from:
- [prompts](/e:/AI4Learning-Backend/manim/MVP/prompts)

Common commands:

```powershell
python pipeline/zhipu_workflow/run_mvp.py --run-dir cases/demo_001 --no-render
python pipeline/zhipu_workflow/run_llm1.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm2.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm3.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm35.py --run-dir cases/demo_001
python pipeline/zhipu_workflow/run_llm4.py --run-dir cases/demo_001 --max-fix-rounds 10
python pipeline/zhipu_workflow/run_llm5.py --run-dir cases/demo_001
```
