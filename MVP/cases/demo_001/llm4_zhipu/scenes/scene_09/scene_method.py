def scene_scene_09(self):
    reset_scene(self, self.objects)

    zone_left = (0.05, 0.45, 0.2, 0.9)
    zone_right = (0.55, 0.95, 0.2, 0.9)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        check_text = Text(
            "能量验证：\nW_F = ΔE_k + Q\nΔE_k = 1/2 m v_A² + 1/2 M v_B² ≈ 15.8 J\nQ = 1.2 J\nW_F ≈ 17.0 J (验证通过)",
            font_size=24,
            color=WHITE,
            line_spacing=0.4
        )
        fit_in_zone(check_text, zone_left, width_ratio=0.95, height_ratio=0.95)
        place_in_zone(check_text, zone_left, offset=(0.0, 0.0))
        register_obj(self, self.objects, "check_panel", check_text)
        self.add(check_text)

    run_step(
        self,
        self.objects,
        "我们利用能量守恒定律来验证计算结果是否正确。",
        zone_subtitle,
        ["check_panel"],
        step_01,
    )

    def step_02():
        summary_text = Text(
            "答案汇总：\n(1) a_A = 3.0 m/s², a_B ≈ 5.67 m/s²\n(2) t ≈ 0.55 s, v_A ≈ 1.65 m/s, v_B ≈ 3.11 m/s\n(3) W_F ≈ 17.0 J, Q = 1.2 J",
            font_size=24,
            color=WHITE,
            line_spacing=0.4
        )
        fit_in_zone(summary_text, zone_right, width_ratio=0.95, height_ratio=0.95)
        place_in_zone(summary_text, zone_right, offset=(0.0, 0.0))
        register_obj(self, self.objects, "summary_panel", summary_text)
        self.add(summary_text)

    run_step(
        self,
        self.objects,
        "验证通过后，我们汇总本题的所有答案。",
        zone_subtitle,
        ["check_panel", "summary_panel"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
