# Zeta代码编辑预测模型项目全面分析报告

## 项目概述

Zeta是一个基于Qwen2.5-Coder-7B的代码编辑预测模型，专门为Zed编辑器的预测编码功能而设计。该模型能够根据开发者最近的编程模式和光标位置预测下一次代码编辑，实现智能代码补全。

## 1. 训练数据组织结构

### 1.1 数据集分割
项目将数据分为三个主要部分：
- **train.jsonl**: 监督微调(SFT)训练数据
- **eval.jsonl**: 评估数据集
- **dpo.jsonl**: 直接偏好优化(DPO)数据

### 1.2 数据格式结构
每个训练样本包含以下关键字段：

#### 核心字段：
- **events**: 用户在请求代码补全前的编辑历史
- **input**: 用户的原始代码片段，包含光标位置标记
- **output**: 期望的代码补全结果
- **rejected**: (仅DPO数据)被拒绝的补全结果
- **assertions**: (仅评估数据)评估标准

#### 特殊标记：
- `<|editable_region_start|>` / `<|editable_region_end|>`: 标记可编辑区域
- `<|user_cursor_is_here|>`: 标记用户光标位置
- `<|start_of_file|>`: 标记文件开始

### 1.3 数据标签系统
项目使用两类标签对训练数据进行分类，每个训练样本必须从两个类别中各选择一个标签：

#### 类别1 - 编辑位置

**`no-op`: 输入输出相同**
- 特征：模型不需要进行任何修改，输入和输出完全一致
- 示例：用户光标位置不需要任何编辑，代码已经是正确的状态
```ruby
# 输入和输出完全相同，光标位置无需修改
create_table :users do |t|
  t.string   :email,    null: false
    <|user_cursor_is_here|>t.string   :name,     null: false
      t.string   :company,    null: false
        t.datetime   :signed_up_at,    null: false
```

**`local-edit`: 光标附近的编辑**
- 特征：编辑发生在光标位置的直接邻近区域（通常在同一行或相邻几行）
- 示例1：函数实现补全，光标在函数签名后，需要补全函数体
```typescript
// 光标在函数签名后，直接补全函数实现
function findKthLargest<T>(arr: T[], k: number, compareFn: (a: T, b: T) => number): T {<|user_cursor_is_here|>
// 输出：在光标位置直接添加完整的函数实现
function findKthLargest<T>(arr: T[], k: number, compareFn: (a: T, b: T) => number): T {
    if (k < 1 || k > arr.length) throw new Error('Invalid k');
    // ... 完整实现
}
```

- 示例2：变量替换，光标在变量定义后，需要在同一作用域内使用该变量
```rust
// 光标在变量定义后，需要在format!调用中使用该变量
let dir = "/tmp";<|user_cursor_is_here|>
let glob_pattern = format!("{}/**/*.rs", "/tmp");
// 输出：将硬编码字符串替换为变量
let glob_pattern = format!("{}/**/*.rs", dir);
```

**`non-local-edit`: 远离光标的编辑**
- 特征：编辑发生在光标位置较远的地方，通常跨越多行或不同的代码块
- 示例1：模式补全，用户在一个字段添加类型注解，模型推断需要为其他字段也添加相同模式
```typescript
// 光标在name字段的类型注解后，但需要为其他字段也添加undefined类型
interface UserProfileProps {
  name: string | undefined<|user_cursor_is_here|>;
  email: string;        // 需要修改为 string | undefined
  avatar: string;       // 需要修改为 string | undefined
  age: number;          // 需要修改为 number | undefined
}
```

- 示例2：导入语句添加，光标在使用类型的地方，但需要在文件顶部添加导入
```typescript
// 光标在JwtService使用处，但需要在文件顶部添加导入语句
@Injectable()
export class AuthService {
    constructor(
        private jwtService: JwtService<|user_cursor_is_here|>,
    ) {}
// 输出：在文件顶部添加导入语句
import { JwtService } from '@nestjs/jwt';
```

#### 类别2 - 编辑意图

**`add-imports`: 添加导入语句**
- 特征：用户使用了未导入的类型或模块，模型需要添加相应的导入语句
- 示例：TypeScript中使用JwtService但未导入
```typescript
// 用户添加了JwtService类型注解，模型推断需要添加导入
// 输入：private jwtService: JwtService<|user_cursor_is_here|>
// 输出：在文件顶部添加 import { JwtService } from '@nestjs/jwt';
```

