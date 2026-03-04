def scene_scene_01(self):
    reset_scene(self, self.objects)

    zone_problem = (0.05, 0.95, 0.52, 0.92)
    zone_preview = (0.15, 0.85, 0.16, 0.48)
    zone_subtitle = (0.05, 0.95, 0.02, 0.12)

    problem_text = """题目:板块模型(3问)
已知:M=3.0kg, m=1.0kg, L=2.0m, l=0.40m
μₖ=0.30, μₛ=0.40, F=20N
问题:(1)判断滑动并求a; (2)求t,vₐ,vᵦ; (3)求Wᶠ,Q"""

    def step_01():
        problem_block = make_wrapped_text_block(
            problem_text,
            zone_problem,
            font_size=28,
            color=WHITE,
            anchor="top_left"
        )
        register_obj(self, self.objects, "text_block_problem", problem_block)
        self.play(Write(problem_block), run_time=1.5)

    run_step(
        self,
        self.objects,
        "首先,我们来看一下题目描述。木板B放在光滑水平面上,物块A静置在木板上,距离左端0.4米。",
        zone_subtitle,
        ["text_block_problem"],
        step_01
    )

    def step_02():
        floor = Line(
            start=np.array([-3.0, -1.2, 0.0]),
            end=np.array([3.0, -1.2, 0.0]),
            color=WHITE,
            stroke_width=3
        )
        register_obj(self, self.objects, "floor", floor)

        block_B = Rectangle(
            width=2.0,
            height=0.3,
            stroke_color=BLUE,
            stroke_width=3,
            fill_color=BLUE,
            fill_opacity=0.3
        ).shift(np.array([0.0, -1.05, 0.0]))
        register_obj(self, self.objects, "block_B", block_B)

        block_A = Rectangle(
            width=0.5,
            height=0.3,
            stroke_color=YELLOW,
            stroke_width=3,
            fill_color=YELLOW,
            fill_opacity=0.5
        ).shift(np.array([-0.6, -0.75, 0.0]))
        register_obj(self, self.objects, "block_A", block_A)

        preview_group = VGroup(floor, block_B, block_A)
        fit_in_zone(preview_group, zone_preview, width_ratio=0.9, height_ratio=0.8)

        self.play(FadeIn(floor), FadeIn(block_B), FadeIn(block_A), run_time=1.0)

        force_arrow = Arrow(
            start=block_B.get_right() + np.array([0.0, 0.0, 0.0]),
            end=block_B.get_right() + np.array([0.6, 0.0, 0.0]),
            buff=0.0,
            stroke_width=4,
            color=RED
        )
        register_obj(self, self.objects, "force_arrow_F", force_arrow)
        self.play(GrowArrow(force_arrow), run_time=0.8)

        self.motion_scene_01("step_02")

    run_step(
        self,
        self.objects,
        "从t=0时刻起,对木板施加水平向右的恒力F。由于A和B之间存在摩擦力,它们都会向右加速,但加速度不同。",
        zone_subtitle,
        ["text_block_problem", "floor", "block_B", "block_A", "force_arrow_F"],
        step_02
    )

    def step_03():
        self.wait(1.5)

    run_step(
        self,
        self.objects,
        "最终,物块A会从木板的左端滑落。接下来,我们将分三问逐步求解。",
        zone_subtitle,
        ["text_block_problem", "floor", "block_B", "block_A", "force_arrow_F"],
        step_03
    )

    cleanup_scene(self, self.objects, [])
