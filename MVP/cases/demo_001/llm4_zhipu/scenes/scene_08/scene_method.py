def scene_scene_08(self):
    reset_scene(self, self.objects)

    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    zone_main = (0.15, 0.85, 0.2, 0.9)

    def step_01():
        # Line 1: x_B calculation
        line1 = MathTex("x_B = \\frac{1}{2} a_B t^2 \\approx 1.02 \\, \\text{m}", font_size=40, color=WHITE)
        # Line 2: W_F calculation
        line2 = MathTex("W_F = F x_B = 20 \\times 1.02 = 20.4 \\, \\text{J}", font_size=40, color=WHITE)
        
        # Group and layout
        group = VGroup(line1, line2).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        place_in_zone(group, zone_main, offset=(0.0, 0.2))
        
        # Register and add
        register_obj(self, self.objects, "calc_xB", line1)
        register_obj(self, self.objects, "calc_WF", line2)
        self.add(group)

    run_step(
        self,
        self.objects,
        "计算B的位移，得到x_B约为1.02米。进而算出W_F为20.4焦耳。",
        zone_subtitle,
        ["calc_xB", "calc_WF"],
        step_01,
    )

    def step_02():
        # Line 3: Q calculation
        line3 = MathTex("Q = f_k l = 3.0 \\times 0.4 = 1.2 \\, \\text{J}", font_size=40, color=YELLOW)
        
        # Get previous group to append
        prev_group = self.objects["calc_xB"].get_parent() or VGroup(self.objects["calc_xB"], self.objects["calc_WF"])
        new_group = VGroup(prev_group, line3).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        
        # Re-center the expanded group
        place_in_zone(new_group, zone_main, offset=(0.0, 0.2))
        
        # Register and add
        register_obj(self, self.objects, "calc_Q", line3)
        self.add(line3)

    run_step(
        self,
        self.objects,
        "最后算摩擦生热Q。f_k是3牛，相对位移l是0.4米，所以Q等于1.2焦耳。",
        zone_subtitle,
        ["calc_xB", "calc_WF", "calc_Q"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
