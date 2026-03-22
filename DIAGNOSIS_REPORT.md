# Manim 数据集流水线 - 系统环境与 API 配置诊断报告

生成时间：2026-03-18

---

## ✅ 任务 1：标杆项目 API 配置提取

### 🔑 API 配置信息（来自 Manim_Dataset_Test/.env）

```env
OPENAI_API_KEY=sk-user-97c98375ba5e50336c7b24a0
OPENAI_BASE_URL=https://api.tabcode.cc/openai
OPENAI_MODEL=gpt-5.4
```

### 📋 配置说明

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **OPENAI_API_KEY** | `sk-user-97c98375ba5e50336c7b24a0` | API 密钥 |
| **OPENAI_BASE_URL** | `https://api.tabcode.cc/openai` | **关键：完整的 API 端点 URL |
| **OPENAI_MODEL** | `gpt-5.4` | 使用的模型名称 |

### ⚠️ 当前 3b1b/.env 配置验证

当前 3b1b 项目的 `.env` 文件配置与标杆项目**完全一致**：
- ✅ OPENAI_API_KEY 匹配
- ✅ OPENAI_BASE_URL 匹配
- ✅ OPENAI_MODEL 匹配

---

## ✅ 任务 2：当前工作区目录树

### 📁 完整目录结构（3 层）

```
/Users/chenshutong/Desktop/3b1b/
│
├── ⭐ extracted_core/              ← 3b1b 核心类提取结果（AST 自动提取）
│   ├── 📂 animation/              ← 动画类（50 个文件：.md + .py）
│   │   ├── Transform.md & Transform.py
│   │   ├── ApplyFunction.md & ApplyFunction.py
│   │   ├── Write.md & Write.py
│   │   ├── ShowCreation.md & ShowCreation.py
│   │   └── ...
│   │
│   └── 📂 mobject/                ← 图形对象类（82 个文件：.md + .py）
│       ├── Axes.md & Axes.py
│       ├── NumberPlane.md & NumberPlane.py
│       ├── FunctionGraph.md & FunctionGraph.py
│       ├── VectorField.md & VectorField.py
│       ├── Line.md & Line.py
│       ├── Circle.md & Circle.py
│       ├── Rectangle.md & Rectangle.py
│       ├── Dot.md & Dot.py
│       ├── Polygon.md & Polygon.py
│       └── ...
│
├── ⭐ scripts/                    ← 脚本工具集
│   └── 📄 batch_washing_pipeline.py  ← 批量洗稿脚本（已更新）
│
├── ⭐ washed_manim_components/      ← AI 批量清洗后的标准化组件
│   ├── 📄 ERROR_Axes.txt          ← 洗稿失败标记
│   ├── 📄 ERROR_VectorField.txt
│   ├── 📄 ERROR_FunctionGraph.txt
│   └── ... (25 个 ERROR 文件，表示之前的洗稿都失败了）
│
├── ⭐ reconstructed_core/          ← 手工重构的核心类
│   ├── 📄 Vector.py              ← 已重构的向量类（标杆）
│   ├── 📄 test_vector.py
│   └── 📄 test_vector_capture.py
│
├── ⭐ videos-master/               ← 3b1b 原始视频代码仓库（只读参考）
│   ├── 📂 _2015/ ~ _2026/      ← 按年份组织的视频场景
│   ├── 📂 custom/
│   ├── 📂 once_useful_constructs/
│   └── 📄 CLAUDE.md
│
├── 📄 extract_manim_core.py         ← AST 提取脚本（已运行）
├── 📄 test_vector_capture.py         ← 集成测试脚本
└── 📄 .env                        ← API 配置文件
```

### 📍 重点目录验证

| 目录 | 路径 | 状态 | 说明 |
|------|--------|------|------|
| **extracted_core/** | `extracted_core/` | ✅ 存在 | 包含 mobject/ 和 animation/ 子目录 |
| **extracted_core/mobject/** | `extracted_core/mobject/` | ✅ 存在 | 40 个类（.md + .py） |
| **extracted_core/animation/** | `extracted_core/animation/` | ✅ 存在 | 25 个类（.md + .py） |
| **scripts/** | `scripts/` | ✅ 存在 | 包含 batch_washing_pipeline.py |
| **washed_manim_components/** | `washed_manim_components/` | ✅ 存在 | 包含 25 个 ERROR 文件 |
| **.env** | `.env` | ✅ 存在 | API 配置正确 |
| **reconstructed_core/** | `reconstructed_core/` | ✅ 存在 | 手工重构的 Vector 类 |

---

## 🔍 问题诊断

### ❌ 洗稿失败分析

`washed_manim_components/` 目录下有 25 个 `ERROR_*.txt` 文件，说明之前的洗稿**全部失败**。

可能原因：
1. **API 连接问题**：虽然 .env 配置正确，但 API 可能返回 404 错误
2. **模型名称问题**：`gpt-5.4` 可能不是有效的模型名
3. **网络连接问题**：无法访问 `https://api.tabcode.cc/openai`

### 🔧 建议修复步骤

1. **验证 API 连接**：
   ```bash
   curl -X POST https://api.tabcode.cc/openai/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-user-97c98375ba5e50336c7b24a0" \
     -d '{"model": "gpt-5.4", "messages": [{"role": "user", "content": "test"}]}'
   ```

2. **验证模型名称**：
   - 检查 `gpt-5.4` 是否为有效模型
   - 尝试更标准的模型名，如 `gpt-4`、`gpt-3.5-turbo`

3. **更新 .env 文件**（如果需要）：
   ```env
   OPENAI_API_KEY=sk-user-97c98375ba5e50336c7b24a0
   OPENAI_BASE_URL=https://api.tabcode.cc/openai
   OPENAI_MODEL=gpt-4  # 尝试更标准的模型名
   ```

4. **重新运行洗稿脚本**：
   ```bash
   cd /Users/chenshutong/Desktop/3b1b
   python scripts/batch_washing_pipeline.py
   ```

---

## 📊 下一步行动

- [ ] 验证 API 连接是否正常
- [ ] 确认模型名称有效性
- [ ] 清理 washed_manim_components/ 中的 ERROR 文件
- [ ] 重新运行批量洗稿脚本
- [ ] 验证生成的 Washed_*.py 文件质量
