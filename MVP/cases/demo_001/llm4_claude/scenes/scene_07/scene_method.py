def scene_scene_07(self):
    reset_scene(self, self.objects)

    zone_goal_main = (0.1, 0.9, 0.16, 0.92)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        title = Text("第三问：求W_F与Q", font_size=32, color=WHITE)
        formula_W = MathTex("W_F = F \\cdot x_B", font_size=36, color=YELLOW)
        formula_Q = MathTex("Q = f_k \\cdot l", font_size=36, color=YELLOW)
        
        energy_goal_group = VGroup(title, formula_W, formula_Q).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        fit_in_zone(energy_goal_group, zone_goal_main, width_ratio=0.8, height_ratio=0.7)
        
        register_obj(self, self.objects, "text_q3", title)
        register_obj(self, self.objects, "formula_W", formula_W)
        register_obj(self, self.objects, "formula_Q", formula_Q)
        
        self.play(Write(title), run_time=0.8)
        self.play(Write(formula_W), run_time=0.8)
        self.play(Write(formula_Q), run_time=0.8)

    run_step(
        self,
        self.objects,
        "计算外力做功，我们需要先求出木板B在这0.6秒内发生的位移。摩擦生热有一个简便公式，直接用摩擦力乘以相对路程即可。",
        zone_subtitle,
        ["text_q3", "formula_W", "formula_Q"],
        step_01,
    )

    cleanup_scene(self, self.objects, [])
