# 输出合同

只输出一个严格 JSON 对象（不要 Markdown）。

## 根结构

- `version`: string
- `objects`: array

## `objects[]` 固定字段

- `object_id`: string
- `code_key`: string（snake_case）
- `spec`: object（必须符合 DSL 骨架）
- `motion_span_s`: number 或 null
- `notes`: string 或 null（可选）

## `spec` DSL 骨架

- `dsl_version`: string（建议 `"1.0"`）
- `kind`: `new_component | special_motion | complex_effect | hybrid | custom`
- `geometry`: object
- `style`: object
- `motion`: object
- `effects`: object
- `meta`: object

禁止在 `spec` 顶层新增以上以外的键。

## `spec.motion.driver`（可选，但复杂运动建议提供）

当需要把运动自动回填到 `scene_plan` 时，必须输出：

```json
{
  "driver": {
    "type": "state_driver",
    "target_object_id": "composite_object_id",
    "motion_id": "m_xxx",
    "part_id": "p_xxx",
    "args": {
      "mode": "model",
      "param_key": "tau",
      "orient_mode": "fixed",
      "model": {
        "kind": "ballistic_2d",
        "params": {}
      }
    },
    "timeline": [
      {"t": 0.0, "tau": 0.0},
      {"t": 4.0, "tau": 1.0}
    ]
  }
}
```

硬性约束：

1. `driver.type` 必须是 `state_driver`。
2. `driver.target_object_id` 必须指向一个 `CompositeObject`（不是 `CustomObject`）。
3. `driver.part_id` 必须是目标 CompositeObject 内部 `graph.parts[].id`。
4. `driver.args.mode` 必须是 `model`。
5. `driver.args.param_key` 必须是 `tau`。
6. `driver.args.model.kind` 只允许：
   - `ballistic_2d`
   - `uniform_circular_2d`
   - `sampled_path_2d`
7. `driver.timeline` 至少 2 个关键帧，`t` 严格递增。
8. 若 `kind=sampled_path_2d`，`params.samples` 必须是严格递增的 `{tau,x,y}` 数组，且 timeline 的 tau 在样本范围内。
