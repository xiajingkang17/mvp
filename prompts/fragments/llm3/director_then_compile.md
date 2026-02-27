# 导演后编译（必须执行）
在每个 scene 内先做导演决策，再编译为 JSON。

导演决策要点：
1. 本 scene 主焦点对象是谁。
2. 观众阅读顺序（先看什么，后看什么）。
3. 动作节奏（引入 -> 建立 -> 强调 -> 过渡）。
4. 是否需要跨 scene 连续对象（进入 `keep`）。

编译映射：
1. 焦点与阅读顺序 -> `layout.placements`。
2. 动作节奏 -> `actions`。
3. 跨场景连续 -> `keep`。
4. 仅在需要时输出 `roles`，且 roles 中对象必须在 `placements/actions/keep` 出现。
