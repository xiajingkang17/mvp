# 输出前自检
1. 是否只输出了一个 JSON 对象？
2. scene id 是否与 `scene_draft` 一一对应且无缺失？
3. 每个 scene 是否都有 `layout/actions/keep`？
4. `layout.type` 是否全部为 `free`？
5. `placements` 是否只引用已存在对象 id，且坐标尺寸范围合法？
6. `actions` 是否满足 transform 合同（`src+dst` 或至少两个 `targets`）？
7. `roles`（若有）是否只引用本 scene 实际使用对象？
