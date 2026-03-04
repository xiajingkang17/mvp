# Mechanics Component Interfaces

以下内容是力学组件的接口级摘要，只用于参考：

- 常用构造参数名称
- 典型几何外观
- 常见子对象命名
- 适合的场景类型

不要：

- 在最终代码里 `import` 这些本地路径
- 逐字复制这些组件源码
- 假设这些自定义类在最终 runtime 中一定可用

如果当前 scene 只是需要“类似外观”，优先把这些接口信息翻译成基础 Manim 图元。

## Cart

- 类名：`Cart`
- 典型参数：`width`, `height`, `wheel_radius`, `color`, `stroke_width`
- 几何外观：矩形车身 + 两个轮子 + 两个轮轴点
- 常见子对象：`body`, `left_wheel`, `right_wheel`, `left_axle`, `right_axle`
- 适合：水平小车、斜面小车、轨道小车

## QuarterCart

- 类名：`QuarterCart`
- 典型参数：`side_length`, `wheel_radius`, `color`, `stroke_width`
- 几何外观：带四分之一圆槽口的车体 + 两个轮子
- 常见子对象：`cart_body`, `left_wheel`, `right_wheel`
- 适合：圆弧轨道附近的小车示意

## ArcTrack

- 类名：`ArcTrack`
- 典型参数：`center`, `radius`, `start`, `end`, `color`, `stroke_width`
- 几何外观：圆弧轨道
- 常见子对象：`arc`
- 适合：圆弧轨道、圆周局部轨迹示意

## FixedPulley

- 类名：`FixedPulley`
- 典型参数：`radius`, `rod_length`, `color`, `stroke_width`
- 几何外观：滑轮 + 上方固定杆
- 常见子对象：`base_pulley`, `fixed_rod`
- 适合：定滑轮受力/连接关系示意

## Rope

- 类名：`Rope`
- 典型参数：`length`, `angle`, `color`, `stroke_width`
- 几何外观：一段直线绳
- 常见子对象：`rope`
- 适合：直绳连接、绳方向提示

## Spring

- 类名：`Spring`
- 典型参数：`length`, `height`, `num_coils`, `end_length`, `color`, `stroke_width`
- 几何外观：左右直线端 + 中间折线弹簧
- 常见子对象：`left_end_line`, `zigzag`, `right_end_line`
- 适合：弹簧振子、弹簧连接示意

## Rod

- 类名：`Rod`
- 典型参数：`length`, `thickness`, `color`, `stroke_width`
- 几何外观：细长矩形杆
- 常见子对象：`rod`
- 适合：刚性杆、连接杆、杠杆示意

## Wall

- 类名：`Wall`
- 典型参数：`length`, `angle`, `rise_to`, `hatch_spacing`, `hatch_length`, `contact_offset_y`, `color`, `stroke_width`
- 几何外观：主接触线 + 斜短线阴影
- 适合：地面、斜面、挡板、接触边界
- 说明：`angle + rise_to` 共同决定倾斜方向

## Weight

- 类名：`Weight`
- 典型参数：`width`, `height`, `hook_radius`, `color`, `stroke_width`
- 几何外观：矩形重物 + 顶部挂钩环
- 适合：砝码、悬挂重物、滑轮配重
