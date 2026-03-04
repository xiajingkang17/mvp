def motion_scene_02(self, step_id):
    if step_id == "step_01":
        text_q1 = self.objects.get("text_q1")
        block_A_icon = self.objects.get("block_A_icon")
        block_B_icon = self.objects.get("block_B_icon")
        logic_flow = self.objects.get("logic_flow")
        
        if text_q1 is None or block_A_icon is None or block_B_icon is None or logic_flow is None:
            return []

        return [
            FadeIn(text_q1, shift=UP * 0.5),
            FadeIn(block_A_icon, shift=LEFT * 0.5),
            FadeIn(block_B_icon, shift=LEFT * 0.5),
            FadeIn(logic_flow, shift=RIGHT * 0.5)
        ]
    
    if step_id == "step_02":
        logic_flow = self.objects.get("logic_flow")
        if logic_flow is None:
            return []
        
        return [
            Indicate(logic_flow, scale_factor=1.1, color=YELLOW)
        ]
    
    return []
