# 批量生成模式

在完整执行 `LLM3` 时，输入可能一次性提供整份 scene plan，而不是只提供当前单个 scene。

当输入中给出了完整且有顺序的 scene 列表时，你必须切换到“批量生成模式”。

## 批量输出契约

你必须输出一个顶层 JSON 对象：

```json
{
  "video_title": "string",
  "scenes": [
    {
      "... 单个 scene design schema ..."
    }
  ]
}
```

规则：

1. `scenes` 的顺序必须与 planner 输入中的顺序一致。
2. planner 中的每个 scene 都必须且只能对应一个 scene design。
3. 必须保留 planner 给出的 `scene_id` 和 `class_name`。
4. 在批量模式下，你必须从全局角度思考叙事顺序，但不要做跨 scene object 继承；每个 scene 的 `entry_state` 与 `exit_state` 都应为空。
5. 在批量模式下，不要设计任何跨 scene object 继承；每一幕需要的对象都在本幕内重新创建。
