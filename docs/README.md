# InlineEdit Recent Changes Benchmark 生成流程

本项目用于为InlineEdit benchmark增强Recent Changes（RC）上下文，模拟真实开发场景中的代码演进过程。

## 📋 项目概述

### 背景
- **原始数据**: 基于ShenYu项目构建的Java代码补全benchmark
- **目标**: 为每条benchmark添加Recent Changes上下文，模拟开发者在实现目标功能前的准备工作
- **方法**: 使用LLM倒推生成3次递进式代码修改（hunks_3 → hunks_2 → hunks_1 → 最终实现）

### 核心理念
- **倒推思维**: 从最终代码状态向前倒推历史修改过程
- **正向演进**: 每个RC都是朝着最终状态的正向补丁
- **真实场景**: 体现开发者的实际思维过程和准备工作

## 🗂️ 项目结构

```
InLineRCRepo/
├── 📁 原始数据
│   └── benchmark/
│       ├── nl2code_java_F10L.jsonl      # 前10条原始数据
│       └── nl2code_java_F20L.jsonl      # 后10条原始数据
├── 📁 GPT-4o生成结果
│   ├── final_gpt4o_output_10/           # 前10条GPT-4o结果
│   └── final_gpt4o_output_20/           # 后10条GPT-4o结果
├── 📁 GPT-5手动结果
│   ├── gpt5_manual_10/                  # 前10条GPT-5结果（已修复）
│   └── gpt5_manual_20/                  # 后10条GPT-5结果
├── 📁 GPT-5原始输入
│   ├── gpt5_result_10/                  # 前10条空文件（供手动填入）
│   └── gpt5_result_20/                  # 后10条空文件（供手动填入）
├── 📄 核心配置
│   ├── instruction.md                   # 完整开发记录
│   ├── RC_prompt_v9_improved.txt        # 最新prompt模板
│   └── README.md                        # 本文件
└── 📁 backup/                           # 历史文件备份
```

## 🚀 完整生成流程

### 步骤1: 准备原始数据
```bash
# 确保benchmark数据存在
ls benchmark/
# nl2code_java_F10L.jsonl  # 前10条
# nl2code_java_F20L.jsonl  # 后10条
```

### 步骤2: 自动生成GPT-4o结果（可选）
如果需要生成新的GPT-4o基准结果：
```python
# 使用最新prompt模板生成
python final_gpt4o_generator.py
```

### 步骤3: 创建GPT-5输入文件
为需要GPT-5处理的数据创建空文件：
```bash
# 为后10条数据创建空文件
mkdir -p gpt5_result_20
cd final_gpt4o_output_20
for file in *.json; do 
  if [[ "$file" != "*summary*" && "$file" != "*progress*" ]]; then 
    basename="${file%.json}"
    touch "../gpt5_result_20/${basename}.txt"
  fi
done
```

### 步骤4: 手动填入GPT-5结果
在`gpt5_result_20/`中的每个`.txt`文件中填入GPT-5的回复：

**输入格式示例**:
```
### hunks\_3 (倒数第三次修改，最早的准备工作)

```json
[
  {
    "file_path": "ClassName.java",
    "start_line": 实际行号,
    "end_line": 实际行号,
    "diff_content": "@@ -行号,数量 +行号,数量 @@\n-删除的行\n+新增的行\n"
  }
]
```

### hunks\_2 (倒数第二次修改，中间准备)
...

### hunks\_1 (最近一次修改，最后的准备工作)
...
```

### 步骤5: 自动合并和验证
运行合并脚本，自动检查diff方向并生成完整结果：
```python
# 创建合并脚本
python merge_gpt5_results.py
```

**脚本功能**:
- ✅ 解析GPT-5结果中的hunks（支持转义符格式）
- ✅ 自动检查diff方向正确性
- ✅ 与GPT-4o模板结构完美合并
- ✅ 生成完整的JSON文件到`gpt5_manual_XX/`

### 步骤6: 项目清理（可选）
清理开发过程中的临时文件：
```python
python cleanup_project.py
```

## 📝 核心Prompt模板

### 当前最优版本: `RC_prompt_v9_improved.txt`

**关键特性**:
- 🔥 **强化diff方向说明**: 多处强调正向演进逻辑
- 🎯 **倒推思维**: 从最终状态向前倒推历史修改
- ✅ **验证机制**: 提供具体的验证方法和标准
- 📏 **精确行号**: 确保diff行号与最终代码完全匹配

**核心理念**:
```
演进路径: 初始版本 → RC3 → RC2 → RC1 → 最终版本
+ 行: 最终版本中存在的内容（目标状态）
- 行: 历史版本中被替换的内容（旧状态）
验证: + 行内容应该能在最终代码的对应行号找到
```

## 📊 输出格式

### 最终生成的JSON结构
每个benchmark文件包含以下结构：
```json
{
  "benchmark_id": "项目名_编号",
  "timestamp": "生成时间",
  "model_used": "gpt-4o-2024-11-20 或 gpt-5-manual",
  "prompt_version": "v9_improved",
  "selected_region": "选中的代码区域（禁止修改）",
  "target_implementation": "目标实现代码（禁止修改）",
  "final_code_with_annotations": "带行号和标注的最终代码",
  "prompt": {
    "system_prompt": "系统提示词",
    "user_prompt": "用户提示词"
  },
  "llm_response": "LLM原始回复",
  "parsed_hunks": {
    "hunks_3": [{"file_path": "...", "start_line": 1, "end_line": 5, "diff_content": "..."}],
    "hunks_2": [{"file_path": "...", "start_line": 10, "end_line": 15, "diff_content": "..."}],
    "hunks_1": [{"file_path": "...", "start_line": 20, "end_line": 25, "diff_content": "..."}]
  },
  "validation_results": {
    "total_issues": 0,
    "total_lines": 100
  },
  "original_benchmark": "原始benchmark数据"
}
```

