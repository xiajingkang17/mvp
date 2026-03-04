def motion_scene_08(self, step_id):
    if step_id == "step_01":
        calc_xB = self.objects.get("calc_xB")
        calc_WF = self.objects.get("calc_WF")
        if calc_xB is None or calc_WF is None:
            return []
        return [
            FadeIn(calc_xB, shift=UP * 0.5),
            FadeIn(calc_WF, shift=UP * 0.5)
        ]
    
    if step_id == "step_02":
        calc_Q = self.objects.get("calc_Q")
        if calc_Q is None:
            return []
        return [
            FadeIn(calc_Q, shift=UP * 0.5)
        ]
    
    return []
