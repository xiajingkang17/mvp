def scene_scene_08(self):
    reset_scene(self, self.objects)

    zone_main = (0.15, 0.85, 0.2, 0.85)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        # Step 1: Calculate displacement and Work
        # Text content for step 1
        text_1 = Text("1. 计算木板位移 x_B：", font_size=32, color=WHITE)
        math_1 = MathTex("x_B = \\frac{1}{2} a_B t^2 = 0.5 \\cdot \\frac{17}{3} \\cdot 0.3 \\approx 0.85 \\, \\text{m}", font_size=32, color=WHITE)
        
        text_2 = Text("2. 计算外力做功 W_F：", font_size=32, color=WHITE)
        math_2 = MathTex("W_F = F \\cdot x_B = 20 \\cdot 0.85 = 17.0 \\, \\text{J}", font_size=32, color=WHITE)

        # Group and arrange
        group = VGroup(text_1, math_1, text_2, math_2)
        group.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        # Place in zone
        place_in_zone(group, zone_main, offset=(0.0, 0.2))
        
        register_obj(self, self.objects, "calc_panel_q3", group)
        self.add(group)

    run_step(
        self,
        self.objects,
        "首先计算木板B的位移，然后求出外力做功W_F。",
        zone_subtitle,
        ["calc_panel_q3"],
        step_01,
    )

    def step_02():
        # Step 2: Calculate Heat Q
        # Retrieve existing object
        group = self.objects["calc_panel_q3"]
        
        # New content for step 3
        text_3 = Text("3. 计算摩擦生热 Q：", font_size=32, color=WHITE)
        math_3 = MathTex("Q = f_k \\cdot l = \\mu_k m g l", font_size=32, color=WHITE)
        math_4 = MathTex("Q = 0.3 \\cdot 1 \\cdot 10 \\cdot 0.4 = 1.2 \\, \\text{J}", font_size=32, color=WHITE)

        # Create a temporary group to calculate position
        new_group = VGroup(text_3, math_3, math_4)
        new_group.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        # Position new group below existing content
        new_group.next_to(group, DOWN, buff=0.5, aligned_edge=LEFT)
        
        # Add to the main group and register update
        group.add(new_group)
        register_obj(self, self.objects, "calc_panel_q3", group)
        self.add(new_group)

    run_step(
        self,
        self.objects,
        "接着计算摩擦生热Q，利用相对位移可以直接得出结果。",
        zone_subtitle,
        ["calc_panel_q3"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
