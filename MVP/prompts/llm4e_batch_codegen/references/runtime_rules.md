# 运行时规则

`llm4e` 的职责是一次性生成整片中的所有 `scene_method` 与 `motion_method`。  
framework helper 已经存在，不要重新定义。

## 可直接调用的 Helper

可以直接假设下面这些 helper 已经存在，而且名称固定不可改：

1. `reset_scene(self, self.objects)`
2. `register_obj(self, self.objects, obj_id, mobject)`
3. `fit_in_zone(mobject, zone_rect, width_ratio=..., height_ratio=...)`
4. `place_in_zone(mobject, zone_rect, offset=...)`
5. `place_in_zone_anchor(mobject, zone_rect, anchor=..., margin_ratio=..., offset=...)`
6. `layout_formula_group(formulas, zone_rect)`
7. `make_wrapped_text_block(text, zone_rect, font_size=..., color=..., anchor=...)`
8. `show_subtitle(self, self.objects, text, subtitle_zone_rect)`
9. `run_step(self, self.objects, subtitle_text, subtitle_zone_rect, keep_ids, step_fn)`
10. `cleanup_step(self, self.objects, keep_ids)`
11. `cleanup_scene(self, self.objects, keep_ids)`

## scene 方法最小调用模板

推荐模式：

```python
def scene_scene_01(self):
    reset_scene(self, self.objects)

    zone_main = (0.05, 0.95, 0.18, 0.88)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        obj = ...
        register_obj(self, self.objects, "obj", obj)
        self.add(obj)

    run_step(self, self.objects, "字幕文本", zone_subtitle, ["obj"], step_01)
    cleanup_scene(self, self.objects, [])
```

## scene 方法生命周期

1. 开头先 `reset_scene(self, self.objects)`
2. 用 `run_step(...)` 逐步推进 narration、对象创建和动画
3. 每个 step 末尾调用 `cleanup_step(...)`
4. scene 结束时调用 `cleanup_scene(self, self.objects, [])`

## 对象注册规则

1. 任何后续 step 或 motion 还会再次使用的对象，都必须 `register_obj(...)`
2. 如果对象只是一步中的临时局部对象，可以不注册，但后面不能再引用
3. 不要依赖局部变量跨 step 存活

## run_step 的职责边界

1. `run_step(...)` 负责字幕显示与节奏控制
2. `step_fn` 里只做对象创建、更新和动画
3. 不要在 `step_fn` 里重复写字幕逻辑
4. 不要在 `step_fn` 里重复实现 cleanup 逻辑

## Zone 与字幕区强约束

1. 所有 zone 都必须是数值四元组 `(x0, x1, y0, y1)`
2. zone 不能是 `None`，不能是 mobject，也不能是 `self.camera.frame`
3. 第一次调用 `run_step(...)` 前，必须先定义有效字幕区
4. 传给 `run_step(...)` 的第四个参数必须始终是有效 zone tuple

## 禁止写法

1. 不要重新定义 runtime helper
2. 不要手写第二套字幕系统
3. 不要手写逐对象清理循环去替代 `cleanup_step(...)` / `cleanup_scene(...)`
4. 不要写 `zone_main = self.camera.frame` 或类似写法