### Diff格式说明
```diff
# 标准unified diff格式
@@ -起始行,行数 +起始行,行数 @@
 上下文行
-删除的行（历史版本内容）
+新增的行（最终版本内容）
 上下文行
```

## 🎯 质量保证

### 自动验证机制
1. **行号验证**: 确保diff中的行号与最终代码匹配
2. **方向验证**: 检查+/-行的内容是否符合演进逻辑
3. **约束验证**: 确保没有修改禁止区域
4. **格式验证**: 检查JSON格式和diff格式正确性

### 手动检查要点
- ✅ **+ 行内容**: 应该能在最终代码的对应行号找到
- ✅ **- 行内容**: 应该是被替换的历史内容，不在最终代码中
- ✅ **演进逻辑**: RC3 → RC2 → RC1 应该体现合理的开发过程
- ✅ **禁止区域**: 不能修改标注为"禁止修改"的代码部分

## 🔧 API配置

### GPT-4o配置
```bash
Model: gpt-4o-2024-11-20
API Key: sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8
URL: https://api2.aigcbest.top/v1/chat/completions
Temperature: 0.7
```

### 调用示例
```bash
curl https://api2.aigcbest.top/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8' \
  -d '{
    "model": "gpt-4o-2024-11-20",
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."}
    ],
    "temperature": 0.7,
    "max_tokens": 3000
  }'
```

## 🛠️ 实用脚本模板

### 创建空文件脚本
```python
#!/usr/bin/env python3
"""创建GPT-5输入空文件"""
import os

def create_gpt5_input_files(source_dir, target_dir):
    """从source_dir复制文件名到target_dir，创建空的.txt文件"""
    os.makedirs(target_dir, exist_ok=True)

    for file in os.listdir(source_dir):
        if file.endswith('.json') and 'summary' not in file and 'progress' not in file:
            basename = file[:-5]  # 移除.json
            target_file = os.path.join(target_dir, f"{basename}.txt")
            with open(target_file, 'w') as f:
                pass  # 创建空文件
            print(f"创建: {target_file}")

# 使用示例
create_gpt5_input_files('final_gpt4o_output_20', 'gpt5_result_20')
```

### 合并脚本模板
```python
#!/usr/bin/env python3
"""合并GPT-5结果脚本"""
import json
import os
import re
from datetime import datetime

def merge_gpt5_results(gpt5_dir, template_dir, output_dir):
    """合并GPT-5结果与GPT-4o模板"""
    os.makedirs(output_dir, exist_ok=True)

    for txt_file in os.listdir(gpt5_dir):
        if txt_file.endswith('.txt'):
            benchmark_id = txt_file[:-4]

            # 读取GPT-5结果
            with open(os.path.join(gpt5_dir, txt_file), 'r', encoding='utf-8') as f:
                gpt5_content = f.read()

            # 读取GPT-4o模板
            template_file = os.path.join(template_dir, f"{benchmark_id}.json")
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)

            # 解析hunks并合并
            hunks_data = parse_hunks_from_gpt5(gpt5_content)

            merged_data = {
                **template_data,
                'model_used': 'gpt-5-manual',
                'llm_response': gpt5_content,
                'parsed_hunks': hunks_data,
                'timestamp': datetime.now().isoformat()
            }

            # 保存结果
            output_file = os.path.join(output_dir, f"{benchmark_id}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)

            print(f"合并完成: {benchmark_id}")

def parse_hunks_from_gpt5(content):
    """解析GPT-5结果中的hunks"""
    hunks_data = {}
    for hunk_name in ['hunks_3', 'hunks_2', 'hunks_1']:
        pattern = rf'### {hunk_name.replace("_", r"\\_")}.*?```json\s*(.*?)\s*```'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                json_content = match.group(1).strip().replace('\\_', '_')
                hunks_data[hunk_name] = json.loads(json_content)
            except json.JSONDecodeError:
                hunks_data[hunk_name] = []
        else:
            hunks_data[hunk_name] = []
    return hunks_data

# 使用示例
merge_gpt5_results('gpt5_result_20', 'final_gpt4o_output_20', 'gpt5_manual_20')
```

## 📚 参考资料

### 相关文档
- `instruction.md`: 完整的开发过程记录
- `RC_prompt_v9_improved.txt`: 最新的prompt模板
- `backup/`: 历史版本和开发过程文件

### 常见问题
1. **Q: diff方向错误怎么办？**
   A: 检查+行内容是否在最终代码中存在，-行内容是否是历史版本

2. **Q: 行号不匹配怎么办？**
   A: 确保diff中的行号与最终代码的实际行号完全一致

3. **Q: hunks解析失败怎么办？**
   A: 检查JSON格式是否正确，注意转义符处理

### 版本历史
- **v9_improved**: 当前最优版本，强化diff方向说明
- **v8**: 支持GPT-5格式，基础diff验证
- **v7**: 初始稳定版本，基础功能完整

---

*最后更新: 2025-09-17*
*项目状态: 生产就绪，包含20条完整benchmark数据*
