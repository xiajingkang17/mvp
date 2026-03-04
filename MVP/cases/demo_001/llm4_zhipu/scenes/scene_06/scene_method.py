def scene_scene_06(self):
    reset_scene(self, self.objects)

    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    zone_main = (0.15, 0.85, 0.2, 0.9)

    def step_01():
        # Line 1: Relative Acceleration
        line1 = MathTex("a_{rel} = a_B - a_A = \\frac{17}{3} - 3.0 \\approx 2.67 \\, \\text{m/s}^2", font_size=36)
        # Line 2: Time Formula
        line2 = MathTex("l = \\frac{1}{2} a_{rel} t^2", font_size=36)
        # Line 3: Time Calculation
        line3 = MathTex("t = \\sqrt{\\frac{2l}{a_{rel}}} = \\sqrt{\\frac{0.8}{2.67}} \\approx 0.6 \\, \\text{s}", font_size=36)
        
        # Group and arrange
        calc_t_group = VGroup(line1, line2, line3).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        # Position in zone
        place_in_zone(calc_t_group, zone_main, offset=(0.0, 0.2))
        
        # Register and add
        register_obj(self, self.objects, "calc_t", calc_t_group)
        
        # Animate line by line
        self.play(Write(line1))
        self.play(Write(line2))
        self.play(Write(line3))

    run_step(
        self,
        self.objects,
        "相对加速度a_rel约为2.67。根据公式，t等于根号下2l除以a_rel，计算得出t等于0.6秒。",
        zone_subtitle,
        ["calc_t"],
        step_01,
    )

    def step_02():
        # Line 1: Velocity A
        line1 = MathTex("v_A = a_A t = 3.0 \\times 0.6 = 1.8 \\, \\text{m/s}", font_size=36)
        # Line 2: Velocity B
        line2 = MathTex("v_B = a_B t = \\frac{17}{3} \\times 0.6 \\approx 3.4 \\, \\text{m/s}", font_size=36)
        
        # Group and arrange
        calc_v_group = VGroup(line1, line2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        # Position below previous content
        calc_t = self.objects["calc_t"]
        calc_v_group.next_to(calc_t, DOWN, buff=0.6)
        
        # Register and add
        register_obj(self, self.objects, "calc_v", calc_v_group)
        
        # Animate line by line
        self.play(Write(line1))
        self.play(Write(line2))

    run_step(
        self,
        self.objects,
        "求出时间后，我们就可以算出滑落瞬间的速度了。v_A等于a_A乘以t，等于1.8米每秒，方向向右。v_B等于a_B乘以t，约为3.4米每秒，方向也向右。",
        zone_subtitle,
        ["calc_t", "calc_v"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
