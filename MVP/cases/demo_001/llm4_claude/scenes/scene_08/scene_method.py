def scene_scene_08(self):
    reset_scene(self, self.objects)

    zone_formula_main = (0.1, 0.9, 0.16, 0.92)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        formula_xB = MathTex(
            r"x_B = \frac{1}{2} a_B t^2 = \frac{1}{2} \times \frac{17}{3} \times 0.3 \approx 0.85 \text{ m}",
            font_size=36,
            color=WHITE
        )
        formula_WF = MathTex(
            r"W_F = F \cdot x_B = 20 \times 0.85 = 17.0 \text{ J}",
            font_size=36,
            color=YELLOW
        )
        
        formulas = VGroup(formula_xB, formula_WF).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        place_in_zone(formulas, zone_formula_main, offset=(0.0, 0.1))
        
        register_obj(self, self.objects, "calc_xB", formula_xB)
        register_obj(self, self.objects, "calc_WF", formula_WF)
        
        self.play(Write(formula_xB), run_time=1.5)
        self.wait(0.5)
        self.play(Write(formula_WF), run_time=1.5)

    run_step(
        self,
        self.objects,
        "计算B的位移，得到x_B约为0.85米。进而算出W_F为17.0焦耳。",
        zone_subtitle,
        ["calc_xB", "calc_WF"],
        step_01
    )

    def step_02():
        formula_Q = MathTex(
            r"Q = f_k \cdot l = 3.0 \times 0.4 = 1.2 \text{ J}",
            font_size=36,
            color=GREEN
        )
        
        existing_formulas = VGroup(
            self.objects["calc_xB"],
            self.objects["calc_WF"]
        )
        all_formulas = VGroup(existing_formulas, formula_Q).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        place_in_zone(all_formulas, zone_formula_main, offset=(0.0, 0.1))
        
        register_obj(self, self.objects, "calc_Q", formula_Q)
        self.play(Write(formula_Q), run_time=1.5)

    run_step(
        self,
        self.objects,
        "最后算摩擦生热Q。f_k是3牛，相对位移l是0.4米，所以Q等于1.2焦耳。",
        zone_subtitle,
        ["calc_xB", "calc_WF", "calc_Q"],
        step_02
    )

    cleanup_scene(self, self.objects, [])
