def scene_scene_07(self):
    reset_scene(self, self.objects)

    zone_main = (0.15, 0.85, 0.25, 0.85)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    def step_01():
        title = Text("(3) 求外力做功 W_F 与摩擦生热 Q", font_size=36, color=WHITE)
        place_in_zone(title, zone_main, offset=(0.0, 0.35))
        register_obj(self, self.objects, "goal_panel_q3_title", title)
        self.add(title)

        plan_text = Text(
            "1. 求 W_F：需要先求木板对地位移 x_B\n   W_F = F * x_B\n\n2. 求 Q：利用相对位移\n   Q = f_k * x_rel = f_k * l",
            font_size=28,
            color=WHITE,
            line_spacing=0.5
        )
        place_in_zone(plan_text, zone_main, offset=(0.0, -0.15))
        register_obj(self, self.objects, "goal_panel_q3", plan_text)
        self.add(plan_text)

    run_step(
        self,
        self.objects,
        "最后是第三问，求外力做功W_F和摩擦生热Q。外力做功等于力乘以木板的位移，所以我们需要先求出木板B的位移。而摩擦生热Q有一个简便算法，它等于滑动摩擦力乘以相对位移。",
        zone_subtitle,
        ["goal_panel_q3", "goal_panel_q3_title"],
        step_01,
    )
    cleanup_scene(self, self.objects, [])
