def scene_scene_09(self):
    reset_scene(self, self.objects)

    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    zone_check = (0.05, 0.5, 0.2, 0.9)
    zone_summary = (0.55, 0.95, 0.2, 0.9)

    def step_01():
        # Energy verification formulas
        title_check = Text("能量守恒验证", font_size=32, color=WHITE)
        place_in_zone(title_check, zone_check, offset=(0.0, 0.35))
        register_obj(self, self.objects, "check_title", title_check)
        self.add(title_check)

        eq1 = MathTex("W_F = \\Delta E_k + Q", font_size=36, color=YELLOW)
        place_in_zone(eq1, zone_check, offset=(0.0, 0.15))
        register_obj(self, self.objects, "check_eq_1", eq1)
        self.add(eq1)

        eq2 = MathTex("\\Delta E_k = \\frac{1}{2}mv_A^2 + \\frac{1}{2}Mv_B^2", font_size=32)
        place_in_zone(eq2, zone_check, offset=(0.0, -0.05))
        register_obj(self, self.objects, "check_eq_2", eq2)
        self.add(eq2)

        eq3 = MathTex("\\Delta E_k \\approx 19.2 \\text{ J}", font_size=32)
        place_in_zone(eq3, zone_check, offset=(0.0, -0.20))
        register_obj(self, self.objects, "check_eq_3", eq3)
        self.add(eq3)

        eq4 = MathTex("Q = 1.2 \\text{ J}", font_size=32)
        place_in_zone(eq4, zone_check, offset=(0.0, -0.35))
        register_obj(self, self.objects, "check_eq_4", eq4)
        self.add(eq4)

        eq5 = MathTex("W_F = 19.2 + 1.2 = 20.4 \\text{ J} \\quad (\\text{一致})", font_size=32, color=GREEN)
        place_in_zone(eq5, zone_check, offset=(0.0, -0.50))
        register_obj(self, self.objects, "check_eq_5", eq5)
        self.add(eq5)

        # Group for cleanup reference
        check_group = VGroup(title_check, eq1, eq2, eq3, eq4, eq5)
        register_obj(self, self.objects, "check_eq", check_group)

    run_step(
        self,
        self.objects,
        "根据能量守恒，外力做功转化为系统动能和内能。我们计算动能增量，加上热量，确实等于外力做功。",
        zone_subtitle,
        ["check_eq"],
        step_01,
    )

    def step_02():
        # Summary table
        title_summary = Text("答案汇总", font_size=32, color=WHITE)
        place_in_zone(title_summary, zone_summary, offset=(0.0, 0.35))
        register_obj(self, self.objects, "summary_title", title_summary)
        self.add(title_summary)

        # Table content
        row1 = MathTex("(1) \\text{滑动状态: } a_A = 3.0 \\text{ m/s}^2, \\ a_B = \\frac{17}{3} \\text{ m/s}^2", font_size=28)
        row2 = MathTex("(2) \\text{滑落时间: } t = \\sqrt{0.3} \\text{ s} \\approx 0.55 \\text{ s}", font_size=28)
        row3 = MathTex("\\quad \\text{滑落速度: } v_A = 3\\sqrt{0.3} \\text{ m/s}, \\ v_B = \\frac{17}{3}\\sqrt{0.3} \\text{ m/s}", font_size=28)
        row4 = MathTex("(3) \\text{外力做功: } W_F = 20.4 \\text{ J}", font_size=28)
        row5 = MathTex("\\quad \\text{摩擦生热: } Q = 1.2 \\text{ J}", font_size=28)

        table_group = VGroup(row1, row2, row3, row4, row5)
        table_group.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        place_in_zone(table_group, zone_summary, offset=(0.0, -0.1))
        
        register_obj(self, self.objects, "summary_table", table_group)
        self.add(table_group)

    run_step(
        self,
        self.objects,
        "最后，我们汇总一下本题的所有答案。",
        zone_subtitle,
        ["check_eq", "summary_table"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
