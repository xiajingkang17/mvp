#!/usr/bin/env python3
"""
静态代码解析器 2.0 - 用于解析 3Blue1Brown 的 Manim 动画源码
使用 Python 内置的 ast 模块进行纯静态分析，不执行代码

2.0 新增功能：时间轴切片（Temporal Slicing）
以 self.play() 为界限，将代码按动画步骤进行分块聚合
"""

import ast
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass


@dataclass
class Operation:
    """表示一个代码操作（对象创建或空间操作）"""
    type: str  # "object" 或 "relation"
    data: Dict[str, Any]
    line_number: int


class ManimSceneParser(ast.NodeVisitor):
    """
    遍历 AST 节点，提取 Manim 场景的静态信息

    2.0 版本核心功能：
    1. 场景识别：识别继承自 Scene/InteractiveScene 等的类
    2. 时间轴切片：以 self.play() 为界限将代码分块
    3. 实体抽取：提取 construct 方法中的对象实例化
    4. 关系提取：捕获空间布局方法调用（next_to, shift, scale, move_to, align_to, arrange, to_corner 等）
    """

    # 已知的 Scene 基类名称
    SCENE_BASE_CLASSES = {"Scene", "InteractiveScene", "PiCreatureScene", "TeacherStudentsScene"}

    # 需要捕获的空间方法名称
    SPATIAL_METHODS = {
        "next_to", "shift", "scale", "move_to", "align_to",
        "arrange", "arrange_in_grid", "to_corner", "to_edge", "center",
        "shift_onto_screen", "set_width", "set_height", "match_width",
        "match_height", "stretch_to_fit_width", "stretch_to_fit_height",
        "scale_to_fit_width", "scale_to_fit_height", "surround"
    }

    # 需要作为切割点的方法名称
    CUTPOINT_METHODS = {"play", "wait"}

    def __init__(self, file_path: str):
        """
        初始化解析器

        Args:
            file_path: 要解析的 Python 文件路径
        """
        self.file_path = file_path
        self.current_class: Optional[str] = None  # 当前正在解析的类名
        self.is_in_construct = False  # 是否在 construct 方法中

        # 存储解析结果
        self.result: Dict[str, Any] = {
            "file_path": file_path,
            "scenes": {}  # {类名: {animation_steps: [...]}}
        }

        # 临时存储：按行号排序的操作流
        self.operations: List[Operation] = []  # 当前场景的所有操作
        self.step_counter = 0  # 步骤计数器

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        处理类定义节点

        判断是否是 Scene 子类，如果是则进入类体进行解析
        """
        # 保存当前类名
        prev_class = self.current_class
        self.current_class = node.name

        # 检查是否继承自 Scene 类
        is_scene_class = False
        for base in node.bases:
            base_name = self._get_name_from_node(base)
            if base_name in self.SCENE_BASE_CLASSES:
                is_scene_class = True
                break

        # 如果是 Scene 类，初始化存储结构并访问类体
        if is_scene_class:
            self.result["scenes"][node.name] = {
                "animation_steps": []
            }
            # 重置临时存储
            self.operations = []
            self.step_counter = 0

            # 继续访问子节点
            self.generic_visit(node)

            # 处理剩余的未触发操作（如果 construct 结束后还有操作）
            if self.operations:
                self._create_step(
                    trigger=None,
                    line_number=None,
                    is_final=True
                )

        # 恢复之前的类名
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        处理函数定义节点

        重点关注 construct 方法，在其中提取对象和空间关系
        """
        # 检查是否是 construct 方法
        prev_in_construct = self.is_in_construct
        if node.name == "construct" and self.current_class:
            self.is_in_construct = True
            # 只在 construct 方法中深入解析
            self.generic_visit(node)

        # 恢复之前的状态
        self.is_in_construct = prev_in_construct

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        处理赋值语句节点

        在 construct 方法中提取对象实例化，存储到操作流中
        """
        if not self.is_in_construct or not self.current_class:
            self.generic_visit(node)
            return

        # 遍历所有赋值目标
        for target in node.targets:
            # 提取左侧的变量名
            var_name = self._extract_var_name(target)
            if not var_name:
                continue

            # 提取右侧的实例化信息
            obj_info = self._extract_object_info(node.value)
            if obj_info:
                # 存储到操作流中
                operation = Operation(
                    type="object",
                    data={
                        "variable_name": var_name,
                        "object_type": obj_info["type"],
                        "arguments": obj_info["arguments"],
                        "line_number": node.lineno
                    },
                    line_number=node.lineno
                )
                self.operations.append(operation)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """
        处理方法调用节点

        1. 检查是否是切割点（self.play 或 self.wait），如果是则创建新的 step
        2. 检查是否是空间方法调用，如果是则存储到操作流中
        """
        if not self.is_in_construct or not self.current_class:
            self.generic_visit(node)
            return

        # 检查是否是切割点方法
        method_name = self._get_method_name(node)
        subject = self._get_call_subject(node)

        if method_name in self.CUTPOINT_METHODS and subject == "self":
            # 遇到切割点，创建新的 step
            self._create_step(
                trigger=f"self.{method_name}({self._get_call_arguments(node)})",
                line_number=node.lineno
            )

            # 清空当前操作流（已打包到 step 中）
            self.operations = []

        # 检查是否是空间方法
        elif method_name in self.SPATIAL_METHODS:
            # 提取参数
            args = []
            kwargs = {}

            for arg in node.args:
                args.append(self._node_to_text(arg))

            for kwarg in node.keywords:
                kwargs[kwarg.arg] = self._node_to_text(kwarg.value)

            # 存储到操作流中
            operation = Operation(
                type="relation",
                data={
                    "subject": subject,
                    "action": method_name,
                    "args": args,
                    "kwargs": kwargs,
                    "line_number": node.lineno
                },
                line_number=node.lineno
            )
            self.operations.append(operation)

        self.generic_visit(node)

    def _create_step(self, trigger: Optional[str], line_number: Optional[int], is_final: bool = False) -> None:
        """
        创建一个时间切片（Step）

        将当前操作流中所有在切割点之前的操作打包成一个 step

        Args:
            trigger: 触发该 step 的代码（如 "self.play(...)"）
            line_number: 触发点的行号
            is_final: 是否是最后一个 step（construct 方法结束后的剩余操作）
        """
        if not self.current_class:
            return

        self.step_counter += 1

        # 分离对象和关系操作
        prior_objects = []
        prior_relations = []

        for operation in self.operations:
            if operation.type == "object":
                prior_objects.append(operation.data)
            elif operation.type == "relation":
                prior_relations.append(operation.data)

        # 创建 step
        step = {
            "step_id": self.step_counter,
            "trigger": trigger if not is_final else "<construct_end>",
            "line_number": line_number if not is_final else "<end>",
            "prior_objects": prior_objects,
            "prior_relations": prior_relations
        }

        # 添加到结果中
        self.result["scenes"][self.current_class]["animation_steps"].append(step)

    def _extract_var_name(self, node: ast.AST) -> Optional[str]:
        """
        从赋值目标节点中提取变量名

        处理：
            self.circle -> "self.circle"
            face -> "face"
            axes, bars -> "axes" （多个目标时只取第一个）
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # 处理 self.attr 的形式
            obj = self._get_name_from_node(node.value)
            return f"{obj}.{node.attr}" if obj else node.attr
        elif isinstance(node, ast.Tuple):
            # 处理多个赋值目标，返回第一个
            if node.elts:
                return self._extract_var_name(node.elts[0])
        return None

    def _extract_object_info(self, node: ast.AST) -> Optional[Dict[str, Any]]:
        """
        从节点中提取对象实例化信息

        处理：
            Circle(radius=2) -> {"type": "Circle", "arguments": {"radius": "2"}}
            DieFace(n, fill_color=BLUE_E) -> {"type": "DieFace", "arguments": ["n", "BLUE_E"]}
            VGroup(*faces) -> {"type": "VGroup", "arguments": ["*faces"]}
        """
        if not isinstance(node, ast.Call):
            return None

        obj_type = self._get_name_from_node(node.func)
        if not obj_type:
            return None

        arguments = []

        # 提取位置参数
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                # 处理 *args 展开语法
                arguments.append(f"*{self._node_to_text(arg.value)}")
            else:
                arguments.append(self._node_to_text(arg))

        # 提取关键字参数
        for kwarg in node.keywords:
            if kwarg.arg:
                # 普通关键字参数 name=value
                value_text = self._node_to_text(kwarg.value)
                arguments.append(f"{kwarg.arg}={value_text}")
            else:
                # **kwargs 展开语法
                arguments.append(f"**{self._node_to_text(kwarg.value)}")

        return {
            "type": obj_type,
            "arguments": arguments
        }

    def _get_method_name(self, node: ast.Call) -> Optional[str]:
        """
        从调用节点中提取方法名

        例如：
            self.circle.next_to(...) -> "next_to"
            self.play(...) -> "play"
        """
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_call_subject(self, node: ast.Call) -> Optional[str]:
        """
        从调用节点中提取调用主体

        例如：
            self.circle.next_to(...) -> "self.circle"
            self.play(...) -> "self"
        """
        if isinstance(node.func, ast.Attribute):
            return self._node_to_text(node.func.value)
        return None

    def _get_call_arguments(self, node: ast.Call) -> str:
        """
        获取调用的参数文本

        例如：
            self.play(FadeIn(circle)) -> "FadeIn(circle)"
            self.wait(1) -> "1"
        """
        args_text = []
        for arg in node.args:
            args_text.append(self._node_to_text(arg))

        for kwarg in node.keywords:
            if kwarg.arg:
                value_text = self._node_to_text(kwarg.value)
                args_text.append(f"{kwarg.arg}={value_text}")
            else:
                args_text.append(f"**{self._node_to_text(kwarg.value)}")

        return ", ".join(args_text)

    def _get_name_from_node(self, node: ast.AST) -> Optional[str]:
        """
        从节点中提取名称字符串

        处理各种可能的形式：
            Name(id="Circle") -> "Circle"
            Attribute(value=Name(id="self"), attr="circle") -> "self"
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # 对于 self.attr 形式，只返回对象部分
            return self._node_to_text(node.value)
        return None

    def _node_to_text(self, node: ast.AST) -> str:
        """
        将 AST 节点转换为源代码文本字符串

        这是用于获取参数值的通用方法，尽可能还原原始代码
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.List):
            elements = [self._node_to_text(e) for e in node.elts]
            return f"[{', '.join(elements)}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._node_to_text(e) for e in node.elts]
            return f"({', '.join(elements)})"
        elif isinstance(node, ast.Dict):
            keys = [self._node_to_text(k) for k in node.keys]
            values = [self._node_to_text(v) for v in node.values]
            items = [f"{k}: {v}" for k, v in zip(keys, values)]
            return f"{{{', '.join(items)}}}"
        elif isinstance(node, ast.UnaryOp):
            op = self._get_op_symbol(node.op)
            operand = self._node_to_text(node.operand)
            return f"{op}{operand}"
        elif isinstance(node, ast.BinOp):
            left = self._node_to_text(node.left)
            op = self._get_op_symbol(node.op)
            right = self._node_to_text(node.right)
            return f"{left} {op} {right}"
        elif isinstance(node, ast.Compare):
            # 处理比较操作符
            left = self._node_to_text(node.left)
            ops_and_comparators = []
            for op, comp in zip(node.ops, node.comparators):
                op_symbol = self._get_cmp_symbol(op)
                comp_text = self._node_to_text(comp)
                ops_and_comparators.append(f"{op_symbol} {comp_text}")
            return f"{left} {' '.join(ops_and_comparators)}"
        elif isinstance(node, ast.Call):
            # 处理函数调用
            func_name = self._get_name_from_node(node) or self._node_to_text(node.func)
            args = [self._node_to_text(arg) for arg in node.args]
            kwargs = []
            for kw in node.keywords:
                if kw.arg:
                    kwargs.append(f"{kw.arg}={self._node_to_text(kw.value)}")
                else:
                    kwargs.append(f"**{self._node_to_text(kw.value)}")
            all_args = args + kwargs
            return f"{func_name}({', '.join(all_args)})"
        elif isinstance(node, ast.Attribute):
            # 处理属性访问 obj.attr
            value = self._node_to_text(node.value)
            return f"{value}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            # 处理索引访问 obj[key]
            value = self._node_to_text(node.value)
            slice_text = self._node_to_text(node.slice)
            return f"{value}[{slice_text}]"
        elif isinstance(node, ast.Slice):
            # 处理切片
            lower = self._node_to_text(node.lower) if node.lower else ""
            upper = self._node_to_text(node.upper) if node.upper else ""
            step = self._node_to_text(node.step) if node.step else ""
            if step:
                return f"{lower}:{upper}:{step}"
            else:
                return f"{lower}:{upper}"
        elif isinstance(node, ast.IfExp):
            # 处理三元表达式 x if cond else y
            body = self._node_to_text(node.body)
            test = self._node_to_text(node.test)
            orelse = self._node_to_text(node.orelse)
            return f"{body} if {test} else {orelse}"
        elif isinstance(node, ast.BoolOp):
            # 处理布尔运算 and/or
            values = [self._node_to_text(v) for v in node.values]
            op = " and " if isinstance(node.op, ast.And) else " or "
            return op.join(values)
        else:
            # 对于无法处理的节点，返回占位符
            return f"<{node.__class__.__name__}>"

    def _get_op_symbol(self, op: ast.AST) -> str:
        """获取一元/二元运算符的符号"""
        if isinstance(op, ast.Add):
            return "+"
        elif isinstance(op, ast.Sub):
            return "-"
        elif isinstance(op, ast.Mult):
            return "*"
        elif isinstance(op, ast.Div):
            return "/"
        elif isinstance(op, ast.FloorDiv):
            return "//"
        elif isinstance(op, ast.Mod):
            return "%"
        elif isinstance(op, ast.Pow):
            return "**"
        elif isinstance(op, ast.LShift):
            return "<<"
        elif isinstance(op, ast.RShift):
            return ">>"
        elif isinstance(op, ast.BitOr):
            return "|"
        elif isinstance(op, ast.BitXor):
            return "^"
        elif isinstance(op, ast.BitAnd):
            return "&"
        elif isinstance(op, ast.UAdd):
            return "+"
        elif isinstance(op, ast.USub):
            return "-"
        elif isinstance(op, ast.Not):
            return "not "
        return ""

    def _get_cmp_symbol(self, op: ast.AST) -> str:
        """获取比较运算符的符号"""
        if isinstance(op, ast.Eq):
            return "=="
        elif isinstance(op, ast.NotEq):
            return "!="
        elif isinstance(op, ast.Lt):
            return "<"
        elif isinstance(op, ast.LtE):
            return "<="
        elif isinstance(op, ast.Gt):
            return ">"
        elif isinstance(op, ast.GtE):
            return ">="
        elif isinstance(op, ast.Is):
            return "is"
        elif isinstance(op, ast.IsNot):
            return "is not"
        elif isinstance(op, ast.In):
            return "in"
        elif isinstance(op, ast.NotIn):
            return "not in"
        return ""

    def get_result(self) -> Dict[str, Any]:
        """
        返回解析结果

        Returns:
            包含文件路径、场景和动画步骤的字典
        """
        return self.result


