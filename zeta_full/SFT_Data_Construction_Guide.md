# 智能补全/编辑 SFT 数据构造技术方案（通用方法论）
**版本**：v1.0  
**最后更新**：2025-09-28  
**适用范围**：从包含 *old/new 源码、diff 片段、评审行与评审意见* 的原始数据，构造**序列到序列（SFT）**训练样本，用于代码**智能补全 / 下一步编辑**场景。  
**强调**：本文是**方法论与操作步骤**，不包含代码实现。

---


## 0. 术语与目标
- **SFT（Supervised Fine-Tuning）**：以*输入 prompt* → *目标 completion* 的监督学习样本训练模型。
- **下一步编辑**：在“最近编辑/评审”语境下，对**方法级或注解块级**代码进行**小粒度、自洽**的编辑建议或直接重写。
- **输入原始字段（示例）**：`mrcr_url, file_path, code_type, old_file, new_file, old_hunk, new_hunk, review_line, review_message, code_with_line, start_line, end_line, commit_id...`

**目标产物（SFT JSONL）**：
- **最小必需**：`{ "prompt": <字符串>, "completion": <字符串> }`
- **推荐扩展**（便于分析/抽样/回溯）：`id, file_path, lang, meta, history, before, after, focus_line, edit_span, labels, spans, notes` 等。

---

## 1. 输出数据 Schema（通用、与具体模型解耦）

### 1.1 最小 Schema（直接可用于 SFT）
每行 JSONL：
```json
{
  "prompt": "<INSTRUCTION + CONTEXT + TASK + BEFORE + FOCUS/EDIT HINTS>",
  "completion": "<AFTER 或 仅编辑区的新内容>"
}
```
> 适用于绝大多数指令微调框架；**prompt** 尽量自解释，避免模型外部依赖。

### 1.2 推荐扩展 Schema（便于质控/统计/误差分析）
```json
{
  "id": "...",
  "file_path": "...",
  "lang": "java",
  "meta": {"mrcr_url": "...", "old_commit_id": "...", "new_commit_id": "..."},
  "history": "<一句话摘要 + 精简diff>",
  "before": "<方法级/注解块级 变更前代码片段>",
  "after": "<方法级/注解块级 变更后代码片段（训练目标）>",
  "focus_line": 37,
  "edit_span": [37, 43],
  "labels": {"position": "local-edit", "intent": "infer-intent", "flags": ["needs-import-fix"]},
  "spans": {
    "scope": {"type": "method"|"class-annotations"|"imports", "start_line": X, "end_line": Y},
    "imports": [{"start_line": I1, "end_line": I2 }]
  },
  "prompt": "<最终用于训练的 prompt 字符串>",
  "completion": "<用于训练的 completion 字符串>"
}
```
> **before/after 与 prompt/completion**可冗余保留，便于离线对齐与人工抽检。

---

## 2. 统一的样本“单元”与范围原则
- **样本最小单元**：**方法体**或**类注解块**；必要时增加一个**imports 子区域**（仅与本次改动直接相关）。
- **范围控制**：覆盖所有改动 + 使编辑“自洽”的最小上下文；优先不跨越不相关方法/类；窗口长度尽量控制在**几十行**。

---

## 3. 管道总览（从原始 → SFT）
1) **归一化与解析**：
   - 优先使用 `old_hunk/new_hunk`；如缺失，基于 `old_file/new_file` 计算**最小 diff**；生成**变更块列表**。
2) **样本单元定位**：
   - 解析方法/类与注解边界（失败退回“变更最小包围 + 上下K行”）；确定**主区域**（method / class-annotations）。
   - 若需 import 调整，标记**imports 子区域**（顶部 import 段中最小相关行集）。
3) **关注点（光标）推断**：
   - 首选 `review_line`；若偏离主变更过远（>10行或跨语义块），则回退到**第一处实际变更行**。
   - 注解类问题：光标＝注解组末行（最靠近类声明的注解行）。方法类问题：光标＝关键逻辑附近（if/return/call 等）。
