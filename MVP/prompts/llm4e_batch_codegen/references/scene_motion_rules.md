# Scene 与 Motion 规则

## 分工

1. `scene_method` 负责静态对象、step 推进、字幕与布局
2. `motion_method` 负责返回当前 step 的动画列表

## motion 方法约定

1. 方法签名必须是 `def motion_scene_xx(self, step_id):`
2. 返回值必须是动画列表，例如 `return [anim1, anim2]`
3. 无运动时返回 `[]`
4. `step_id` 是主时间轴，运动应挂在具体 step 上

## scene 调用规则

1. 当前 step 需要运动时，先接收返回值：
   `anims = self.motion_scene_xx("step_02")`
2. 然后真正播放：
   `if anims: self.play(*anims)`
3. 禁止只写 `self.motion_scene_xx("step_02")` 而不播放
4. 不要把 motion 写成和 scene 脱节的平行流程