**`complete-implementation`: 完成函数/类实现**
- 特征：用户创建了函数签名或类结构，模型需要补全完整的实现逻辑
- 示例：Java中的回文检测算法实现
```java
// 用户创建了空的isPalindrome方法，模型补全完整算法实现
public boolean isPalindrome() {<|user_cursor_is_here|>}
// 输出：完整的双指针回文检测算法实现
```

**`complete-pattern`: 完成模式匹配**
- 特征：用户开始了某种编码模式，模型识别并继续完成相同的模式
- 示例1：为结构体字段添加pub关键字
```rust
// 用户为id字段添加了pub，模型推断为其他字段也添加pub
struct User {
    pub <|user_cursor_is_here|>id: i32,
    username: String,     // 需要添加pub
    email: String,        // 需要添加pub
    // ...
}
```

- 示例2：GraphQL schema中添加非空标记
```graphql
// 用户为title添加了!，模型为其他字段也添加!
type Post {
  title: String!<|user_cursor_is_here|>
  content: String      // 需要改为 String!
  author: User         // 需要改为 User!
  // ...
}
```

**`infer-intent`: 推断用户意图**
- 特征：基于用户的编辑历史和上下文，推断用户的真实意图并进行相应修改
- 示例：变量重命名的连锁反应
```typescript
// 用户将FETCH_DASHBOARD重命名为FETCH_DASHBOARD_DATA
// 模型推断需要在使用该常量的地方也进行相应更新
const FETCH_DASHBOARD_DATA<|user_cursor_is_here|> = gql`...`;
// 在useQuery中也需要更新引用
const { data, loading, error } = useQuery<DashboardData, DashboardVars>(
    FETCH_DASHBOARD_DATA,  // 从FETCH_DASHBOARD更新为FETCH_DASHBOARD_DATA
    { variables: { userId } }
);
```

**`infer-refactor`: 推断重构意图**
- 特征：用户开始重构代码结构，模型推断重构的范围和方式
- 示例：提取变量重构
```javascript
// 用户创建了新变量，模型推断需要将重复的值提取到该变量
let dir = "/tmp";
let glob_pattern = format!("{}/**/*.rs", "/tmp");  // 需要使用dir变量
```

**`unknown`: 未知类型**
- 特征：编辑意图不明确或不属于上述任何类别
- 通常与no-op配对，表示无明确的编辑模式

## 2. 评估数据组织

### 2.1 评估数据特点
- 包含具体的断言(assertions)用于自动化评估
- 每个样本都有明确的评估标准
- 支持多种编程语言(Rust, TypeScript, Python, Java, Go等)

### 2.2 评估样本示例详细解析

#### 完整评估样本示例
```markdown
<events>
User edited file: "src/main.rs":

```diff
@@ -1,3 +1,4 @@
 fn main() {
+    let dir = "/tmp";
     let glob_pattern = format!("{}/**/*.rs", "/tmp");
 }
```
</events>

<input>
```src/main.rs
fn main() {
<|editable_region_start|>
    let dir = "/tmp";<|user_cursor_is_here|>
    let glob_pattern = format!("{}/**/*.rs", "/tmp");
<|editable_region_end|>
}
```
</input>

<output>
```src/main.rs
fn main() {
<|editable_region_start|>
    let dir = "/tmp";
    let glob_pattern = format!("{}/**/*.rs", dir);
<|editable_region_end|>
}
```
</output>

<assertions>
Ensure that the test output replaced the string `\"/tmp\"` with the variable `dir` in the call to `format!`
</assertions>

<labels>
local-edit,infer-intent
</labels>
```

#### Assertion构造详细解析

**1. Assertion设计原理**
该示例中的assertion `"Ensure that the test output replaced the string \"/tmp\" with the variable dir in the call to format!"`是基于以下设计原理构造的：

- **具体性原则**: 明确指出需要检查的具体变化（将字符串"/tmp"替换为变量dir）
- **位置精确性**: 指明变化发生的具体位置（在format!调用中）
- **可验证性**: 提供了明确的验证标准，可以通过字符串匹配来自动验证

**2. Assertion文本描述选择理由**
- **动作导向**: 使用"replaced"明确描述期望的操作类型
- **对象明确**: 具体指出被替换的内容（字符串"/tmp"）和替换目标（变量dir）
- **上下文限定**: 通过"in the call to format!"限定检查范围，避免误判

**3. Assertion验证流程**

**步骤1: 模型输出生成**
```rust
// 模型基于输入生成的输出
let dir = "/tmp";
let glob_pattern = format!("{}/**/*.rs", dir);  // 关键：使用了变量dir而不是字符串"/tmp"
```

**步骤2: Claude API评估**
使用以下prompt模板进行评估：
```
Your task is to help me grade code test output.

