def motion_scene_09(self, step_id):
    if step_id == "step_01":
        check_eq = self.objects.get("check_eq")
        if check_eq is None:
            return []
        return [FadeIn(check_eq, shift=DOWN*0.3)]
    
    if step_id == "step_02":
        summary_table = self.objects.get("summary_table")
        if summary_table is None:
            return []
        return [FadeIn(summary_table, shift=LEFT*0.3)]
    
    return []
