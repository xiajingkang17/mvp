def motion_scene_02(self, step_id):
    if step_id == "step_01":
        problem_text = self.objects.get("problem_text")
        goal_panel = self.objects.get("goal_panel")
        if problem_text is None or goal_panel is None:
            return []
        return [
            FadeIn(problem_text, run_time=1.0),
            FadeIn(goal_panel, run_time=1.0)
        ]
    
    if step_id == "step_02":
        goal_panel = self.objects.get("goal_panel")
        if goal_panel is None:
            return []
        
        logic_text = (
            "1. 假设A、B相对静止，求共同加速度 a。\n"
            "2. 求A所需的静摩擦力 f_req。\n"
            "3. 比较 f_req 与 f_max (μ_s mg)。\n"
            "4. 若 f_req > f_max，则发生相对滑动，隔离求解 a_A, a_B。"
        )
        
        new_content = Text(logic_text, font_size=24, color=WHITE)
        new_content.move_to(goal_panel.get_center())
        
        return [
            ReplacementTransform(goal_panel, new_content, run_time=1.5)
        ]
    
    return []
