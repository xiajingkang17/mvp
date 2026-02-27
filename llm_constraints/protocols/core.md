# 通用力学画图协议：核心层（V1）

## 1. 数据结构

统一使用四段式：

- `parts`：图元组件实例（Wall、Block、ArcTrack...）
- `tracks`：参数化轨道（line/arc/segment，参数字段使用 `data`）
- `constraints`：装配与几何约束
- `motions`：时间相关运动（可选）

## 2. 基础约定

- 坐标语义为二维平面；实现层可自动补 `z=0`。
- 角度单位统一为度（除非另行声明）。
- JSON 约束参数统一用 `args`，禁止 `params`。
- JSON 轨道参数统一用 `tracks[].data`（不要用 `tracks[].params`）。
- 组件与锚点必须来自白名单，不允许自由造词。

## 3. 输出最低要求

1. 至少一个基准件（作为整体布局参考）。
2. 几何连接对象必须通过 `constraints` 显式连接。
3. 若有可动物体，必须有对应运动约束（见 `motion.md`）。
