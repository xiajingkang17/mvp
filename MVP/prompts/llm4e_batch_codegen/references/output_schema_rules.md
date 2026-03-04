# 输出结构规则

## 顶层结构

输出必须是一个 JSON 对象，且顶层只能包含：

1. `class_name`
2. `scenes`

示例：

```json
{
  "class_name": "MainScene",
  "scenes": [
    {
      "scene_id": "scene_01",
      "scene_method": "def scene_scene_01(self): ...",
      "motion_method": "def motion_scene_01(self, step_id): ..."
    }
  ]
}
```

## scenes 数组规则

1. `scenes` 必须是数组
2. 顺序必须与输入中的 `interface_contract.scenes` 完全一致
3. 不能漏 scene
4. 不能重复 scene
5. 不能重排

## 每个 scene 元素规则

每个元素只能包含：

1. `scene_id`
2. `scene_method`
3. `motion_method`

不要添加其他字段。

## 方法代码规则

1. `scene_method` 必须是完整的 `def scene_scene_xx(self): ...`
2. `motion_method` 必须是完整的 `def motion_scene_xx(self, step_id): ...`
3. 不要输出 `import`
4. 不要输出 `class MainScene`
5. 不要输出 framework helper 定义
6. 不要输出 markdown 代码块
7. 不要输出解释、前言、总结、注释说明

## 缺省规则

1. 某个 scene 没有运动，也必须输出对应 `motion_method`
2. 无运动时 `motion_method` 返回 `[]`
