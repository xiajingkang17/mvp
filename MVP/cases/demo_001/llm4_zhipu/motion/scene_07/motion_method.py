def motion_scene_07(self, step_id):
    if step_id == "step_01":
        text_q3 = self.objects.get("text_q3")
        formula_W = self.objects.get("formula_W")
        formula_Q = self.objects.get("formula_Q")
        
        if text_q3 is None or formula_W is None or formula_Q is None:
            return []

        return [
            FadeIn(text_q3, shift=UP * 0.5),
            FadeIn(formula_W, shift=UP * 0.5),
            FadeIn(formula_Q, shift=UP * 0.5)
        ]
    return []
