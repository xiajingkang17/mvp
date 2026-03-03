# Scene Runtime Contract

`scene_codegen` 的职责是把 `scene_design` 编译成单个 scene 方法。  
scene 框架层 helper 已经存在，不要重新定义。

## 可直接调用的 Helper

可以直接假设下面这些 helper 已经存在，而且名称固定不可改：

- `reset_scene(self, self.objects)`
- `register_obj(self, self.objects, obj_id, mobject)`
- `fit_in_zone(mobject, zone_rect, width_ratio=..., height_ratio=...)`
- `place_in_zone(mobject, zone_rect, offset=...)`
- `layout_formula_group(formulas, zone_rect)`
- `show_subtitle(self, self.objects, text, subtitle_zone_rect)`
- `run_step(self, self.objects, subtitle_text, subtitle_zone_rect, keep_ids, step_fn)`
- `cleanup_step(self, self.objects, keep_ids)`
- `cleanup_scene(self, self.objects, keep_ids)`

## 最小调用模板

推荐模式：

```python
def <scene_method_name>(self):
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

## Zone 与字幕流程的强约束

1. 所有 zone 都必须是数值四元组 `(x0, x1, y0, y1)`。
2. zone 不能是 `None`，不能是 mobject，也不能是 `self.camera.frame`。
3. 不要从 camera、frame 或其他运行时对象推导 zone；直接定义明确的 tuple。
4. 在第一次调用 `run_step(...)` 之前，必须先定义一个有效的字幕区，例如：
   `zone_subtitle = (0.05, 0.95, 0.02, 0.12)`。
5. 传给 `run_step(...)` 的第四个参数必须始终是有效 zone tuple。
6. 主内容区和字幕区职责不同，不要把内容对象当作字幕区传入。

## 推荐布局模板

```python
zone_main = (0.05, 0.95, 0.18, 0.88)
zone_subtitle = (0.05, 0.95, 0.02, 0.12)

def step_01():
    title = Text("当前标题", font_size=30, color=WHITE)
    place_in_zone(title, zone_main, offset=(0.0, 0.32))
    register_obj(self, self.objects, "title", title)
    self.add(title)

run_step(
    self,
    self.objects,
    "字幕文本",
    zone_subtitle,
    ["title"],
    step_01,
)
```

## 禁止写法

1. 不要重新定义 runtime helper。
2. 不要手写第二套字幕系统。
3. 不要手写逐对象清理循环去替代 `cleanup_step(...)` / `cleanup_scene(...)`。
4. 不要假设还存在额外的 framework 上下文。
5. 不要写 `zone_main = self.camera.frame` 或类似写法。
6. 不要在未定义有效 subtitle zone 的情况下调用 `run_step(...)`。
