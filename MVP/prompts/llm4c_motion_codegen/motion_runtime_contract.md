# Motion Runtime Contract

`motion_codegen` 只负责“某个 step 要执行哪些动画”，不负责 scene 框架。

## 运行时事实

1. scene 方法已经创建好对象，并把可复用对象注册到 `self.objects`。
2. motion 方法只需要从 `self.objects` 里取对象，不要再次创建字幕、标题、公式、布局 helper 或 scene 边界逻辑。
3. motion 方法的返回值必须是“当前 step 需要执行的动画列表”。
4. 如果当前 `step_id` 没有运动，直接返回 `[]`。

## 禁止事项

1. 不要调用 `reset_scene(...)`、`cleanup_step(...)`、`cleanup_scene(...)`。
2. 不要调用 `show_subtitle(...)`。
3. 不要负责标题、公式、文字排版或对象注册框架。
4. 不要假设 `self.objects` 之外存在别的共享对象容器。

## 最小模式

推荐写法：

```python
def <motion_method_name>(self, step_id):
    if step_id == "step_02":
        particle = self.objects.get("particle")
        if particle is None:
            return []
        ...
        return [animation_a, animation_b]
    return []
```
