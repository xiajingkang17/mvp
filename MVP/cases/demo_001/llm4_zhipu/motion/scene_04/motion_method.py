def motion_scene_04(self, step_id):
    if step_id == "step_01":
        diagram_A = self.objects.get("diagram_A")
        calc_a_A = self.objects.get("calc_a_A")
        
        if diagram_A is None or calc_a_A is None:
            return []
            
        return [
            FadeIn(diagram_A, shift=LEFT*0.5),
            Write(calc_a_A)
        ]
        
    elif step_id == "step_02":
        diagram_B = self.objects.get("diagram_B")
        calc_a_B = self.objects.get("calc_a_B")
        
        if diagram_B is None or calc_a_B is None:
            return []
            
        return [
            FadeIn(diagram_B, shift=RIGHT*0.5),
            Write(calc_a_B)
        ]
        
    return []
