# 布局规则（必须满足）
1. `layout.type` 必须是 `free`。
2. `layout.placements` 的 key 必须是 `scene_draft` 中已存在对象 id。
3. 每个 placement 必须包含 `cx/cy/w/h`，可选 `anchor`。
4. 数值范围：`cx,cy ∈ [0,1]`；`w,h ∈ (0,1]`。
5. `anchor` 仅允许：`C/U/D/L/R/UL/UR/DL/DR`。
6. 场内优先保持单焦点，避免对象重叠。
