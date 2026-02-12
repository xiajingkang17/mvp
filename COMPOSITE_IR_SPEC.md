# Composite IR 冻结规范（P0）

版本：`composite_ir_v0.1`  
状态：**Frozen for P1-P8**

## 1. 适用范围

- 本规范定义 `CompositeObject.params.graph` 的字段、单位、坐标系和约束语义。
- 外层布局系统只把 `CompositeObject` 当作一个 object。

## 2. 外层约束（冻结）

- 一个题意整图在 scene 外层必须是一个 object（`type=CompositeObject`）。
- 外层只负责把这个 object 放到 slot，不参与内部子组件排布。

## 3. 坐标系与单位（冻结）

- 内部坐标系：二维笛卡尔，`x` 向右为正，`y` 向上为正。
- 角度单位：**degree**（度）。
- 尺寸单位：`space.unit` 指定，默认 `scene_unit`。
- 默认原点：`space.origin = "center"`。
- `z` 不参与几何求解，仅渲染层保留（默认 0）。

## 4. Graph 顶层结构（冻结）

```json
{
  "version": "0.1",
  "space": {
    "x_range": [-10, 10],
    "y_range": [-6, 6],
    "unit": "scene_unit",
    "angle_unit": "deg",
    "origin": "center"
  },
  "parts": [],
  "tracks": [],
  "constraints": [],
  "motions": []
}
```

## 5. 字段定义（冻结）

### 5.1 parts

每个 part 对应一次组件库实例化：

```json
{
  "id": "p1",
  "type": "Block",
  "params": {},
  "style": {},
  "seed_pose": { "x": 0, "y": 0, "theta": 0, "scale": 1.0 }
}
```

约束：

- `id` 全局唯一
- `type` 必须存在于当前组件库枚举
- `params` 必须通过组件参数白名单校验

### 5.2 tracks

轨道几何定义（P1 先支持 line/segment/arc）：

```json
{
  "id": "t1",
  "type": "segment",
  "data": { "x1": -2, "y1": 1, "x2": 3, "y2": 0 }
}
```

### 5.3 constraints

关系约束（P1 静态）：

```json
{
  "id": "c1",
  "type": "on_segment",
  "args": { "part_id": "p1", "anchor": "bottom_center", "track_id": "t1", "t": 0.5 },
  "hard": true
}
```

P1 允许类型：

- `attach`
- `on_segment`
- `midpoint`
- `align_axis`
- `distance`

### 5.4 motions

运动约束（P5 开启）：

```json
{
  "id": "m1",
  "type": "on_track",
  "args": { "part_id": "p1", "anchor": "bottom_center", "track_id": "t1" },
  "timeline": [{ "t": 0.0, "s": 0.0 }, { "t": 1.0, "s": 1.0 }]
}
```

## 6. 非质点运动语义（冻结）

- 轨道约束作用在 **anchor**（接触点），不直接作用在中心点。
- 每帧由 anchor 位置反算中心位姿，避免“中心点穿轨道”。
- 默认支持锚点：`center`、`bottom_center`、`top_center`、`left_center`、`right_center`。

## 7. 外层 slot 放置（冻结）

- 先在内部坐标系完成整图。
- 计算整图 bbox：`W_obj, H_obj`。
- slot 可用框：`W_slot, H_slot`。
- 缩放因子：`s = min(W_slot / W_obj, H_slot / H_obj)`（等比）。
- 再按 slot 锚点平移放置。

## 8. 校验规则（冻结）

- graph 缺字段、错类型、引用不存在 part/track 必须报错。
- part 参数越权（不在白名单）必须报错。
- hard constraint 未满足（残差超阈值）必须报错或触发降级策略。
- 未知 constraint/motion 类型必须报错。

## 9. 降级策略（冻结）

- 若求解失败，允许回退到 `seed_pose` 生成静态图，但必须产生日志：
  - `resolved_pose.json`
  - `constraint_residuals.json`

## 10. P0 冻结结论

- 以上字段命名、单位、坐标轴方向、角度单位、外层单 object 约束已冻结。
- 后续阶段（P1-P8）必须以本规范为准；如需变更，先更新本文件并评审。
