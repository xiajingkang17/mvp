# Motion 模块说明

本目录把原来的 `render/composite/motion.py` 拆成了按职责划分的子模块。

## 文件职责

1. `__init__.py`

- 对外统一导出接口（兼容旧调用路径 `from render.composite.motion import ...`）。
- 当前导出的核心函数：
  - `apply_motions`
  - `evaluate_timeline`
  - `timeline_bounds`
  - `resolve_motion_pose_args`
  - `evaluate_state_driver_target`
  - `find_state_driver_end_event`
  - `parse_state_driver_end_condition`

1. `common.py`

- 通用工具函数，不包含业务逻辑：
  - `_arg`: 多键参数读取
  - `_to_float` / `_to_float_or_none`: 数值转换
  - `_to_bool`: 布尔归一化

1. `timeline.py`

- 关键帧时间线计算：
  - `evaluate_timeline`: 在给定时间 `t` 上做线性插值
  - `timeline_bounds`: 获取 timeline 起止时间
- 被 `track_motion.py`、`state_driver.py`、`physics_world.py` 复用。

1. `track_motion.py`

- 轨道类运动逻辑：
  - `on_track`
  - `on_track_schedule`
- 核心函数：
  - `_apply_on_track`
  - `_apply_on_track_schedule`
  - `resolve_motion_pose_args`（把 motion 转成 on_track_pose 约束参数）
- 依赖 `solver.on_track_pose.apply` 来真正执行贴轨位姿更新。

1. `state_driver.py`

- 无轨道状态驱动逻辑（`motion.type == state_driver`）：
  - `ballistic_2d`
  - `uniform_circular_2d`
  - `sampled_path_2d`
- 核心函数：
  - `evaluate_state_driver_target`
  - `parse_state_driver_end_condition`
  - `find_state_driver_end_event`
- 负责根据 `timeline + model` 计算目标位姿 `(x, y, theta)`。

1. `engine.py`

- 运动总调度入口：
  - `apply_motions`
- 按 motion 类型分发到 `track_motion` 或 `state_driver`，并回写每个 part 的 pose。

## 调用关系（简化）

1. 场景渲染阶段调用 `apply_motions`（`engine.py`）。
2. `engine.py` 遍历 `graph.motions`：

- 轨道类：调用 `track_motion.py`
- 无轨道类：调用 `state_driver.py`

3. 子模块都通过 `timeline.py` 做参数随时间插值。

## 扩展建议

1. 新增轨道运动类型：优先改 `track_motion.py`。
2. 新增无轨道模型（新 kind）：改 `state_driver.py`。
3. 不要把新业务逻辑塞进 `common.py`；`common.py` 只放纯工具函数。
