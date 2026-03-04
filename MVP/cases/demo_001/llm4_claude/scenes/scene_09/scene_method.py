def scene_scene_09(self):
    reset_scene(self, self.objects)

    zone_check_left = (0.05, 0.48, 0.16, 0.92)
    zone_summary_right = (0.52, 0.95, 0.16, 0.92)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        eq1 = MathTex(r"W_F = \Delta E_k + Q", font_size=36, color=WHITE)
        eq2 = MathTex(r"\Delta E_k = \frac{1}{2}m v_A^2 + \frac{1}{2}M v_B^2 \approx 19.2\,\text{J}", font_size=32, color=YELLOW)
        eq3 = MathTex(r"Q = 1.2\,\text{J}", font_size=32, color=YELLOW)
        eq4 = MathTex(r"W_F = 19.2 + 1.2 = 20.4\,\text{J}", font_size=32, color=GREEN)
        
        check_group = VGroup(eq1, eq2, eq3, eq4).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit_in_zone(check_group, zone_check_left, width_ratio=0.9, height_ratio=0.85)
        
        register_obj(self, self.objects, "check_eq1", eq1)
        register_obj(self, self.objects, "check_eq2", eq2)
        register_obj(self, self.objects, "check_eq3", eq3)
        register_obj(self, self.objects, "check_eq4", eq4)
        
        self.play(Write(eq1))
        self.wait(0.5)
        self.play(Write(eq2))
        self.wait(0.5)
        self.play(Write(eq3))
        self.wait(0.5)
        self.play(Write(eq4))

    run_step(
        self,
        self.objects,
        "根据能量守恒,外力做功转化为系统动能和内能。我们计算动能增量,加上热量,确实等于外力做功。",
        zone_subtitle,
        ["check_eq1", "check_eq2", "check_eq3", "check_eq4"],
        step_01
    )

    def step_02():
        summary_lines = [
            "答案汇总:",
            "(1) 一开始就滑动",
            "    a_A = 3.0 m/s²",
            "    a_B ≈ 5.67 m/s²",
            "(2) t ≈ 0.55 s",
            "    v_A ≈ 1.64 m/s",
            "    v_B ≈ 3.10 m/s",
            "(3) W_F = 20.4 J",
            "    Q = 1.2 J"
        ]
        summary_text = "\n".join(summary_lines)
        summary_block = make_wrapped_text_block(
            summary_text,
            zone_summary_right,
            font_size=28,
            color=WHITE,
            anchor="top_left"
        )
        
        register_obj(self, self.objects, "summary_table", summary_block)
        self.play(FadeIn(summary_block))

    run_step(
        self,
        self.objects,
        "最后,我们汇总一下本题的所有答案。",
        zone_subtitle,
        ["check_eq1", "check_eq2", "check_eq3", "check_eq4", "summary_table"],
        step_02
    )

    cleanup_scene(self, self.objects, [])
