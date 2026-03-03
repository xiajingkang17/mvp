def scene_scene_05(self):
    reset_scene(self, self.objects)

    zone_main = (0.05, 0.45, 0.2, 0.9)
    zone_formula = (0.55, 0.95, 0.2, 0.9)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        # Diagram: Board B and Block A
        board = Rectangle(width=4.0, height=0.6, color=BLUE, stroke_width=4)
        board.shift(LEFT * 0.5)
        
        block = Rectangle(width=1.0, height=0.6, color=YELLOW, stroke_width=4)
        block.next_to(board, LEFT, buff=0.0)
        
        # Labels
        label_b = Text("B", font_size=24, color=BLUE).next_to(board, DOWN)
        label_a = Text("A", font_size=24, color=YELLOW).next_to(block, UP)
        
        # Relative displacement arrow
        arrow_start = block.get_center()
        arrow_end = board.get_left() + LEFT * 0.5
        rel_arrow = Arrow(arrow_start, arrow_end, buff=0.0, color=RED, stroke_width=4)
        
        label_l = MathTex("l", font_size=28, color=RED).next_to(rel_arrow, UP)
        
        diagram = VGroup(board, block, label_b, label_a, rel_arrow, label_l)
        fit_in_zone(diagram, zone_main, width_ratio=0.9, height_ratio=0.8)
        place_in_zone(diagram, zone_main, offset=(0.0, 0.0))
        
        register_obj(self, self.objects, "diagram_rel", diagram)
        self.add(diagram)

    run_step(
        self,
        self.objects,
        "首先明确几何条件。物块相对于木板向左移动了l的距离，这就是相对位移。",
        zone_subtitle,
        ["diagram_rel"],
        step_01,
    )
    cleanup_step(self, self.objects, ["diagram_rel"])

    def step_02():
        # Goal Panel
        title = Text("(2) 求滑落时间t及瞬时速度", font_size=32, color=WHITE)
        title.to_edge(UP, buff=0.2)
        
        line1 = Text("几何条件：相对位移 x_rel = l = 0.40 m", font_size=24, color=WHITE)
        line1.next_to(title, DOWN, buff=0.4)
        
        line2 = Text("运动学公式：", font_size=24, color=WHITE)
        line2.next_to(line1, DOWN, buff=0.4)
        
        eq1 = MathTex("a_{rel} = a_B - a_A", font_size=24, color=YELLOW)
        eq1.next_to(line2, DOWN, buff=0.2, aligned_edge=LEFT)
        eq1.shift(LEFT * 0.5)
        
        eq2 = MathTex("l = \\frac{1}{2} a_{rel} t^2", font_size=24, color=YELLOW)
        eq2.next_to(eq1, DOWN, buff=0.2, aligned_edge=LEFT)
        
        eq3 = MathTex("v_A = a_A t, \\quad v_B = a_B t", font_size=24, color=YELLOW)
        eq3.next_to(eq2, DOWN, buff=0.2, aligned_edge=LEFT)
        
        panel = VGroup(title, line1, line2, eq1, eq2, eq3)
        fit_in_zone(panel, zone_formula, width_ratio=0.9, height_ratio=0.9)
        place_in_zone(panel, zone_formula, offset=(0.0, 0.0))
        
        register_obj(self, self.objects, "goal_panel_q2", panel)
        self.add(panel)

    run_step(
        self,
        self.objects,
        "利用相对加速度和位移公式求出时间t，再分别用速度公式求出v_A和v_B。",
        zone_subtitle,
        ["diagram_rel", "goal_panel_q2"],
        step_02,
    )
    cleanup_scene(self, self.objects, [])
