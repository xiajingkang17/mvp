# 对象生命周期执行规则（LLM4 必须执行）

当输入 scene_design 中存在 `object_manifest` 与 `lifecycle_contract` 时，必须按该契约编码，不得忽略。

## 执行要求

1) 维护对象注册表（例如 `objects: dict[str, Mobject]`）。  
2) 对每个 step，按 `create/update/remove/keep` 执行：  

- `create`: 创建并注册对象。  
- `update`: 对已存在对象执行变换/动画。  
- `remove`: 本 step 内显式淡出或移除。  
- `keep`: step 结束后允许继续存活的对象。  

3) step 结束时，自动清理“不在 keep 且仍在场”的对象（`FadeOut` 或 `Uncreate`）。  
2) scene 结束时，清理所有不在 `scene_end_keep` 的对象。  
3) 若 `scene_end_keep` 与 `scene_plan.carry_over` 冲突，以两者交集为准。  

## 禁止项

- 禁止把所有对象挂在场上直到 scene 结束再一次性清空。  
- 禁止忽略 `remove` 指令。  
- 禁止对象 id 混乱（同一 id 对应不同语义对象）。  
