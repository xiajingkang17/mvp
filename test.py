from manim import *
import numpy as np

class TrackMotion(Scene):
    def construct(self):
        # -------------------------
        # 1) 轨道参数（可改）
        # -------------------------
        y_high = 1.8       # 第一段高处水平高度
        y_low  = -1.0      # 低处水平高度（半圆直径所在水平线）
        L1 = 4.2           # 高处水平长度
        L2 = 2.8           # 低处水平（半圆前）长度
        L3 = 3.2           # 半圆后水平长度
        R  = 1.3           # 半圆半径（向下半圆）
        x0 = -6.0          # 整体左移量

        # -------------------------
        # 2) 构造轨道关键点
        # -------------------------
        pA = np.array([x0,              y_high, 0.0])                 # 高水平起点
        pB = np.array([x0 + L1,         y_high, 0.0])                 # 高水平终点/斜面上端
        pC = np.array([x0 + L1 + 2.2,   y_low,  0.0])                 # 斜面下端/低水平起点
        pD = np.array([pC[0] + L2,      y_low,  0.0])                 # 低水平终点=半圆左端点
        pE = np.array([pD[0] + 2*R,     y_low,  0.0])                 # 半圆右端点=后水平起点
        pF = np.array([pE[0] + L3,      y_low,  0.0])                 # 最后水平终点

        # -------------------------
        # 3) 轨道分段（线 + 圆弧）
        # -------------------------
        seg1 = Line(pA, pB)                 # 高处水平
        seg2 = Line(pB, pC)                 # 斜面
        seg3 = Line(pC, pD)                 # 低处水平（半圆前）

        arc_center = np.array([pD[0] + R, y_low, 0.0])
        # 下半圆：从左端(PI)走到右端(2PI)，会经过最低点(3PI/2)
        seg4 = Arc(radius=R, start_angle=PI, angle=PI, arc_center=arc_center)

        seg5 = Line(pE, pF)                 # 半圆后水平

        track = VGroup(seg1, seg2, seg3, seg4, seg5).set_stroke(width=8)
        track.set_z_index(0)

        ground = Line([-7, y_low - 1.2, 0], [7, y_low - 1.2, 0]).set_stroke(width=2, opacity=0.3)
        ground.set_z_index(-1)

        self.add(ground, track)

        # -------------------------
        # 4) 用弧长参数 s 驱动整条轨道
        # -------------------------
        Ls = [
            seg1.get_length(),
            seg2.get_length(),
            seg3.get_length(),
            R * PI,                 # 半圆弧长
            seg5.get_length()
        ]
        total_len = sum(Ls)

        # 分段边界（累计长度）
        b1 = Ls[0]
        b2 = b1 + Ls[1]
        b3 = b2 + Ls[2]
        b4 = b3 + Ls[3]             # 弧段结束

        def point_from_s(s: float) -> np.ndarray:
            """沿轨道累计距离 s 对应的点坐标"""
            s = float(np.clip(s, 0.0, total_len))

            if s <= b1:
                a = s / Ls[0]
                return interpolate(pA, pB, a)

            if s <= b2:
                s2 = s - b1
                a = s2 / Ls[1]
                return interpolate(pB, pC, a)

            if s <= b3:
                s3 = s - b2
                a = s3 / Ls[2]
                return interpolate(pC, pD, a)

            if s <= b4:
                s4 = s - b3
                a = s4 / Ls[3]      # 0..1
                theta = PI + a * PI
                return arc_center + R * np.array([np.cos(theta), np.sin(theta), 0.0])

            s5 = s - b4
            a = s5 / Ls[4] if Ls[4] > 1e-9 else 1.0
            return interpolate(pE, pF, np.clip(a, 0.0, 1.0))

        def tangent_from_s(s: float) -> np.ndarray:
            """数值差分估计切向方向"""
            s = float(np.clip(s, 0.0, total_len))
            p1 = point_from_s(s)
            p2 = point_from_s(min(s + 0.03, total_len))
            v = p2 - p1
            n = np.linalg.norm(v)
            return v / n if n > 1e-9 else RIGHT

        def normal_from_s(s: float) -> np.ndarray:
            """
            支撑法向（滑块应该位于轨道的哪一侧）
            - 圆弧：取指向圆心（滑块在“碗里”贴弧面）
            - 线段：取切向旋转 90° 后更“向上”的那一侧
            """
            s = float(np.clip(s, 0.0, total_len))
            pos = point_from_s(s)

            # 圆弧段：径向（指向圆心）
            if b3 <= s <= b4:
                v = arc_center - pos
                n = np.linalg.norm(v)
                return v / n if n > 1e-9 else UP

            # 线段：切向旋转得到法向，取 y 更大的（更像“轨道上方”）
            tan = tangent_from_s(s)
            n1 = rotate_vector(tan, PI / 2)
            n2 = -n1
            pick = n1 if n1[1] >= n2[1] else n2
            return pick / np.linalg.norm(pick)

        # -------------------------
        # 5) 滑块：投影贴合（不会穿模）
        # -------------------------
        s_tracker = ValueTracker(0.0)

        block = RoundedRectangle(width=0.7, height=0.45, corner_radius=0.12)
        # 用灰色便于肉眼确认贴合（确认后你可以改回白色）
        block.set_fill(GREY_B, opacity=1.0).set_stroke(WHITE, width=2)
        block.set_z_index(10)

        block._theta = 0.0     # 手动记录当前角度（避免 get_angle 报错）
        gap = 0.02             # 与轨道线留一点点缝，视觉更干净

        def place_block_on_track(mob: Mobject, s: float):
            pos = point_from_s(s)
            tan = tangent_from_s(s)
            nor = normal_from_s(s)

            # (1) 旋到切线方向：增量旋转 + 手动记角度
            target_theta = angle_of_vector(tan)
            mob.rotate(target_theta - mob._theta)
            mob._theta = target_theta

            # (2) 临时把中心放到轨道点
            mob.move_to(pos)

            # (3) 投影找出：滑块在 -nor 方向上最“靠轨道”的极值距离 d
            pts = mob.get_all_points()
            c = mob.get_center()
            d = 0.0
            for p in pts:
                d = max(d, float(np.dot(p - c, -nor)))

            # (4) 抬起中心：让“最靠轨道的点”正好落在轨道点上（+gap）
            mob.move_to(pos + nor * (d + gap))

        def update_block(mob: Mobject):
            place_block_on_track(mob, s_tracker.get_value())

        block.add_updater(update_block)

        # 速度箭头（切向）
        vel_arrow = always_redraw(lambda: Arrow(
            start=block.get_center(),
            end=block.get_center() + 0.9 * tangent_from_s(s_tracker.get_value()),
            buff=0,
            max_tip_length_to_length_ratio=0.25
        ).set_stroke(width=6).set_z_index(11))

        vel_label = always_redraw(lambda: MathTex("v").scale(0.6).next_to(
            vel_arrow.get_end(), UP, buff=0.1
        ).set_z_index(11))

        self.add(block, vel_arrow, vel_label)

        # -------------------------
        # 6) 动画：匀速走完整条轨道（演示用）
        # -------------------------
        self.wait(0.2)
        self.play(s_tracker.animate.set_value(total_len), run_time=10, rate_func=linear)
        self.wait(0.8)
