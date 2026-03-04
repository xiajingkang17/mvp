def scene_scene_03(self):
    reset_scene(self, self.objects)

    zone_subtitle = (0.05, 0.95, 0.02, 0.12)
    zone_diagram = (0.05, 0.5, 0.2, 0.9)
    zone_formula = (0.55, 0.95, 0.2, 0.9)

    def step_01():
        # Diagram: System (A+B) and Isolated A
        # System representation (A+B box)
        sys_box = Rectangle(width=2.5, height=1.0, color=WHITE, stroke_width=2)
        sys_box.move_to(ORIGIN + UP * 0.5)
        
        # Force F on system
        arrow_F_sys = Arrow(start=sys_box.get_right(), end=sys_box.get_right() + RIGHT * 1.2, buff=0, color=YELLOW, stroke_width=4)
        label_F_sys = MathTex("F", font_size=24, color=YELLOW).next_to(arrow_F_sys, UP)
        
        # Label for system
        label_sys = Text("系统(A+B)", font_size=20).next_to(sys_box, DOWN)
        
        # Isolated A (smaller box)
        box_A = Rectangle(width=1.0, height=0.6, color=BLUE, stroke_width=2)
        box_A.move_to(ORIGIN + DOWN * 1.5)
        
        # Friction force on A (initially static f_s)
        arrow_f_A = Arrow(start=box_A.get_left(), end=box_A.get_left() + LEFT * 0.8, buff=0, color=RED, stroke_width=4)
        label_f_A = MathTex("f_s", font_size=24, color=RED).next_to(arrow_f_A, UP)
        
        # Label for A
        label_A = Text("物块A", font_size=20).next_to(box_A, DOWN)
        
        # Group diagrams
        diagram_group = VGroup(sys_box, arrow_F_sys, label_F_sys, label_sys, box_A, arrow_f_A, label_f_A, label_A)
        fit_in_zone(diagram_group, zone_diagram, width_ratio=0.9)
        register_obj(self, self.objects, "diagram_system", diagram_group)
        self.add(diagram_group)

        # Equations
        eq1_text = MathTex("F = (M+m)a", font_size=32, color=WHITE)
        eq2_text = MathTex("a = \\frac{F}{M+m} = 5.0 \\, \\text{m/s}^2", font_size=32, color=WHITE)
        eq3_text = MathTex("f_s = ma = 5.0 \\, \\text{N}", font_size=32, color=WHITE)
        
        eq_group = VGroup(eq1_text, eq2_text, eq3_text)
        eq_group.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        place_in_zone(eq_group, zone_formula, offset=(0.0, 0.2))
        
        register_obj(self, self.objects, "equation_1", eq1_text)
        register_obj(self, self.objects, "equation_2", eq2_text)
        register_obj(self, self.objects, "equation_3", eq3_text)
        
        # Animate equations line by line
        self.play(Write(eq1_text))
        self.play(Write(eq2_text))
        self.play(Write(eq3_text))

    run_step(
        self,
        self.objects,
        "假设A、B相对静止，整体加速度a为5米每二次方秒。此时A需要5牛的静摩擦力来维持这个加速度。",
        zone_subtitle,
        ["diagram_system", "equation_1", "equation_2", "equation_3"],
        step_01,
    )

    def step_02():
        # Update friction label from f_s to f_k
        diagram_group = self.objects["diagram_system"]
        
        # Find the label mobject (assuming structure from step_01)
        # We need to identify the specific MathTex object for the label
        # Since we can't easily query by content in generated code without helpers,
        # we rely on the structure: label_f_A is the 6th submobject (index 5) if added in order
        # Or better, we just recreate the label to ensure correctness
        
        # Locate the arrow to position the new label
        # arrow_f_A is index 4 in the group created in step_01
        arrow_f_A = diagram_group[4]
        
        # Create new label
        new_label = MathTex("f_k", font_size=24, color=RED).next_to(arrow_f_A, UP)
        
        # Replace old label (index 5) with new label
        diagram_group[5].become(new_label)
        
        # Add comparison text (5N > 4N) temporarily or as part of the scene flow
        # The prompt asks to show comparison. Let's add it to the formula zone or near the diagram.
        # Adding to formula zone for cleanliness.
        comp_text = MathTex("5.0 \\, \\text{N} > 4.0 \\, \\text{N}", font_size=32, color=YELLOW)
        comp_text.next_to(self.objects["equation_3"], DOWN, buff=0.5)
        
        register_obj(self, self.objects, "comparison_text", comp_text)
        self.play(FadeIn(comp_text))

    run_step(
        self,
        self.objects,
        "但是，A与B间的最大静摩擦力f_max只有4牛。因为需要的5牛大于最大的4牛，所以假设不成立，A会相对B滑动。摩擦力变为滑动摩擦力f_k。",
        zone_subtitle,
        ["diagram_system", "equation_1", "equation_2", "equation_3", "comparison_text"],
        step_02,
    )

    cleanup_scene(self, self.objects, [])