Here is the test output:
```
let dir = "/tmp";
let glob_pattern = format!("{}/**/*.rs", dir);
```

Now, help me score the test output using the following criteria:
Ensure that the test output replaced the string "/tmp" with the variable dir in the call to format!

Based on these criteria, give the test output a score between 0.0 and 1.0.
```

**步骤3: 评估逻辑**
Claude会执行以下检查：
1. 在format!调用中查找字符串"/tmp"的使用
2. 确认是否已被变量dir替换
3. 验证替换的正确性和完整性
4. 给出0.0-1.0的评分

**4. Assertion有效性保证机制**

**一致性检查**:
- Assertion与期望输出完全对应：输出确实将"/tmp"替换为了dir
- 评估标准客观明确：可以通过代码分析自动验证
- 避免歧义表述：使用精确的技术术语和具体的代码元素

**准确性验证**:
- 专家审核：确保assertion描述的行为是正确和合理的
- 测试验证：通过多个类似样本验证assertion的一致性
- 边界情况考虑：确保assertion不会对正确的变体产生误判

**5. 从设计到验证的完整流程**

**设计阶段**:
1. 分析用户编辑意图：用户定义了变量dir，意图是为了重用
2. 确定期望行为：应该在后续使用中替换硬编码的相同值
3. 制定验证标准：检查format!调用中的字符串是否被变量替换

**实施阶段**:
1. 编写具体的assertion文本
2. 确保assertion语言清晰、无歧义
3. 验证assertion与期望输出的一致性

**验证阶段**:
1. 使用Claude API进行自动化评估
2. 人工抽查评估结果的准确性
3. 根据反馈调整assertion的表述

这种基于assertion的评估机制确保了模型训练和评估的客观性、一致性和可重复性，是Zeta项目质量保证体系的核心组成部分。

## 3. 评估方法

### 3.1 自动化评估流程
1. **模型推理**: 使用训练好的模型生成代码补全
2. **Claude评分**: 使用Claude-3.5-Sonnet对输出进行评分
3. **评分标准**: 0-5分制，基于assertions中的具体标准
4. **通过阈值**: 通常设置为4分以上为通过

### 3.2 评估指标
- **通过率**: 达到阈值的测试用例百分比
- **平均分数**: 所有测试用例的平均得分
- **详细分析**: 每个测试用例的具体评估反馈

### 3.3 评估脚本
项目在Jupyter notebook中实现了完整的评估流程：
- 批量生成模型输出
- 自动调用Claude API进行评分
- 生成详细的评估报告

## 4. 提示工程(Prompt Engineering)

### 4.1 训练提示模板详细分析

基于项目中的`complete_prompt.md`文件，Zeta使用了精心设计的训练提示模板：

#### 完整训练提示模板
```
You're a code assistant. Your task is to help the user write code by suggesting the next edit for the user.

As an intelligent code assistant, your role is to analyze what the user has been doing and then to suggest the most likely next modification.

## Recent Actions

Here is what the user has been doing:

<events>

## Task

Your task now is to rewrite the code I send you to include an edit the user should make.

Follow the following criteria.

### High-level Guidelines

- Predict logical next changes based on the edit patterns you've observed
- Consider the overall intent and direction of the changes
- Take into account what the user has been doing

### Constraints

- Your edit suggestions **must** be small and self-contained. Example: if there are two statements that logically need to be added together, suggest them together instead of one by one.
- Preserve indentation.
- Do not suggest re-adding code the user has recently deleted
- Do not suggest deleting lines that the user has recently inserted
- Prefer completing what the user just typed over suggesting to delete what they typed

### Best Practices

- Fix any syntax errors or inconsistencies in the code
- Maintain the code style and formatting conventions of the language used in the file
- Add missing import statements or other necessary code. You MUST add these in the right spots
- Add missing syntactic elements, such as closing parentheses or semicolons

