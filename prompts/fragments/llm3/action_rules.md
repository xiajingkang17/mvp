# 动作规则（必须满足）

1. `op` 只能是 `play` 或 `wait`。
2. `wait` 必须提供 `duration` 且 `duration >= 0`。
3. `play.anim` 必须来自允许的动画列表。
4. `fade_in/fade_out/write/create/indicate` 必须给非空 `targets`。
5. `transform` 必须满足其一：
   - 显式提供 `src` 与 `dst`
   - 或 `targets` 至少 2 个（`targets[0]` 视作 `src`，`targets[1]` 视作 `dst`）
6. 严禁：
   `{"op":"play","anim":"transform","targets":["only_one"]}`