4) **可编辑区域确定**：
   - 主区域＝方法体或注解块；imports 作为子区域（可同样本处理或拆子样本）。
5) **编辑历史构造（history）**：
   - **一句话摘要** + **精简 diff**（仅展示与主/子区域相关的加减行）。
6) **构造 prompt / completion**：
   - Prompt = 角色/约束 + history + before + 位置提示（focus_line 与编辑范围说明） + “仅重写该片段”的任务指令。
   - Completion = after（两种形态：①整片段重写；②仅编辑区新内容）。
7) **去重与过滤**：
   - 去除无语义改动（空白/注释）；合并重复/等价样本；控制过长样本。
8) **质控与验收**：
   - 结构校验、语义对齐、长度预算、标签一致性、人工抽检通过率。
9) **序列化与落盘**：
   - 输出 JSONL；train/eval 划分按 MR/方法隔离（避免泄漏）；记录统计。

---

## 4. 关键决策逻辑（详细）

### 4.1 关注点（光标）推断
- **优先**：`review_line`；若该行是注解组中的一行，则以**注解组末行**作为编辑落点；若在方法体内，则以**最近的可执行语句**为落点（优先回退1–2行）。
- **回退**：若 `review_line` 距主变更>10行或跨语义块，则落在**第一处主变更行**。
- **多点**：若同方法内多处改动，选择**与评审最相关的一处**作为落点（其余在编辑区域内由模型完成）。

### 4.2 可编辑区域确定
- **方法问题**：区域 = **整个方法体**（签名至右花括号），确保编辑自洽（局部声明/return/异常等）。
- **类注解问题**：区域 = **注解块 + 紧邻类声明行**；严禁扩展至不相关字段/方法。
- **imports 子区域**：如注解/逻辑变化引入/移除依赖（如 `@Data` → `@Getter/@Setter`、`StringUtils.isBlank`），将 import 相关的**最小行集**标为子区域（可同条样本或拆子样本）。
- **长度**：优先不超过**100行**；超限则缩小到“最小自洽上下文”。

### 4.3 编辑历史（Events / history）
- **一句话摘要**：描述“这轮改动要做什么/刚做了什么”（面向策略/规范/功能）。
- **精简 diff**：仅展示**主区域**相关加减行；imports 改动以“合并说明 + 简短增删”表达；避免贴整文件。

### 4.4 标签（非必需但强烈建议）
- **位置 position**：
  - `local-edit`：关注点与主变更在同块且行距≤2；
  - `non-local-edit`：行距大或跨块；
  - `no-op`：仅格式/注释。
- **意图 intent**：
  - `infer-intent`（策略/规范修正：如 `@Data→@Getter/@Setter`、`null→blank`）；
  - `add-imports`（为现改动补/清理 import）；
  - `complete-implementation`（补齐必要语句/注解/返回/异常）；
  - `complete-pattern`（一致性批量修改）；
  - `infer-refactor`（结构重构）；
  - `unknown`。

---

## 5. Prompt 设计（通用，可直接用于 SFT）
> 仅模板，不绑定任一模型特定 token；**两种 completion 形态**任选其一保持一致。

### 5.1 Baseline Prompt（整片段重写式）
```
You are an intelligent code editor for next-edit prediction.
Analyze the recent edits and rewrite ONLY the given slice accordingly.

# Recent edits
{history}

# Scope
- File: {file_path}
- Language: {lang}
- Focus line: {focus_line}
- Editable region: {scope_desc}  (e.g., method body 'updateUserNickName', or class annotations)

# Constraints
- Keep edits small and self-contained.
- Preserve indentation and style.
- Do not revert unrelated changes.
- Prefer completing the current intent (e.g., policy fix, consistency, imports).

# Before (slice)
<code>
{before}
</code>

# Task
Rewrite the slice so that it reflects the correct next edit implied by the recent edits and constraints.
Return ONLY the rewritten slice.
```

**Completion（对应）**：`after` **同范围**的完整重写。

