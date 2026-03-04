def scene_scene_04(self):
    reset_scene(self, self.objects)

    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    zone_main = (0.15, 0.85, 0.2, 0.9)

    def step_01():
        # A的受力分析图
        diagram_A = VGroup()
        block_A = Rectangle(width=1.2, height=0.8, color=BLUE, stroke_width=4, fill_opacity=0.2)
        center_A = block_A.get_center()
        
        # 重力 mg
        g_arrow = Arrow(start=center_A, end=center_A + DOWN * 1.0, buff=0.1, color=WHITE)
        g_label = MathTex("mg", font_size=24).next_to(g_arrow, RIGHT, buff=0.05)
        
        # 支持力 N
        n_arrow = Arrow(start=center_A, end=center_A + UP * 1.0, buff=0.1, color=WHITE)
        n_label = MathTex("N", font_size=24).next_to(n_arrow, RIGHT, buff=0.05)
        
        # 摩擦力 f_k (向右)
        f_arrow = Arrow(start=center_A, end=center_A + RIGHT * 1.2, buff=0.1, color=YELLOW)
        f_label = MathTex("f_k", font_size=24).next_to(f_arrow, UP, buff=0.05)
        
        diagram_A.add(block_A, g_arrow, g_label, n_arrow, n_label, f_arrow, f_label)
        diagram_A.scale(0.8)
        place_in_zone(diagram_A, zone_main, offset=(-0.2, 0.3))
        register_obj(self, self.objects, "diagram_A", diagram_A)
        self.add(diagram_A)

        # 计算公式
        f_eq = MathTex("f_k = \\mu_k mg = 0.3 \\times 1.0 \\times 10 = 3.0 \\, \\text{N}", font_size=32, color=WHITE)
        a_eq = MathTex("a_A = \\frac{f_k}{m} = \\frac{3.0}{1.0} = 3.0 \\, \\text{m/s}^2", font_size=32, color=YELLOW)
        
        formulas = VGroup(f_eq, a_eq).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        place_in_zone(formulas, zone_main, offset=(0.1, 0.0))
        
        register_obj(self, self.objects, "calc_a_A", formulas)
        self.add(f_eq)
        self.play(Write(f_eq), run_time=1.0)
        self.play(Write(a_eq), run_time=1.0)

    run_step(
        self,
        self.objects,
        "先求A的加速度。隔离A，受向右的滑动摩擦力f_k。计算得a_A为3米每二次方秒。",
        zone_subtitle,
        ["diagram_A", "calc_a_A"],
        step_01,
    )

    def step_02():
        # B的受力分析图
        diagram_B = VGroup()
        block_B = Rectangle(width=1.2, height=0.8, color=GREEN, stroke_width=4, fill_opacity=0.2)
        center_B = block_B.get_center()
        
        # 重力 Mg
        g_arrow_B = Arrow(start=center_B, end=center_B + DOWN * 1.0, buff=0.1, color=WHITE)
        g_label_B = MathTex("Mg", font_size=24).next_to(g_arrow_B, RIGHT, buff=0.05)
        
        # 支持力 N'
        n_arrow_B = Arrow(start=center_B, end=center_B + UP * 1.0, buff=0.1, color=WHITE)
        n_label_B = MathTex("N'", font_size=24).next_to(n_arrow_B, RIGHT, buff=0.05)
        
        # 拉力 F (向右)
        F_arrow = Arrow(start=center_B, end=center_B + RIGHT * 1.5, buff=0.1, color=RED)
        F_label = MathTex("F", font_size=24).next_to(F_arrow, UP, buff=0.05)
        
        # 摩擦力 f_k' (向左)
        f_arrow_B = Arrow(start=center_B, end=center_B + LEFT * 1.2, buff=0.1, color=YELLOW)
        f_label_B = MathTex("f_k'", font_size=24).next_to(f_arrow_B, UP, buff=0.05)
        
        diagram_B.add(block_B, g_arrow_B, g_label_B, n_arrow_B, n_label_B, F_arrow, F_label, f_arrow_B, f_label_B)
        diagram_B.scale(0.8)
        place_in_zone(diagram_B, zone_main, offset=(-0.2, -0.3))
        register_obj(self, self.objects, "diagram_B", diagram_B)
        self.add(diagram_B)

        # 计算公式
        net_force_eq = MathTex("F_{\\text{net}} = F - f_k = 20.0 - 3.0 = 17.0 \\, \\text{N}", font_size=32, color=WHITE)
        a_eq_B = MathTex("a_B = \\frac{F_{\\text{net}}}{M} = \\frac{17.0}{3.0} \\approx 5.67 \\, \\text{m/s}^2", font_size=32, color=YELLOW)
        
        formulas_B = VGroup(net_force_eq, a_eq_B).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        place_in_zone(formulas_B, zone_main, offset=(0.1, -0.6))
        
        register_obj(self, self.objects, "calc_a_B", formulas_B)
        self.add(net_force_eq)
        self.play(Write(net_force_eq), run_time=1.0)
        self.play(Write(a_eq_B), run_time=1.0)

    run_step(
        self,
        self.objects,
        "再求B的加速度。隔离B，受向右的拉力F和向左的滑动摩擦力f_k。合力等于F减f_k，除以M，算得a_B约为5.67米每二次方秒。",
        zone_subtitle,
        ["diagram_A", "calc_a_A", "diagram_B", "calc_a_B"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
