def scene_scene_06(self):
    reset_scene(self, self.objects)

    zone_main = (0.15, 0.85, 0.2, 0.85)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        # Step 1: Show relative acceleration and time derivation
        # Text content: "1. 计算相对加速度：\na_rel = a_B - a_A = 17/3 - 3 = 8/3 m/s²"
        # Text content: "2. 计算时间 t：\nl = 1/2 * a_rel * t²\n0.4 = 1/2 * (8/3) * t²\nt² = 0.3\nt = √0.3 ≈ 0.55 s"
        
        text_part1 = Text("1. 计算相对加速度：", font_size=32, color=WHITE)
        math_part1 = MathTex("a_{rel} = a_B - a_A = \\frac{17}{3} - 3 = \\frac{8}{3} \\, m/s^2", font_size=36, color=YELLOW)
        
        text_part2 = Text("2. 计算时间 t：", font_size=32, color=WHITE)
        math_part2 = MathTex("l = \\frac{1}{2} a_{rel} t^2", font_size=36, color=WHITE)
        math_part3 = MathTex("0.4 = \\frac{1}{2} \\cdot \\frac{8}{3} \\cdot t^2", font_size=36, color=WHITE)
        math_part4 = MathTex("t^2 = 0.3", font_size=36, color=WHITE)
        math_part5 = MathTex("t = \\sqrt{0.3} \\approx 0.55 \\, s", font_size=36, color=GREEN)

        # Group and arrange vertically
        group = VGroup(
            text_part1, math_part1,
            text_part2, math_part2, math_part3, math_part4, math_part5
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        
        place_in_zone(group, zone_main, offset=(0.0, 0.1))
        register_obj(self, self.objects, "derive_panel_q2", group)
        self.add(group)

    run_step(
        self,
        self.objects,
        "首先计算相对加速度，然后求出滑落时间t。",
        zone_subtitle,
        ["derive_panel_q2"],
        step_01,
    )

    def step_02():
        # Step 2: Update panel to show velocity calculations
        # Remove old content and create new full content including velocities
        old_group = self.objects.get("derive_panel_q2")
        if old_group:
            self.remove(old_group)

        # Text content: "1. 计算相对加速度：\na_rel = a_B - a_A = 17/3 - 3 = 8/3 m/s²"
        # Text content: "2. 计算时间 t：\nl = 1/2 * a_rel * t²\n0.4 = 1/2 * (8/3) * t²\nt² = 0.3\nt = √0.3 ≈ 0.55 s"
        # Text content: "3. 计算速度：\nv_A = a_A * t = 3 * √0.3 ≈ 1.65 m/s\nv_B = a_B * t = (17/3) * √0.3 ≈ 3.11 m/s"

        text_part1 = Text("1. 计算相对加速度：", font_size=28, color=WHITE)
        math_part1 = MathTex("a_{rel} = a_B - a_A = \\frac{17}{3} - 3 = \\frac{8}{3} \\, m/s^2", font_size=32, color=YELLOW)
        
        text_part2 = Text("2. 计算时间 t：", font_size=28, color=WHITE)
        math_part2 = MathTex("l = \\frac{1}{2} a_{rel} t^2", font_size=32, color=WHITE)
        math_part3 = MathTex("0.4 = \\frac{1}{2} \\cdot \\frac{8}{3} \\cdot t^2", font_size=32, color=WHITE)
        math_part4 = MathTex("t^2 = 0.3", font_size=32, color=WHITE)
        math_part5 = MathTex("t = \\sqrt{0.3} \\approx 0.55 \\, s", font_size=32, color=GREEN)

        text_part3 = Text("3. 计算速度：", font_size=28, color=WHITE)
        math_part6 = MathTex("v_A = a_A t = 3 \\sqrt{0.3} \\approx 1.65 \\, m/s", font_size=32, color=BLUE)
        math_part7 = MathTex("v_B = a_B t = \\frac{17}{3} \\sqrt{0.3} \\approx 3.11 \\, m/s", font_size=32, color=BLUE)

        # Group and arrange vertically
        group = VGroup(
            text_part1, math_part1,
            text_part2, math_part2, math_part3, math_part4, math_part5,
            text_part3, math_part6, math_part7
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        
        place_in_zone(group, zone_main, offset=(0.0, 0.15))
        register_obj(self, self.objects, "derive_panel_q2", group)
        self.add(group)

    run_step(
        self,
        self.objects,
        "最后，利用时间t计算滑落瞬间的速度v_A和v_B。",
        zone_subtitle,
        ["derive_panel_q2"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
