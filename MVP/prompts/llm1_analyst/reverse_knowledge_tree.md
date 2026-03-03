
# 逆向知识树算法

逆向知识树是一项核心创新，它在生成教学动画时**无需训练数据**。

## 核心理念

传统方法需要基于示例动画进行训练。
而本系统采用**纯推理**方式：

**对任意概念 X，递归追问：「在理解 X 之前，我必须先掌握什么？」**

由此构建出一张**知识依赖有向无环图（DAG）**，可自然生成符合教学逻辑的内容。

---

## 算法细节

### 数据结构：KnowledgeNode（知识节点）

```python
@dataclass
class KnowledgeNode:
    concept: str           # 概念名称
    depth: int             # 0 = 目标概念，数值越大表示越基础
    is_foundation: bool    # 是否为基础概念（无需再拆解前提）
    prerequisites: List['KnowledgeNode']  # 子节点（前置知识）

    # 由内容增强模块补充
    equations: Optional[List[str]]        # LaTeX 公式
    definitions: Optional[Dict[str, str]] # 变量定义
    narrative: Optional[str]              # 场景描述文本
```

### 探索过程

```python
async def explore(concept: str, depth: int = 0) -> KnowledgeNode:
    # 检查终止条件
    if depth >= max_depth or is_foundation(concept):
        return KnowledgeNode(
            concept=concept,
            depth=depth,
            is_foundation=True,
            prerequisites=[]
        )

    # 通过大模型发现前置知识
    prerequisites = await discover_prerequisites(concept)

    # 递归探索每一个前置知识
    child_nodes = []
    for prereq in prerequisites:
        child_nodes.append(await explore(prereq, depth + 1))

    return KnowledgeNode(
        concept=concept,
        depth=depth,
        is_foundation=False,
        prerequisites=child_nodes
    )
```

### 基础概念判定

如果一个概念**高中毕业生无需额外解释即可理解**，则视为基础概念。

**基础概念示例：**

- 速度、距离、时间、加速度
- 力、质量、能量
- 波、频率、波长
- 数字、加法、乘法
- 基础几何（点、线、角）
- 函数、图像

**非基础概念示例：**

- 洛伦兹变换
- 规范场论
- 微分几何
- 张量微积分
- 量子算符
- 希尔伯特空间

### 前置知识发现提示词

```
你是一名资深教育专家与课程设计师。

你的任务是：找出学习者在**理解某一概念之前，必须掌握的核心前置概念**。

规则：
1. 只列出**理解该概念所必需**的概念（而非仅仅有帮助）
2. 按重要性从高到低排序
3. 以高中知识水平为基准
4. 聚焦**有助于理解**的概念，而非历史背景
5. 表述具体——优先使用「狭义相对论」而非「相对论」
6. 每个概念最多列出 3–5 个前置知识

仅返回 JSON 数组格式的概念名称。
```

---

## 缓存策略

为避免重复调用大模型 API：

1. **内存缓存**：按概念名存储已发现的前置知识
2. **可选 Atlas 集成**：使用 Nomic Atlas 实现语义化缓存与检索

```python
async def lookup_prerequisites(concept: str) -> List[str]:
    # 先查缓存
    if concept in cache:
        return cache[concept]

    # 若启用 Atlas，则查询 Atlas
    if atlas_client:
        results = atlas_client.search_similar(concept)
        if exact_match_found(results):
            return results[0].prerequisites

    # 通过大模型发现前置知识
    prerequisites = await discover_prerequisites(concept)

    # 存入缓存
    cache[concept] = prerequisites
    if atlas_client:
        atlas_client.store(concept, prerequisites)

    return prerequisites
```

---

## 用于动画生成的树遍历

构建知识树后，**从叶子节点（基础概念）遍历到根节点（目标概念）**：

### 拓扑排序

```python
def topological_sort(root: KnowledgeNode) -> List[KnowledgeNode]:
    visited = set()
    result = []

    def dfs(node):
        if node.concept in visited:
            return
        visited.add(node.concept)

        # 先访问前置知识（基础概念）
        for prereq in node.prerequisites:
            dfs(prereq)

        # 再将当前节点加入结果
        result.append(node)

    dfs(root)
    return result  # 顺序：基础概念 → 目标概念
```

该排序保证：

- 基础概念在动画中**最先出现**
- 每个概念都建立在**已讲解内容**之上
- 观众在接触高阶知识点前，已具备必要背景

---

## 配置项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_depth` | 4 | 最大树深度，超过则强制视为基础概念 |
| `max_prerequisites` | 5 | 每个概念最多前置知识数量 |
| `cache_enabled` | True | 是否启用内存缓存 |
| `atlas_enabled` | False | 是否使用 Nomic Atlas 持久化缓存 |

---

## 示例树

**输入**：「解释量子隧穿」

**生成的知识树**：

```
量子隧穿（深度 0）
├─ 波粒二象性（深度 1）
│   ├─ 德布罗意波长（深度 2）[基础概念]
│   └─ 海森堡不确定性原理（深度 2）
│       └─ 波函数（深度 3）[基础概念]
├─ 薛定谔方程（深度 1）
│   ├─ 波函数（深度 2）[基础概念]
│   └─ 势能（深度 2）[基础概念]
└─ 势垒（深度 1）[基础概念]
```

**动画播放顺序**（拓扑排序后）：

1. 德布罗意波长
2. 波函数
3. 海森堡不确定性原理
4. 波粒二象性
5. 势能
6. 势垒
7. 薛定谔方程
8. 量子隧穿

每个概念都建立在前序内容之上，形成**自然、连贯的学习流程**。