- If there are no useful edits to make, return the code unmodified.
- Don't explain the code, just rewrite it to include the next, most probable change.
- Never include this prompt in the response.
```

#### 提示结构组成分析

**1. 角色定义层**
```
You're a code assistant. Your task is to help the user write code by suggesting the next edit for the user.
```
- **明确身份**: 定义AI为代码助手，专注于编辑建议
- **任务聚焦**: 强调"下一个编辑"的预测性质，而非通用代码生成

**2. 能力描述层**
```
As an intelligent code assistant, your role is to analyze what the user has been doing and then to suggest the most likely next modification.
```
- **分析能力**: 强调需要分析用户行为模式
- **预测能力**: 重点在于预测"最可能的"下一步修改
- **上下文感知**: 基于用户历史行为进行推理

**3. 上下文输入层**
```
## Recent Actions
Here is what the user has been doing:
<events>
```
- **历史信息**: 提供用户最近的编辑历史
- **模式识别**: 帮助模型识别用户的编辑模式和意图

**4. 任务指令层**
```
## Task
Your task now is to rewrite the code I send you to include an edit the user should make.
```
- **具体任务**: 明确要求重写代码而非解释
- **编辑导向**: 强调包含用户应该进行的编辑

**5. 指导原则层**
分为三个子层次：

**High-level Guidelines（高层指导）**:
- 基于观察到的编辑模式预测逻辑性的下一步变化
- 考虑变化的整体意图和方向
- 充分考虑用户的历史行为

**Constraints（约束条件）**:
- 编辑建议必须小而自包含
- 保持缩进格式
- 不建议重新添加用户刚删除的代码
- 不建议删除用户刚插入的代码
- 优先完成用户刚输入的内容而非删除

**Best Practices（最佳实践）**:
- 修复语法错误和不一致性
- 维护代码风格和格式约定
- 在正确位置添加缺失的导入语句
- 添加缺失的语法元素

### 4.2 评估提示模板分析

基于项目中的`eval_prompt.md`文件，评估使用了不同的提示策略：

#### 完整评估提示模板
```
Your task is to help me grade code test output.

Here is the test output:

```
<actual>
```

Now, help me score the test output using the following criteria:

<assertions>

Based on these criteria, give the test output a score between 0.0 and 1.0.

