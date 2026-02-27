from manim import *
import math

class EMFieldLayersProblem(MovingCameraScene):
    def construct(self):
        # ----------------------------
        # Style / Color coding (consistent)
        # ----------------------------
        C_PART = RED
        C_E = BLUE_B
        C_B1 = PURPLE_B
        C_B2 = ORANGE
        C_D = YELLOW
        C_V = GREEN

        # ----------------------------
        # Geometric scale
        # ----------------------------
        d = 1.2  # visual unit for distance d
        sqrt2 = math.sqrt(2)

        y_L2 = 0.0
        y_L1 = d
        y_L3 = -d
        y_L4 = -2 * d

        # left diagram anchor (shift left so we have a right panel)
        diagram_shift = LEFT * 3.2

        # ----------------------------
        # Helper: build field diagram
        # ----------------------------
        x_span = 5.2
        def boundary(y, label_tex):
            line = DashedLine(
                start=LEFT * x_span + UP * y,
                end=RIGHT * x_span + UP * y,
                dash_length=0.18
            )
            label = MathTex(label_tex).scale(0.6).next_to(line, RIGHT, buff=0.25)
            return VGroup(line, label)

        L1 = boundary(y_L1, r"L_1")
        L2 = boundary(y_L2, r"L_2")
        L3 = boundary(y_L3, r"L_3")
        L4 = boundary(y_L4, r"L_4")

        boundaries = VGroup(L1, L2, L3, L4).shift(diagram_shift)

        # Distance markers d on the left
        def d_brace(y_top, y_bot):
            p1 = LEFT * x_span + UP * y_top
            p2 = LEFT * x_span + UP * y_bot
            br = BraceBetweenPoints(p1, p2, direction=LEFT, buff=0.15)
            lab = MathTex("d").set_color(C_D).scale(0.6).next_to(br, LEFT, buff=0.15)
            return VGroup(br, lab)

        braces = VGroup(
            d_brace(y_L1, y_L2),
            d_brace(y_L2, y_L3),
            d_brace(y_L3, y_L4),
        ).shift(diagram_shift)

        # E-field arrows between L1 and L2 (downward)
        E_arrows = VGroup()
        for i in range(7):
            x = -3.8 + i * 1.15
            arr = Arrow(
                start=np.array([x, y_L1 - 0.15, 0]),
                end=np.array([x, y_L2 + 0.15, 0]),
                buff=0,
                stroke_width=4,
                max_tip_length_to_length_ratio=0.18
            ).set_color(C_E)
            E_arrows.add(arr)
        E_label = MathTex("E").set_color(C_E).scale(0.7).next_to(E_arrows, RIGHT, buff=0.2)
        E_group = VGroup(E_arrows, E_label).shift(diagram_shift)

        # B1 crosses between L2 and L3
        B1_marks = VGroup()
        for row_y in [y_L2 - 0.35, y_L2 - 0.75]:
            for i in range(9):
                x = -4.0 + i * 1.0
                mk = MathTex(r"\times").set_color(C_B1).scale(0.5).move_to([x, row_y, 0])
                B1_marks.add(mk)
        B1_label = MathTex("B_1").set_color(C_B1).scale(0.7).next_to(B1_marks, RIGHT, buff=0.2)
        B1_group = VGroup(B1_marks, B1_label).shift(diagram_shift)

        # B2 dots between L3 and L4
        B2_marks = VGroup()
        for row_y in [y_L3 - 0.35, y_L3 - 0.75]:
            for i in range(9):
                x = -4.0 + i * 1.0
                mk = Dot(point=[x, row_y, 0], radius=0.06, color=C_B2)
                B2_marks.add(mk)
        B2_label = MathTex("B_2").set_color(C_B2).scale(0.7).next_to(B2_marks, RIGHT, buff=0.2)
        B2_group = VGroup(B2_marks, B2_label).shift(diagram_shift)

        diagram = VGroup(boundaries, braces, E_group, B1_group, B2_group)

        # ----------------------------
        # Points P, Q on L1 with distance 2sqrt(2)d
        # ----------------------------
        P_x = -2.6  # choose visually nice
        PQ = 2 * sqrt2 * d
        Q_x = P_x + PQ

        P_dot = Dot(point=[P_x, y_L1, 0], radius=0.07, color=WHITE).shift(diagram_shift)
        Q_dot = Dot(point=[Q_x, y_L1, 0], radius=0.07, color=WHITE).shift(diagram_shift)
        P_lab = MathTex("P").scale(0.7).next_to(P_dot, UP, buff=0.12)
        Q_lab = MathTex("Q").scale(0.7).next_to(Q_dot, UP, buff=0.12)

        brace_PQ = BraceBetweenPoints(P_dot.get_center(), Q_dot.get_center(), direction=UP, buff=0.18)
        label_PQ = MathTex(r"2\sqrt{2}d").set_color(C_D).scale(0.65).next_to(brace_PQ, UP, buff=0.12)
        PQ_group = VGroup(P_dot, Q_dot, P_lab, Q_lab, brace_PQ, label_PQ)

        # ----------------------------
        # Right-side derivation panel (Text for Chinese)
        # ----------------------------
        panel_bg = RoundedRectangle(corner_radius=0.2, width=6.4, height=6.8)
        panel_bg.set_fill(color=GREY_E, opacity=0.55)
        panel_bg.set_stroke(color=GREY_B, width=2)
        panel_bg.to_edge(RIGHT, buff=0.4)

        panel_anchor = panel_bg.get_top_left() + RIGHT * 0.35 + DOWN * 0.35

        def panel_title(s):
            t = Text(s, font_size=30, color=WHITE)
            t.move_to(panel_anchor).align_to(panel_bg, LEFT).shift(DOWN * 0.1)
            t.align_to(panel_bg, LEFT)
            t.to_corner(UR, buff=0.75).shift(LEFT * 0.2)  # keep inside
            return t

        # We'll place formulas manually under the title
        def place_under(obj, ref, dy=0.55):
            obj.next_to(ref, DOWN, aligned_edge=LEFT, buff=0.35)
            obj.shift(DOWN * (dy - 0.55))
            return obj

        # ----------------------------
        # Camera initial framing
        # ----------------------------
        self.camera.frame.save_state()

        # ----------------------------
        # 0s–6s: Establish diagram
        # ----------------------------
        title = Text("带电粒子在分层电磁场中的运动", font_size=36, color=WHITE).to_edge(UP, buff=0.35)
        self.play(FadeIn(title, shift=DOWN*0.2), run_time=1.0)

        self.play(Create(diagram), run_time=2.2)
        self.play(FadeIn(PQ_group), run_time=1.0)

        # Slight camera settle
        self.play(self.camera.frame.animate.scale(0.98).shift(LEFT*0.1), run_time=0.8)

        # ----------------------------
        # 6s–16s: (1) v0
        # ----------------------------
        self.play(FadeIn(panel_bg), run_time=0.6)

        t1 = Text("（1）进入磁场 B1 的速度 v0", font_size=28, color=WHITE)
        t1.move_to(panel_bg.get_top_left() + RIGHT * 0.35 + DOWN * 0.35).align_to(panel_bg, LEFT)
        self.play(Write(t1), run_time=0.9)

        # Highlight E region
        E_highlight = Rectangle(width=10.6, height=d, stroke_width=0)
        E_highlight.set_fill(C_E, opacity=0.12)
        E_highlight.move_to(diagram_shift + UP * ((y_L1 + y_L2) / 2))
        self.play(FadeIn(E_highlight), run_time=0.6)

        self.play(self.camera.frame.animate.scale(0.92).move_to(panel_bg), run_time=0.9)

        eq1 = MathTex(
            r"qEd=\frac{1}{2}mv_0^2",
            tex_to_color_map={r"E": C_E, r"d": C_D, r"v_0": C_V}
        ).scale(0.72)
        eq1.next_to(t1, DOWN, aligned_edge=LEFT, buff=0.35).align_to(panel_bg, LEFT).shift(RIGHT*0.35)

        eq2 = MathTex(
            r"v_0=\sqrt{\frac{2qEd}{m}}",
            tex_to_color_map={r"E": C_E, r"d": C_D, r"v_0": C_V}
        ).scale(0.72)
        eq2.next_to(eq1, DOWN, aligned_edge=LEFT, buff=0.25)

        self.play(Write(eq1), run_time=1.2)
        self.play(Write(eq2), run_time=1.2)

        self.play(FadeOut(E_highlight), run_time=0.5)
        self.play(Restore(self.camera.frame), run_time=0.9)

        # ----------------------------
        # 16s–33s: (2) return to P -> B2
        # ----------------------------
        t2 = Text("（2）恰好回到 P 点：求 B2", font_size=28, color=WHITE)
        t2.move_to(t1).align_to(t1, LEFT)
        self.play(Transform(t1, t2), FadeOut(eq1), FadeOut(eq2), run_time=0.9)

        self.play(self.camera.frame.animate.scale(0.92).move_to(panel_bg), run_time=0.9)

        eqB1 = MathTex(
            r"B_1=\sqrt{\frac{mE}{qd}}",
            tex_to_color_map={r"B_1": C_B1, r"E": C_E, r"d": C_D}
        ).scale(0.72)
        eqB1.next_to(t1, DOWN, aligned_edge=LEFT, buff=0.35).align_to(panel_bg, LEFT).shift(RIGHT*0.35)

        eqr1 = MathTex(
            r"r_1=\frac{mv_0}{qB_1}=\sqrt{2}\,d",
            tex_to_color_map={r"r_1": C_D, r"v_0": C_V, r"B_1": C_B1, r"d": C_D}
        ).scale(0.72)
        eqr1.next_to(eqB1, DOWN, aligned_edge=LEFT, buff=0.25)

        self.play(Write(eqB1), run_time=1.1)
        self.play(Write(eqr1), run_time=1.2)

        # back to diagram and draw the "return" path
        self.play(Restore(self.camera.frame), run_time=0.9)

        # Key points on L2, L3 for one cycle (return-to-P case)
        A = np.array([P_x, y_L2, 0]) + diagram_shift  # enter B1 at L2 below P
        r1 = sqrt2 * d
        xB = d * (sqrt2 - 1)
        B = np.array([P_x + xB, y_L3, 0]) + diagram_shift  # after B1 down 45°

        r2_return = d * (2 - sqrt2)
        C = np.array([ (P_x + xB) - sqrt2 * r2_return, y_L3, 0]) + diagram_shift

        # Centers
        center_b1_down = A + RIGHT * r1
        center_b2 = B + (LEFT + DOWN) * (r2_return / sqrt2)  # down-left from B
        center_b1_up = C + (LEFT + UP) * (d)  # because r1/sqrt2 = d

        arc_b1_down = Arc(radius=r1, start_angle=PI, angle=PI/4).set_color(C_B1)
        arc_b1_down.move_arc_center_to(center_b1_down)

        arc_b2 = Arc(radius=r2_return, start_angle=PI/4, angle=-3*PI/2).set_color(C_B2)
        arc_b2.move_arc_center_to(center_b2)

        arc_b1_up = Arc(radius=r1, start_angle=-PI/4, angle=PI/4).set_color(C_B1)
        arc_b1_up.move_arc_center_to(center_b1_up)

        path_group_return = VGroup(arc_b1_down, arc_b2, arc_b1_up)

        # Small angle labels (optional, keep light)
        theta1 = MathTex(r"\Delta\theta_1=\frac{\pi}{4}").scale(0.55).set_color(C_B1)
        theta1.next_to(arc_b1_down, UP, buff=0.1)
        theta2 = MathTex(r"\Delta\theta_2=\frac{3\pi}{2}").scale(0.55).set_color(C_B2)
        theta2.next_to(arc_b2, DOWN, buff=0.1)

        self.play(Create(path_group_return), FadeIn(theta1), FadeIn(theta2), run_time=1.6)

        particle = Dot(color=C_PART, radius=0.08).move_to(A)

        self.play(FadeIn(particle), run_time=0.3)
        self.play(MoveAlongPath(particle, arc_b1_down), run_time=1.3, rate_func=linear)
        self.play(MoveAlongPath(particle, arc_b2), run_time=1.3, rate_func=linear)
        self.play(MoveAlongPath(particle, arc_b1_up), run_time=0.9, rate_func=linear)

        # show the B2 result
        self.play(self.camera.frame.animate.scale(0.92).move_to(panel_bg), run_time=0.9)
        eqr2 = MathTex(
            r"r_2=d(2-\sqrt2)",
            tex_to_color_map={r"r_2": C_D, r"d": C_D}
        ).scale(0.72)
        eqr2.next_to(eqr1, DOWN, aligned_edge=LEFT, buff=0.3)

        eqB2 = MathTex(
            r"B_2=(1+\sqrt2)B_1=(1+\sqrt2)\sqrt{\frac{mE}{qd}}",
            tex_to_color_map={r"B_2": C_B2, r"B_1": C_B1, r"E": C_E, r"d": C_D}
        ).scale(0.66)
        eqB2.next_to(eqr2, DOWN, aligned_edge=LEFT, buff=0.25)

        self.play(Write(eqr2), run_time=1.0)
        self.play(Write(eqB2), run_time=1.2)

        self.play(Restore(self.camera.frame), run_time=0.9)

        # Clean some visuals before part (3)
        self.play(FadeOut(theta1), FadeOut(theta2), FadeOut(particle), run_time=0.6)

        # ----------------------------
        # 33s–58s: (3) shortest time to reach Q -> t0
        # ----------------------------
        t3 = Text("（3）最短时间到达 Q：求 t0", font_size=28, color=WHITE)
        self.play(Transform(t1, t3), run_time=0.8)

        # Move camera to panel
        self.play(self.camera.frame.animate.scale(0.92).move_to(panel_bg), run_time=0.9)

        # Replace equations area: fade old (2) detail except keep B1, r1 visible lightly
        self.play(FadeOut(eqr2), FadeOut(eqB2), run_time=0.6)

        # drift per cycle
        eq_dx = MathTex(
            r"\Delta x=2(\sqrt2-1)d-\sqrt2\,r_2",
            tex_to_color_map={r"\Delta x": C_D, r"d": C_D, r"r_2": C_D}
        ).scale(0.70)
        eq_dx.next_to(eqr1, DOWN, aligned_edge=LEFT, buff=0.30)

        eq_need4 = MathTex(
            r"\Delta x_{\max}=2(\sqrt2-1)d<\frac{2\sqrt2}{3}d\ \Rightarrow\ N_{\min}=4",
            tex_to_color_map={r"\Delta x_{\max}": C_D, r"d": C_D}
        ).scale(0.60)
        eq_need4.next_to(eq_dx, DOWN, aligned_edge=LEFT, buff=0.25)

        eq_set = MathTex(
            r"\Delta x=\frac{2\sqrt2 d}{4}=\frac{d}{\sqrt2}\Rightarrow r_2=d\Big(\frac{3}{2}-\sqrt2\Big)",
            tex_to_color_map={r"\Delta x": C_D, r"d": C_D, r"r_2": C_D}
        ).scale(0.56)
        eq_set.next_to(eq_need4, DOWN, aligned_edge=LEFT, buff=0.25)

        eq_B2opt = MathTex(
            r"B_2=\frac{mv_0}{qr_2}=(8+6\sqrt2)B_1",
            tex_to_color_map={r"B_2": C_B2, r"v_0": C_V, r"r_2": C_D, r"B_1": C_B1}
        ).scale(0.62)
        eq_B2opt.next_to(eq_set, DOWN, aligned_edge=LEFT, buff=0.25)

        eq_t0 = MathTex(
            r"t_0=\sqrt{\frac{md}{qE}}\Big(8\sqrt2-4\pi+\frac{9\pi}{\sqrt2}\Big)",
            tex_to_color_map={r"t_0": WHITE, r"E": C_E, r"d": C_D}
        ).scale(0.62)
        eq_t0.next_to(eq_B2opt, DOWN, aligned_edge=LEFT, buff=0.25)

        self.play(Write(eq_dx), run_time=1.0)
        self.play(Write(eq_need4), run_time=1.1)
        self.play(Write(eq_set), run_time=1.2)
        self.play(Write(eq_B2opt), run_time=1.0)
        self.play(Write(eq_t0), run_time=1.2)

        # Show landing points sequence on L1: P0..P4=Q
        self.play(Restore(self.camera.frame), run_time=0.9)

        dx_per_cycle = PQ / 4  # = d/sqrt2 * 4? actually PQ/4
        pts = VGroup()
        labels = VGroup()
        for k in range(5):
            xk = P_x + k * dx_per_cycle
            dotk = Dot(point=[xk, y_L1, 0], radius=0.06, color=WHITE).shift(diagram_shift)
            labk = MathTex(f"P_{k}").scale(0.5).next_to(dotk, UP, buff=0.1)
            pts.add(dotk); labels.add(labk)

        # Replace last label with Q
        labels[-1].become(MathTex("Q").scale(0.65).next_to(pts[-1], UP, buff=0.12))
        labels[-1].set_color(WHITE)

        arrow_seq = Arrow(pts[0].get_center() + DOWN*0.25, pts[-1].get_center() + DOWN*0.25, buff=0.1)
        arrow_seq.set_color(C_D)
        seq_label = MathTex(r"4\times \Delta x=2\sqrt2 d").set_color(C_D).scale(0.6).next_to(arrow_seq, DOWN, buff=0.12)

        self.play(FadeIn(pts), FadeIn(labels), run_time=1.0)
        self.play(GrowArrow(arrow_seq), FadeIn(seq_label), run_time=1.0)

        # Final summary card
        summary_bg = RoundedRectangle(corner_radius=0.2, width=12.5, height=2.2)
        summary_bg.set_fill(color=BLACK, opacity=0.6)
        summary_bg.set_stroke(color=GREY_B, width=2)
        summary_bg.to_edge(DOWN, buff=0.35)

        s1 = MathTex(r"v_0=\sqrt{\frac{2qEd}{m}}", tex_to_color_map={r"E": C_E, r"d": C_D, r"v_0": C_V}).scale(0.65)
        s2 = MathTex(r"B_2=(1+\sqrt2)\sqrt{\frac{mE}{qd}}", tex_to_color_map={r"B_2": C_B2, r"E": C_E, r"d": C_D}).scale(0.60)
        s3 = MathTex(r"t_0=\sqrt{\frac{md}{qE}}\Big(8\sqrt2-4\pi+\frac{9\pi}{\sqrt2}\Big)",
                     tex_to_color_map={r"E": C_E, r"d": C_D}).scale(0.54)

        summary = VGroup(s1, s2, s3).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        summary.move_to(summary_bg.get_center()).shift(LEFT*4.8)

        self.play(FadeIn(summary_bg), Write(summary), run_time=1.5)
        self.wait(1.2)