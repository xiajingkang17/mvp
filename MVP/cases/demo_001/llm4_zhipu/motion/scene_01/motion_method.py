def motion_scene_01(self, step_id):
    if step_id == "step_02":
        board_B = self.objects.get("board_B")
        block_A = self.objects.get("block_A")
        
        if board_B is None or block_A is None:
            return []

        # Step 02: 板块模型运动演示
        # 运动参数：木板B向右加速，物块A向右加速但较慢
        # 模拟时间 t = 0.55s (sqrt(0.3))
        # a_A = 3.0, a_B = 17/3 ≈ 5.67
        # x_B = 0.5 * a_B * t^2 ≈ 0.85
        # x_A = 0.4 + 0.5 * a_A * t^2 ≈ 0.45
        
        # 视觉缩放比例 (将物理位移映射到屏幕坐标)
        # 假设屏幕上 1 unit 对应 1 meter
        scale = 1.0
        
        # 计算终点位置 (相对于初始位置)
        # 初始位置由 scene 方法设定，这里计算位移量
        t_final = 0.55
        a_B = 17.0 / 3.0
        a_A = 3.0
        
        disp_B = 0.5 * a_B * t_final**2
        disp_A = 0.5 * a_A * t_final**2
        
        # 获取初始位置 (假设初始时刻已由 scene 设置好)
        # 这里我们通过获取当前对象的中心点作为起点
        start_pos_B = board_B.get_center()
        start_pos_A = block_A.get_center()
        
        # 计算终点坐标
        # 运动方向向右 (x轴正方向)
        end_pos_B = start_pos_B + np.array([disp_B * scale, 0, 0])
        end_pos_A = start_pos_A + np.array([disp_A * scale, 0, 0])
        
        # 动画时长
        run_time = 8.0
        
        # 创建动画
        # 使用 MoveAlongPath 或直接使用 target 参数的动画
        # 这里使用 MoveToPoint (通过 animate 语法或 MoveTo)
        # 为了平滑，使用 UpdateFromAlpha 或者简单的 MoveTo
        
        anim_board = board_B.animate.move_to(end_pos_B).set(run_time=run_time)
        anim_block = block_A.animate.move_to(end_pos_A).set(run_time=run_time)
        
        return [anim_board, anim_block]
        
    return []
