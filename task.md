要稳定得到你现在 test.py 里那种效果（斜面/平面/弧面连续连接，滑块沿轨迹走），需要同时改“底层几何约束”和“LLM 自动生成规则”。只改 JSON 一处不够。

P0 必做（核心稳定性）

语义锚点必须进入求解器（已做）

anchors.py (line 24)
现在会读取组件 list_anchors/get_anchor（start/end 不再退化成 center），这是之前“交于一点”的主因修复。
align_angle 按真实轴向对齐（已做）

align_angle.py (line 21)
解决 Wall(angle=30) 这类“组件内部已旋转但 pose.theta=0”导致的错对齐。
直线轨迹支持锚点动态绑定（已做）

on_track_pose.py (line 93)
line/segment 轨迹现在可用 part_id + anchor_a/anchor_b，滑块贴轨不会和零件脱节。
场景里弧段必须用弧形零件（已做）

scene_plan.json (line 59)
p_arc 必须是 ArcTrack，不能是 Rod。
你要的视频演示代码（已做）

test.py (line 24) (CompositeAnchorConstraintSlide)
这是“锚点 + 约束 + on_track_pose”完整跑通版本。
P1 必做（自动生成不再回退）

修 LLM 模板错误约束写法

static_incline_flat_arc.json (line 24)
这个模板里 align_angle 还在用 part_a/part_b，应改成 part_id + (angle|ref_part_id)。
加强计划校验器（防止脏 JSON 进渲染）

validate_plan.py (line 229)
增加规则：
ArcTrack/SemicircleGroove 场景禁止用 Rod 充当弧段。
attach/on_track_pose 的锚点名必须在该组件锚点字典里。
align_angle 参数必须满足白名单（缺 part_id 直接报错）。
协议文档补一条“渲染事实”

drawing_protocol.md (line 34)
明确“画面由 parts 决定，tracks 主要用于接触/运动”。
P2 验收与回归

单元测试
新增 render/composite/solver/test：验证 start/end 锚点确实生效。
集成测试
用 cases/demo_001 跑一次，断言无 unsatisfied_hard。
视觉验收
运行 python -m manim -pql test.py CompositeAnchorConstraintSlide，检查 4 个连接点连续、滑块全程贴轨。
执行顺序

先合并 P0（你现在已有）。
立刻做 P1（这是你“有时好、有时崩”的根因）。
最后上 P2，锁住回归。
