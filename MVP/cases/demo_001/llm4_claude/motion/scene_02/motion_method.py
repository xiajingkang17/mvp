def motion_scene_02(self, step_id):
    if step_id == "step_01":
        text_q1 = self.objects.get("text_q1")
        block_A_icon = self.objects.get("block_A_icon")
        block_B_icon = self.objects.get("block_B_icon")
        logic_flow = self.objects.get("logic_flow")
        
        anims = []
        if text_q1:
            anims.append(FadeIn(text_q1, shift=DOWN*0.3))
        if block_A_icon:
            anims.append(FadeIn(block_A_icon, shift=UP*0.2))
        if block_B_icon:
            anims.append(FadeIn(block_B_icon, shift=UP*0.2))
        if logic_flow:
            anims.append(FadeIn(logic_flow, shift=RIGHT*0.3))
        
        return anims
    
    if step_id == "step_02":
        logic_flow = self.objects.get("logic_flow")
        if logic_flow is None:
            return []
        
        return [Indicate(logic_flow, scale_factor=1.05)]
    
    return []
