def scene_scene_07(self):
    reset_scene(self, self.objects)

    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    zone_main = (0.15, 0.85, 0.2, 0.9)

    def step_01():
        text_q3 = Text("第三问：求W_F与Q", font_size=36, color=WHITE)
        place_in_zone(text_q3, zone_main, offset=(0.0, 0.35))
        register_obj(self, self.objects, "text_q3", text_q3)
        self.add(text_q3)

        formula_W = MathTex("W_F = F \\cdot x_B", font_size=40, color=YELLOW)
        formula_Q = MathTex("Q = f_k \\cdot l", font_size=40, color=YELLOW)
        
        formulas = VGroup(formula_W, formula_Q)
        formulas.arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        place_in_zone(formulas, zone_main, offset=(0.0, -0.1))
        
        register_obj(self, self.objects, "formula_W", formula_W)
        register_obj(self, self.objects, "formula_Q", formula_Q)
        self.add(formulas)

    run_step(
        self,
        self.objects,
        "计算外力做功，我们需要先求出木板B在这0.6秒内发生的位移。摩擦生热有一个简便公式，直接用摩擦力乘以相对路程即可。",
        zone_subtitle,
        ["text_q3", "formula_W", "formula_Q"],
        step_01,
    )
    cleanup_scene(self, self.objects, [])
