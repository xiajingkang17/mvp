from manim import *

class GeneratedTeachScene(Scene):
    def construct(self):
        # problem_intake
        title = Text("双曲线离心率与直线交点问题", font_size=36, color=BLUE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)
        
        problem_text = VGroup(
            MathTex(r"C: \frac{x^2}{a^2} - \frac{y^2}{b^2} = 1", font_size=28),
            Text("F为右焦点，P在第一象限，M在左准线", font_size=24),
            MathTex(r"MP = OF, \ |PF| = \lambda|OF|", font_size=24, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        problem_text.next_to(title, DOWN, buff=0.5).to_edge(LEFT)
        
        self.play(FadeIn(problem_text, shift=DOWN))
        self.wait(1)
        
        # goal_lock
        goal1 = Text("(I) 求e与λ的关系", font_size=26, color=GREEN).next_to(problem_text, DOWN, buff=0.4).to_edge(LEFT)
        goal2 = Text("(II) 当λ=1时求双曲线方程", font_size=26, color=GREEN).next_to(goal1, DOWN, buff=0.2).align_to(goal1, LEFT)
        
        self.play(Write(goal1), Write(goal2))
        self.wait(1)
        self.play(FadeOut(problem_text), FadeOut(goal1), FadeOut(goal2))
        
        # model
        axes = Axes(
            x_range=[-4, 4, 1],
            y_range=[-3, 3, 1],
            x_length=5,
            y_length=4,
            axis_config={"include_tip": False, "stroke_width": 2}
        ).scale(0.8).shift(LEFT*3.2)
        
        hyperbola = axes.plot_implicit_curve(
            lambda x_val, y_val: x_val**2/4 - y_val**2/3 - 1,
            color=BLUE
        )
        
        O = Dot(axes.c2p(0, 0), color=WHITE)
        O_label = MathTex("O", font_size=28).next_to(O, DOWN, buff=0.15)
        
        F = Dot(axes.c2p(2.65, 0), color=RED)
        F_label = MathTex("F", font_size=28, color=RED).next_to(F, DOWN, buff=0.15)
        
        P = Dot(axes.c2p(2.3, 1.2), color=YELLOW)
        P_label = MathTex("P", font_size=28, color=YELLOW).next_to(P, UR, buff=0.15)
        
        left_directrix = DashedLine(axes.c2p(-1.5, -3), axes.c2p(-1.5, 3), color=GRAY)
        M = Dot(axes.c2p(-1.5, 1.2), color=GREEN)
        M_label = MathTex("M", font_size=28, color=GREEN).next_to(M, LEFT, buff=0.15)
        
        MP_line = Line(M.get_center(), P.get_center(), color=GREEN, stroke_width=2)
        OF_line = Line(O.get_center(), F.get_center(), color=RED, stroke_width=2)
        PF_line = Line(P.get_center(), F.get_center(), color=ORANGE, stroke_width=2)
        
        graph_group = VGroup(axes, hyperbola, O, O_label, F, F_label, P, P_label, 
                            left_directrix, M, M_label, MP_line, OF_line, PF_line)
        
        self.play(Create(axes), Create(hyperbola), run_time=1)
        self.wait(0.3)
        self.play(FadeIn(O), FadeIn(O_label), FadeIn(F), FadeIn(F_label), run_time=0.6)
        self.wait(0.3)
        self.play(Create(left_directrix), FadeIn(M), FadeIn(M_label), run_time=0.6)
        self.wait(0.3)
        self.play(FadeIn(P), FadeIn(P_label), run_time=0.5)
        self.wait(0.3)
        self.play(Create(MP_line), Create(OF_line), Create(PF_line), run_time=0.8)
        self.wait(0.8)
        
        # method_choice + derive
        step1 = MathTex(r"MP = OF", font_size=26).shift(RIGHT*3.2 + UP*2.4)
        step2 = MathTex(r"|PF| = \lambda c", font_size=26).next_to(step1, DOWN, buff=0.5)
        step3 = MathTex(r"\frac{|PF|}{|PN|} = e", font_size=26).next_to(step2, DOWN, buff=0.5)
        
        self.play(Write(step1), run_time=0.6)
        self.wait(0.4)
        self.play(Write(step2), run_time=0.6)
        self.wait(0.4)
        self.play(Write(step3), run_time=0.6)
        self.wait(0.6)
        
        N = Dot(axes.c2p(1.5, 1.2), color=PURPLE)
        N_label = MathTex("N", font_size=28, color=PURPLE).next_to(N, RIGHT, buff=0.15)
        PN_line = Line(P.get_center(), N.get_center(), color=PURPLE, stroke_width=2)
        
        self.play(FadeIn(N), FadeIn(N_label), Create(PN_line), run_time=0.7)
        self.wait(0.5)
        
        step4 = MathTex(r"|PN| = c - \frac{c}{e}", font_size=24).next_to(step3, DOWN, buff=0.5)
        step5 = MathTex(r"\lambda c = e(c - \frac{c}{e})", font_size=24).next_to(step4, DOWN, buff=0.5)
        step6 = MathTex(r"e = \lambda + 1", font_size=28, color=YELLOW).next_to(step5, DOWN, buff=0.6)
        
        self.play(Write(step4), run_time=0.6)
        self.wait(0.4)
        self.play(Write(step5), run_time=0.6)
        self.wait(0.4)
        self.play(Write(step6), run_time=0.7)
        self.wait(0.8)
        
        # recap part I
        result1_box = SurroundingRectangle(step6, color=YELLOW, buff=0.15)
        self.play(Create(result1_box))
        self.wait(0.8)
        
        self.play(FadeOut(graph_group), FadeOut(step1), FadeOut(step2), FadeOut(step3), 
                 FadeOut(step4), FadeOut(step5), FadeOut(result1_box), FadeOut(N), 
                 FadeOut(N_label), FadeOut(PN_line))
        
        conclusion1 = MathTex(r"e = \lambda + 1", font_size=40, color=YELLOW)
        self.play(TransformFromCopy(step6, conclusion1))
        self.wait(1.2)
        self.play(FadeOut(conclusion1), FadeOut(step6))
        
        # Part II
        part2_title = Text("(II) 当λ=1时", font_size=32, color=GREEN).to_edge(UP).shift(DOWN*0.5)
        self.play(Write(part2_title))
        
        cond1 = MathTex(r"e = 2, \ c = 2a, \ b^2 = 3a^2", font_size=26).next_to(part2_title, DOWN, buff=0.5)
        cond2 = MathTex(r"y = -a(x-1)", font_size=26).next_to(cond1, DOWN, buff=0.4)
        
        self.play(Write(cond1))
        self.wait(0.5)
        self.play(Write(cond2))
        self.wait(0.8)
        
        eq1 = MathTex(r"\frac{x^2}{a^2} - \frac{a^2(x-1)^2}{3a^2} = 1", font_size=24).next_to(cond2, DOWN, buff=0.5)
        eq2 = MathTex(r"3x^2 - a^2(x-1)^2 = 3a^2", font_size=24).next_to(eq1, DOWN, buff=0.4)
        
        self.play(Write(eq1))
        self.wait(0.5)
        self.play(Write(eq2))
        self.wait(0.8)
        
        vec_cond = MathTex(r"\vec{DA} = (\sqrt{3}-2)\vec{DB}", font_size=24, color=ORANGE).next_to(eq2, DOWN, buff=0.5)
        self.play(Write(vec_cond))
        self.wait(0.5)
        
        solve_step = MathTex(r"x_1 = (\sqrt{3}-2)x_2", font_size=24).next_to(vec_cond, DOWN, buff=0.4)
        self.play(Write(solve_step))
        self.wait(0.5)
        
        final_a = MathTex(r"a^2 = 3", font_size=28, color=YELLOW).next_to(solve_step, DOWN, buff=0.5)
        self.play(Write(final_a))
        self.wait(0.8)
        
        # recap
        self.play(FadeOut(part2_title), FadeOut(cond1), FadeOut(cond2), FadeOut(eq1), 
                 FadeOut(eq2), FadeOut(vec_cond), FadeOut(solve_step))
        
        final_box = SurroundingRectangle(final_a, color=YELLOW, buff=0.2)
        self.play(Create(final_box))
        self.wait(0.5)
        
        final_answer = MathTex(r"\frac{x^2}{3} - \frac{y^2}{9} = 1", font_size=40, color=GREEN)
        self.play(ReplacementTransform(VGroup(final_a, final_box), final_answer))
        self.wait(2)
