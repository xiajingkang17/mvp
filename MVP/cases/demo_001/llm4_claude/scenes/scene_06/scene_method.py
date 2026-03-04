def scene_scene_06(self):
    reset_scene(self, self.objects)

    zone_formula_main = (0.1, 0.9, 0.16, 0.92)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        formula_1 = MathTex("a_{rel} = a_B - a_A \\approx 2.67 \\, \\text{m/s}^2", font_size=36)
        formula_2 = MathTex("t = \\sqrt{\\frac{2l}{a_{rel}}} = \\sqrt{\\frac{0.8}{2.67}} \\approx 0.6 \\, \\text{s}", font_size=36)
        
        calc_t = VGroup(formula_1, formula_2).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        place_in_zone(calc_t, zone_formula_main, offset=(0.0, 0.1))
        
        register_obj(self, self.objects, "calc_t", calc_t)
        self.play(Write(formula_1), run_time=1.5)
        self.wait(0.5)
        self.play(Write(formula_2), run_time=1.5)

    run_step(
        self,
        self.objects,
        "相对加速度a_rel约为2.67。根据公式，t等于根号下2l除以a_rel，计算得出t等于0.6秒。",
        zone_subtitle,
        ["calc_t"],
        step_01,
    )

    def step_02():
        formula_3 = MathTex("v_A = a_A t = 3.0 \\times 0.6 = 1.8 \\, \\text{m/s}", font_size=36)
        formula_4 = MathTex("v_B = a_B t \\approx 5.67 \\times 0.6 \\approx 3.4 \\, \\text{m/s}", font_size=36)
        
        calc_v = VGroup(formula_3, formula_4).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        
        calc_t_obj = self.objects["calc_t"]
        calc_v.next_to(calc_t_obj, DOWN, buff=0.6)
        
        register_obj(self, self.objects, "calc_v", calc_v)
        self.play(Write(formula_3), run_time=1.5)
        self.wait(0.5)
        self.play(Write(formula_4), run_time=1.5)

    run_step(
        self,
        self.objects,
        "求出时间后，我们就可以算出滑落瞬间的速度了。v_A等于a_A乘以t，等于1.8米每秒，方向向右。v_B等于a_B乘以t，约为3.4米每秒，方向也向右。",
        zone_subtitle,
        ["calc_t"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