def parse_file(file_path: str, output_format: str = "dict") -> Union[Dict[str, Any], str]:
    """
    解析指定的 Python 文件并输出结果

    Args:
        file_path: 要解析的 Python 文件路径
        output_format: 输出格式，"dict" 返回真正的字典，"json" 返回 JSON 字符串

    Returns:
        解析结果的字典或 JSON 字符串
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # 解析为 AST
        tree = ast.parse(source_code, filename=file_path)

        # 创建解析器并遍历
        parser = ManimSceneParser(file_path)
        parser.visit(tree)

        # 获取结果
        result = parser.get_result()

        # 【核心修复】：如果是 dict，必须返回真正的字典对象！
        if output_format == "json":
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return result  # 绝对不能用 str(result)

    except Exception as e:
        # 【核心修复】：报错时也必须返回字典结构，让主程序能够识别
        error_dict = {"error": f"解析失败: {type(e).__name__} - {str(e)}", "file_path": file_path}
        if output_format == "json":
            return json.dumps(error_dict, ensure_ascii=False)
        else:
            return error_dict


def main():
    """主函数：解析指定的靶标文件"""
    # 本地靶标文件路径
    file_path = "/Users/chenshutong/Desktop/3b1b/videos-master/_2023/clt/main.py"
    result = parse_file(file_path, output_format="json")
    print(result)


if __name__ == "__main__":
    main()
