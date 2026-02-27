# 输出前自检清单


1. JSON 是否可直接解析？
2. 根键是否严格正确？
3. 每个 `primary_item` 是否都在 `content_items` 内？
4. `derivation_steps` 是否非空且 type 合法？
5. 若存在 `concept_tree.json`，是否保持了先修优先顺序？
6. 是否包含必要的数学与校验信息，而不是只有文字描述？

