def scene_scene_04(self):
    reset_scene(self, self.objects)
    
    zone_formula_main = (0.1, 0.9, 0.16, 0.92)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    
    def step_01():
        formula_A_1 = MathTex("f_k = \\mu_k m g = 0.3 \\times 1.0 \\times 10 = 3.0\\,\\text{N}", font_size=36, color=WHITE)
        formula_A_2 = MathTex("a_A = \\frac{f_k}{m} = \\frac{3.0}{1.0} = 3.0\\,\\text{m/s}^2", font_size=36, color=YELLOW)
        
        formulas_A = VGroup(formula_A_1, formula_A_2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        fit_in_zone(formulas_A, zone_formula_main, width_ratio=0.85, height_ratio=0.8)
        
        register_obj(self, self.objects, "formula_A_1", formula_A_1)
        register_obj(self, self.objects, "formula_A_2", formula_A_2)
        
        self.play(Write(formula_A_1), run_time=1.5)
        self.wait(0.3)
        self.play(Write(formula_A_2), run_time=1.5)
        self.wait(0.5)
    
    run_step(
        self,
        self.objects,
        "先求A的加速度。隔离A，受向右的滑动摩擦力f_k。计算得a_A为3米每二次方秒。",
        zone_subtitle,
        ["formula_A_1", "formula_A_2"],
        step_01
    )
    
    def step_02():
        formula_B_1 = MathTex("F - f_k = M a_B", font_size=36, color=WHITE)
        formula_B_2 = MathTex("a_B = \\frac{F - f_k}{M} = \\frac{20 - 3.0}{3.0} = \\frac{17}{3} \\approx 5.67\\,\\text{m/s}^2", font_size=36, color=YELLOW)
        
        formulas_B = VGroup(formula_B_1, formula_B_2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        formula_A_1_obj = self.objects.get("formula_A_1")
        formula_A_2_obj = self.objects.get("formula_A_2")
        existing_group = VGroup(formula_A_1_obj, formula_A_2_obj)
        
        all_formulas = VGroup(existing_group, formulas_B).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        fit_in_zone(all_formulas, zone_formula_main, width_ratio=0.85, height_ratio=0.85)
        
        register_obj(self, self.objects, "formula_B_1", formula_B_1)
        register_obj(self, self.objects, "formula_B_2", formula_B_2)
        
        self.play(Write(formula_B_1), run_time=1.5)
        self.wait(0.3)
        self.play(Write(formula_B_2), run_time=1.5)
        self.wait(0.5)
    
    run_step(
        self,
        self.objects,
        "再求B的加速度。隔离B，受向右的拉力F和向左的滑动摩擦力f_k。合力等于F减f_k，除以M，算得a_B约为5.67米每二次方秒。",
        zone_subtitle,
        ["formula_A_1", "formula_A_2", "formula_B_1", "formula_B_2"],
        step_02
    )
    
    cleanup_scene(self, self.objects, [])
