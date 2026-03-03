def motion_scene_05(self, step_id):
    if step_id == "step_01":
        diagram = self.objects.get("diagram_rel")
        if diagram is None:
            return []
        return [FadeIn(diagram)]
    
    if step_id == "step_02":
        goal_panel = self.objects.get("goal_panel_q2")
        if goal_panel is None:
            return []
        return [FadeIn(goal_panel)]
    
    return []
