def scene_scene_04(self):
    reset_scene(self, self.objects)

    zone_main = (0.15, 0.85, 0.25, 0.85)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        title = Text("计算加速度", font_size=36, color=WHITE)
        place_in_zone(title, zone_main, offset=(0.0, 0.35))
        register_obj(self, self.objects, "title", title)
        self.add(title)

        eq_A_text = "对A: f_k = ma_A"
        eq_A_sub = "\\mu_k mg = ma_A"
        eq_A_res = "a_A = \\mu_k g = 0.3 \\times 10 = 3.0 \\, m/s^2 \\, (向右)"
        
        eq_A = VGroup(
            MathTex(eq_A_text, font_size=32, color=WHITE),
            MathTex(eq_A_sub, font_size=32, color=WHITE),
            MathTex(eq_A_res, font_size=32, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        
        place_in_zone(eq_A, zone_main, offset=(0.0, 0.05))
        register_obj(self, self.objects, "calc_panel", eq_A)
        self.add(eq_A)

    run_step(
        self,
        self.objects,
        "首先计算物块A的加速度。",
        zone_subtitle,
        ["title", "calc_panel"],
        step_01,
    )

    def step_02():
        eq_B_text = "对B: F - f_k = Ma_B"
        eq_B_sub = "20 - 0.3 \\times 1 \\times 10 = 3 \\times a_B"
        eq_B_res = "a_B = 17/3 \\approx 5.67 \\, m/s^2 \\, (向右)"
        
        eq_B = VGroup(
            MathTex(eq_B_text, font_size=32, color=WHITE),
            MathTex(eq_B_sub, font_size=32, color=WHITE),
            MathTex(eq_B_res, font_size=32, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        
        place_in_zone(eq_B, zone_main, offset=(0.0, -0.35))
        register_obj(self, self.objects, "calc_panel", eq_B)
        self.add(eq_B)

    run_step(
        self,
        self.objects,
        "接着计算木板B的加速度。",
        zone_subtitle,
        ["title", "calc_panel"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
