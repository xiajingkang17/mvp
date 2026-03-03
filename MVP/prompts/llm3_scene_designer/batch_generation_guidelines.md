# 多 scene 输出模式说明

当输入里给出 llm2 规划出的完整 scene 列表时，你处于“多 scene 输出模式”。

注意：

- 你的工作单元仍然是单个 scene
- 但这次你要把列表里的每个 scene 都依次设计出来
- 最终一次性输出整片结果，而不是只输出第一个 scene

## 顶层输出格式

多 scene 模式下，顶层必须严格输出：

```json
{
  "video_title": "string",
  "scenes": [
    {
      "... scene_01 的 design ..."
    },
    {
      "... scene_02 的 design ..."
    }
  ]
}
```

## 强规则

1. 顶层必须有 `scenes` 数组，不能直接把单个 scene 放在顶层。
2. `scenes` 数组中的每个元素，才是单个 scene 的 design JSON。
3. `scenes` 的顺序必须与 llm2 输入中的顺序完全一致。
4. llm2 中的每个 `scene_id` 都必须出现，不能漏，不能重复。
5. 不要把多个 scene 合并成一个 scene design。
6. 即使是多 scene 模式，每个 scene 仍然独立开场、独立清场，不做跨 scene object 继承。

## 单 scene 重跑模式提醒

如果输入只给了当前 scene 及前后摘要，而没有给完整 scene 列表，那么你不在多 scene 模式。

此时：

1. 顶层只输出当前 scene 的 design JSON
2. 不要输出 `video_title`
3. 不要输出 `scenes: [...]`