### 5.2 Baseline Prompt（仅编辑区填充式）
```
... (同上省略到 Before)

# Editable region
- Start line: {edit_span[0]}, End line: {edit_span[1]}

# Task
Return ONLY the new content for the editable region (no extra lines).
```
**Completion（对应）**：**仅**编辑区的新内容（便于 IDE 原位应用）。

> 同一数据集**统一一种形态**，避免训练目标混杂。

---

## 6. 案例示范（精简）

### 6.1 案例 1：@Data → @Getter/@Setter（注解 + imports）
- **focus_line**：指向注解组末行（靠近 `class`）。
- **主区域**：类注解块 + 类声明行；**子区域**：与注解相关的 `import lombok.Data;` 清理（如存在）。
- **history 摘要**：`Replace Lombok @Data with @Getter and @Setter; remove unused 'import lombok.Data;'; add @JsonProperty on fields.`
- **prompt**：按 5.1 模板填入 `history/before/focus_line/scope_desc`。
- **completion**：输出带 `@Getter/@Setter` 的注解块与类声明；（若采用整片段重写）保留字段与 `@JsonProperty`。

### 6.2 案例 2：null→blank 策略修正（方法内逻辑 + 可选 import）
- **focus_line**：方法体关键判定附近（`review_line`）。
- **主区域**：`updateUserNickName()` 方法体；**子区域**：`StringUtils` import（如需）。
- **history 摘要**：`Remove null-only guard and direct set; apply blank-policy using StringUtils.isBlank; do not set when blank.`
- **prompt/completion**：同 5.1/5.2；重写该方法体或仅返回编辑区的新内容。

---

## 7. 质控（QC）与验收门槛

### 7.1 结构校验
- 必有：`prompt, completion`；推荐：`file_path, lang, before, after, history, focus_line, edit_span`。
- `before/after` **范围一致**；`focus_line` 位于 `before` 范围内；`edit_span` 合法且覆盖主变更。
- 长度预算：单条样本总 tokens 不超过预设阈值（例如 2k-4k tokens）。

### 7.2 语义对齐
- **history 能解释** `before→completion/after` 的主要变化；
- **completion 自洽**（编译/解析合理，缩进风格一致）；
- 若存在 imports 子区域，**与主改动强相关**，避免引入不必要噪声。

### 7.3 标签一致性（如使用标签）
- `position` 由关注点与主变更距离计算一致；
- `intent` 与 `review_message/history` 的主旨一致（策略/规范优先）。

### 7.4 抽检与评分
- 抽检通过率≥95%（结构与语义）；
- 关键错误（错误范围、错位落点、语义不达）为硬性拒收项；
- 记录失败样本类型（方法解析失败/跨块扩张/断言歧义），回流规则。

---

## 8. 划分与采样（仅 SFT 视角）
- **数据切分**：以 **MR/Commit/方法** 为单元隔离 train / eval，防止信息泄漏；
- **分层采样**：按语言、位置、意图保持大致平衡，避免偏科；
- **去重**：去掉等价或高度相似的样本（相同 before+history）。

---

## 9. 可移植性与落地建议
- **与模型解耦**：本文不依赖特定占位符或格式——prompt 全自解释，适配任何指令微调框架；如需 IDE 级 infill，可在推理时把 `edit_span` 映射为占位符。
- **与评测解耦**：评测（assertions/规则/LLM 打分）单独成文，不影响 SFT 训练集形态。
- **小步快跑**：先用“方法体整片段重写”形态出第一版；数据量达到几千条后，再考虑“仅编辑区填充”的第二版，以便贴近工程接入。

---

## 10. 附录：意图标签清单（参考）
- `infer-intent`：策略/规范修正（@Data→@Getter/@Setter、null→blank、重命名连锁修复等）
- `add-imports`：为当前改动新增/清理 import
- `complete-implementation`：补 return/if/try-catch/序列化注解等
- `complete-pattern`：批量一致性修改（多字段加注解/修饰符）
- `infer-refactor`：抽取方法、移动代码、合并重复
- `unknown`：其他
