# 安全规则

1. 禁止导入或使用：`os`、`subprocess`、`pathlib`、`socket`、`urllib`、`requests`。
2. 禁止调用：`open`、`eval`、`exec`、`compile`、`__import__`。
3. 不要访问文件系统、网络或系统命令。
4. 仅在内存中构建和更新 Manim 对象。
5. 不要读取环境变量或依赖外部运行状态。
