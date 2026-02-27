# 数学增强规则（对齐 Math-To-Manim 思路）

1. 每一问都应有明确“数学核心”：
   - 至少 1 条 `equation` 或 1 条 `reasoning`（说明使用定律/守恒/约束）。
2. 数值题优先包含完整链路：
   - `equation`（符号关系）
   - `compute`（代入与化简）
   - `intermediate_result` / `result`
3. `global_symbols` 应覆盖关键符号并给出含义，单位尽量补全。
4. `sanity_checks` 至少包含一种校验：
   - 单位一致性
   - 极限/边界情形
   - 物理可行性（方向、大小、正负、数量级）
5. 若有关键前提（光滑、忽略阻力、理想碰撞等），必须体现在 `given_conditions` 或 `derivation_steps.reasoning`。
