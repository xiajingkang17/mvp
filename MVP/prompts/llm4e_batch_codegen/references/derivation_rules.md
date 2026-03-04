# 推导显示规则

## 目标

推导类 scene 要体现推理过程，而不是把整组公式瞬间堆到屏幕上。

## 规则

1. 两行及以上推导不能整组一起出现
2. 不要对多行推导组直接 `self.add(group)`
3. 不要对多行推导组直接 `Write(group)` 或 `FadeIn(group)`
4. 每一行公式应是独立对象
5. 标题、说明、条件提示也应与公式拆开

## 推荐写法

1. 先用 `VGroup(...).arrange(DOWN, aligned_edge=LEFT)` 做静态排版
2. 再按顺序逐行 `Write`
3. 如果有结论行，结论行单独高亮

## 禁止写法

1. 先把 3 到 5 行公式拼成一个大 `VGroup`
2. 然后一次 `self.add(group)`
3. 或一次 `self.play(Write(group))`