- 0.0 means it doesn't meet any of the criteria.
- 1.0 means it meets all criteria.
- If the test output does not contain any of the text I said it "must" include, grade it 0.0.
- First, perform a short, succinct analysis of how the test output meets the criteria.
- On the last line of your response, write the grade as a single, floating-point number. Nothing else.
- **Always** end with a grade. The last line **must** be a floating-point number.
```

#### 评估提示设计特点

**1. 任务明确性**
- 直接说明是评分任务，避免混淆
- 明确输入（测试输出）和输出（0.0-1.0评分）

**2. 评分标准**
- 使用0.0-1.0连续评分而非离散分类
- 提供明确的边界条件（0.0和1.0的含义）
- 设置严格的失败条件（缺少必需文本直接0.0分）

**3. 输出格式控制**
- 要求先分析再评分的结构化输出
- 强制最后一行必须是数字，确保可解析性
- 多次强调格式要求，提高遵循度

### 4.3 训练与评估提示的差异分析

#### 关键差异对比

| 方面 | 训练提示 | 评估提示 |
|------|----------|----------|
| **目标** | 生成代码编辑 | 评估代码质量 |
| **输入** | 用户历史+当前代码 | 模型输出+评估标准 |
| **输出** | 修改后的代码 | 数值评分+分析 |
| **约束** | 编辑规则+格式要求 | 评分标准+输出格式 |
| **上下文** | 用户行为模式 | 客观评估标准 |

#### 设计策略差异

**训练提示策略**:
- **预测导向**: 重点在于预测用户下一步行为
- **模式识别**: 强调从历史行为中学习模式
- **创造性约束**: 在规则框架内进行创造性编辑
- **用户中心**: 以用户意图为核心进行推理

**评估提示策略**:
- **标准导向**: 严格按照预定标准进行评估
- **客观性**: 避免主观判断，基于明确标准
- **格式严格**: 确保输出可被程序解析和处理
- **二元判断**: 虽然是连续评分，但有明确的通过/失败界限

### 4.4 提示工程在训练流程中的关键作用

#### 1. 数据质量控制
- **一致性保证**: 统一的提示确保所有训练样本的处理方式一致
- **质量标准**: 通过约束条件确保生成内容的质量
- **格式规范**: 确保输出符合训练数据的格式要求

#### 2. 模型行为塑造
- **编辑模式**: 训练模型专注于编辑而非从头生成
- **上下文利用**: 教会模型如何有效利用用户历史信息
- **约束遵循**: 培养模型遵循编程规范和用户偏好的能力

#### 3. 评估标准化
- **客观评估**: 提供标准化的评估框架
- **可重复性**: 确保评估结果的一致性和可重复性
- **质量监控**: 为模型性能提供量化的监控指标

#### 4. 持续优化基础
- **反馈循环**: 评估结果为提示优化提供数据支持
- **迭代改进**: 基于评估结果调整训练提示的策略
- **性能提升**: 通过提示工程实现模型性能的持续提升

这种精心设计的提示工程体系是Zeta项目成功的关键因素之一，它不仅确保了训练数据的质量，还为模型的行为塑造和性能评估提供了坚实的基础。

## 5. 模型架构和配置

### 5.1 基础模型
- **基座模型**: Qwen2.5-Coder-7B
- **微调方法**: LoRA (Low-Rank Adaptation)
- **框架**: Unsloth (优化的训练框架)

### 5.2 LoRA配置
- **Rank**: 256 (SFT), 32 (DPO)
- **Alpha**: 等于Rank值
- **目标模块**: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
- **Dropout**: 0 (优化设置)

### 5.3 训练超参数

#### SFT阶段：
- **学习率**: 2e-4
- **批次大小**: 8
- **最大步数**: 60
- **序列长度**: 2048
- **优化器**: adamw_8bit

#### DPO阶段：
- **学习率**: 6e-5
- **批次大小**: 4
- **Beta**: 0.1
- **序列长度**: 4096
- **提示长度**: 2048

## 6. Assertions生成机制详解

### 6.1 Assertions的作用
Assertions是评估数据集中的关键组件，用于：
- **自动化评估**: 为模型输出提供客观的评判标准
- **质量控制**: 确保训练数据的正确性和一致性
- **性能测试**: 验证模型是否满足特定的功能要求

### 6.2 Assertions生成方式

#### 人工编写
大部分assertions是人工编写的，基于以下原则：
- **具体性**: 明确指出期望的代码行为或结构
- **可验证性**: 能够通过自动化方式进行检查
- **完整性**: 覆盖所有重要的功能点

#### 示例分析
从评估数据中可以看到典型的assertions：

**示例1 - 函数实现验证**：
```
Ensure that the quicksort function recurses to the left and to the right of the pivot
```

**示例2 - 变量重命名验证**：
```
Ensure that the test output does not contain the `root_directory` variable anymore and that it has been renamed into dir everywhere
```

**示例3 - 结构体字段可见性**：
```
Ensure that `pixels` is public.
Ensure that `stride` is public.
Ensure that `size` is public.
Ensure that `format` is public.
```

### 6.3 Assertions设计模式

#### 功能完整性检查
- 确保函数实现了所有必要的逻辑
- 验证算法的关键步骤是否存在
- 检查错误处理和边界条件

#### 代码结构验证
- 验证变量名的一致性修改
- 检查访问修饰符的正确应用
- 确保导入语句的正确添加

#### 语法和格式检查
- 验证代码语法的正确性
- 检查代码格式和风格的一致性
- 确保特定语言特性的正确使用

### 6.4 自动化评估流程

评估系统使用Claude API对模型输出进行评分：

```python
def get_score(model_output, assertions):
    prompt = f"""Your task is to help me grade code test output.

Here is the test output:
```
{model_output}
```

Now, help me score the test output using the following criteria:
{assertions}

Based on these criteria, give the test output a score between 0 and 5.
- 0 means: test output doesn't meet any criteria
- 5 means: test output meets all criteria
- If the test output does not contain any of the text I said it "must" include, grade it 0.
- **Always** end with a grade. The last line **must** be a number between 0 and 5."""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    return extract_score(response.content[-1].text)
```

### 6.5 Assertions质量保证

#### 一致性检查
- 确保assertions与期望输出一致
- 验证评估标准的客观性和公平性
- 检查assertions的完整性和准确性

#### 人工审核
- 专家审核assertions的合理性
- 验证评估标准是否符合实际需求
- 确保assertions能够有效区分好坏输出

这种基于assertions的评估机制为Zeta项目提供了客观、可重复的模型性能评估方法，是整个训练和优化流程的重要组成部分。
