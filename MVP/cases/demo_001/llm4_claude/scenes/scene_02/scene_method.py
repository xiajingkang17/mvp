def scene_scene_02(self):
    reset_scene(self, self.objects)

    zone_problem_left = (0.05, 0.48, 0.16, 0.92)
    zone_goal_right = (0.52, 0.95, 0.16, 0.92)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        problem_text = Text(
            "第一问：判断并求加速度\n目标：判断是否滑动？求a_A, a_B",
            font_size=26,
            color=WHITE
        )
        problem_text = make_wrapped_text_block(
            "第一问：判断并求加速度\n目标：判断是否滑动？求a_A, a_B",
            zone_problem_left,
            font_size=26,
            color=WHITE,
            anchor="top_left"
        )
        register_obj(self, self.objects, "text_q1", problem_text)
        self.add(problem_text)

        block_A = Rectangle(width=0.4, height=0.3, color=YELLOW, stroke_width=3, fill_opacity=0.3)
        block_B = Rectangle(width=1.0, height=0.2, color=BLUE, stroke_width=3, fill_opacity=0.3)
        blocks = VGroup(block_B, block_A.move_to(block_B.get_center() + UP * 0.25))
        place_in_zone(blocks, zone_goal_right, offset=(0.0, 0.25))
        register_obj(self, self.objects, "block_A_icon", block_A)
        register_obj(self, self.objects, "block_B_icon", block_B)
        self.add(blocks)

        flow_items = VGroup(
            Text("1. 假设整体加速", font_size=22, color=YELLOW),
            Text("2. 计算所需f_s", font_size=22, color=WHITE),
            Text("3. 比较f_s与f_max", font_size=22, color=WHITE),
            Text("4. 判断滑动", font_size=22, color=WHITE),
            Text("5. 隔离求a", font_size=22, color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        place_in_zone(flow_items, zone_goal_right, offset=(0.0, -0.15))
        register_obj(self, self.objects, "logic_flow", flow_items)
        self.add(flow_items)

    run_step(
        self,
        self.objects,
        "第一问的核心是判断静摩擦力是否被突破。我们需要先假设它们一起加速，看需要多大的静摩擦力。",
        zone_subtitle,
        ["text_q1", "block_A_icon", "block_B_icon", "logic_flow"],
        step_01
    )

    def step_02():
        logic_flow = self.objects["logic_flow"]
        for i in range(1, 5):
            logic_flow[i].set_color(YELLOW)
            self.wait(0.3)

    run_step(
        self,
        self.objects,
        "如果所需的静摩擦力超过了最大静摩擦力，假设就不成立，物块就会滑动。确认滑动后，我们再用牛顿第二定律隔离求解各自的加速度。",
        zone_subtitle,
        ["text_q1", "block_A_icon", "block_B_icon", "logic_flow"],
        step_02
    )

    cleanup_scene(self, self.objects, [])
