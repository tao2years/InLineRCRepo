#!/usr/bin/env python3
"""
端到端自动化处理器 - 为新增benchmark数据生成完整的处理流程
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List
import re

# 导入配置
from config import *

class EndToEndProcessor:
    def __init__(self):
        self.processed_count = 0
        self.failed_count = 0
        self.failed_items = []
        
    def load_benchmark_data(self) -> List[Dict[str, Any]]:
        """加载benchmark数据"""
        print(f"📖 加载benchmark数据: {INPUT_BENCHMARK_FILE}")
        
        if not os.path.exists(INPUT_BENCHMARK_FILE):
            raise FileNotFoundError(f"输入文件不存在: {INPUT_BENCHMARK_FILE}")
            
        data = []
        with open(INPUT_BENCHMARK_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        data.append(item)
                    except json.JSONDecodeError as e:
                        print(f"⚠️  第{line_num}行JSON解析失败: {e}")
                        
        print(f"✅ 成功加载 {len(data)} 条数据")
        return data
        
    def extract_benchmark_id(self, item: Dict[str, Any]) -> str:
        """从benchmark数据中提取ID"""
        # 尝试从extra_content中获取ID
        if 'extra_content' in item and 'id' in item['extra_content']:
            return item['extra_content']['id']
            
        # 尝试从id字段获取
        if 'id' in item:
            return item['id']
            
        # 尝试从domain和其他信息构造ID
        if 'domain' in item:
            domain = item['domain']
            # 从prompt中尝试提取特征信息构造ID
            prompt = item.get('prompt', '')
            # 这里可以根据实际情况调整ID提取逻辑
            return f"{domain}_item_{self.processed_count + 1}"
            
        # 默认ID
        return f"benchmark_item_{self.processed_count + 1}"
        
    def load_rc_prompt_template(self) -> str:
        """加载RC生成的prompt模板"""
        if not os.path.exists(RC_PROMPT_TEMPLATE):
            print(f"⚠️  RC prompt模板不存在: {RC_PROMPT_TEMPLATE}")
            return ""
            
        with open(RC_PROMPT_TEMPLATE, 'r', encoding='utf-8') as f:
            return f.read()
            
    def extract_code_info(self, item: Dict[str, Any]) -> Dict[str, str]:
        """从benchmark数据中提取代码相关信息"""
        prompt = item.get('prompt', '')
        
        # 提取选中的代码区域
        selected_region = ""
        if 'And here is the code snippet you are asked to modify:' in prompt:
            start = prompt.find('And here is the code snippet you are asked to modify:')
            end = prompt.find('Please analyze the mission carefully')
            if end == -1:
                end = len(prompt)
            selected_section = prompt[start:end]
            
            # 提取代码块
            code_match = re.search(r'```java\n(.*?)\n```', selected_section, re.DOTALL)
            if code_match:
                selected_region = code_match.group(1).strip()
                
        # 提取目标实现（从good_example_response）
        target_implementation = ""
        if 'good_example_response' in item:
            response = item['good_example_response']
            code_match = re.search(r'```java\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                target_implementation = code_match.group(1).strip()
                
        # 提取完整代码（从context above和below拼接）
        final_code = self.reconstruct_full_code(prompt, target_implementation)
        
        return {
            'selected_region': selected_region,
            'target_implementation': target_implementation,
            'final_code_with_annotations': final_code
        }
        
    def reconstruct_full_code(self, prompt: str, target_implementation: str) -> str:
        """重构完整代码，包含行号标注"""
        # 提取context above
        context_above = ""
        if 'The context above is:' in prompt:
            start = prompt.find('The context above is:')
            end = prompt.find('The context below is:')
            if end != -1:
                context_section = prompt[start:end]
                code_match = re.search(r'```java\n(.*?)\n```', context_section, re.DOTALL)
                if code_match:
                    context_above = code_match.group(1).strip()

        # 提取context below
        context_below = ""
        if 'The context below is:' in prompt:
            start = prompt.find('The context below is:')
            end = prompt.find('The new feature is')
            if end == -1:
                end = len(prompt)
            context_section = prompt[start:end]
            code_match = re.search(r'```java\n(.*?)\n```', context_section, re.DOTALL)
            if code_match:
                context_below = code_match.group(1).strip()

        # 拼接完整代码
        full_code_lines = []

        # 添加context above
        if context_above:
            for line in context_above.split('\n'):
                full_code_lines.append(line)

        # 添加目标实现（标注为禁止修改）
        if target_implementation:
            for line in target_implementation.split('\n'):
                if line.strip():
                    full_code_lines.append(f"{line} // [禁止修改-目标实现]")
                else:
                    full_code_lines.append(line)

        # 添加context below
        if context_below:
            for line in context_below.split('\n'):
                full_code_lines.append(line)

        # 添加行号
        numbered_lines = []
        for i, line in enumerate(full_code_lines, 1):
            if line.strip():
                numbered_lines.append(f"{i:3d}: {line}")
            else:
                numbered_lines.append(f"{i:3d}: ")

        return '\n'.join(numbered_lines)

    def generate_rc_prompts(self, code_info: Dict[str, str]) -> Dict[str, str]:
        """生成RC相关的prompt"""
        rc_template = self.load_rc_prompt_template()

        # 构造system prompt
        system_prompt = rc_template if rc_template else """你是资深 Java 工程师。现在给你一个完整的代码文件（最终状态），你需要**倒推**出为了达到这个最终状态而**刚刚**做过的3次递进式代码修改（Recent Changes）。

核心逻辑：
- 给出的代码是最终完整状态，每行都有行号标注
- 你需要倒推出3个历史版本的修改过程
- 演进路径：初始版本 → RC3 → RC2 → RC1 → 当前最终版本
- **关键**：不要在最终状态基础上再做修改，而是倒推出达到最终状态的历史修改过程"""

        # 构造user prompt
        user_prompt = f"""[SELECTED_REGION] - 禁止修改
选中的代码区域（不可修改）：
{code_info['selected_region']}

[TARGET_IMPLEMENTATION] - 禁止修改
目标实现代码（不可修改）：
{code_info['target_implementation']}

[FINAL_CODE_WITH_LINE_NUMBERS] - 最终状态（带行号和标注）
以下是最终完整代码状态，每行都有行号标注，并标注了禁止修改的区域：
{code_info['final_code_with_annotations']}

[RC_CONSTRAINTS]
Recent Changes约束：
1. 只能修改未标注为"禁止修改"的代码部分
2. 每个RC都应该为实现TARGET_IMPLEMENTATION做准备工作
3. 使用精确的行号定位和标准diff格式
4. RC应该体现真实的开发演进过程
5. **关键**：diff中的行号必须与上面给出的最终代码行号完全一致
6. **倒推思维**：从最终状态倒推历史修改，不是在最终状态上继续开发

[INTENT]
请倒推出为了实现TARGET_IMPLEMENTATION，开发者做过的3次递进式准备工作：
- hunks_3: 倒数第三次修改（最早的准备工作）
- hunks_2: 倒数第二次修改（中间准备）
- hunks_1: 最近一次修改（最后的准备工作）

每次修改都应该：
1. 基于精确的行号定位（与最终代码行号完全一致）
2. 使用标准的unified diff格式
3. 为实现TARGET_IMPLEMENTATION做必要准备
4. 体现真实的开发思维过程
5. **验证**：确保diff中的行号与最终代码中的实际行号匹配
6. **倒推验证**：确保是从最终状态向前倒推的修改过程

[RETURN FORMAT]
### hunks_3 (倒数第三次修改，最早的准备工作)
```json
[
    {{
        "file_path": "ClassName.java",
        "start_line": 实际行号,
        "end_line": 实际行号,
        "diff_content": "@@ -实际行号,行数 +实际行号,行数 @@\\\\n 上下文行\\\\n-删除的行\\\\n+新增的行\\\\n 上下文行"
    }}
]
```

### hunks_2 (倒数第二次修改，中间准备)
```json
[
    {{
        "file_path": "ClassName.java",
        "start_line": 实际行号,
        "end_line": 实际行号,
        "diff_content": "@@ -实际行号,行数 +实际行号,行数 @@\\\\n 上下文行\\\\n-删除的行\\\\n+新增的行\\\\n 上下文行"
    }}
]
```

### hunks_1 (最近一次修改，最后的准备工作)
```json
[
    {{
        "file_path": "ClassName.java",
        "start_line": 实际行号,
        "end_line": 实际行号,
        "diff_content": "@@ -实际行号,行数 +实际行号,行数 @@\\\\n 上下文行\\\\n-删除的行\\\\n+新增的行\\\\n 上下文行"
    }}
]
```

### notes
简要说明这3次准备工作如何为实现TARGET_IMPLEMENTATION做准备，体现倒推的逻辑思维"""

        return {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt
        }

    def create_output_structure(self, item: Dict[str, Any], benchmark_id: str) -> Dict[str, Any]:
        """创建输出文件结构"""
        code_info = self.extract_code_info(item)
        prompts = self.generate_rc_prompts(code_info)

        # 构造输出结构
        output_data = {
            "benchmark_id": benchmark_id,
            "timestamp": datetime.now().isoformat(),
            "model_used": MODEL_NAME,
            "prompt_version": "v9_improved",  # 添加prompt版本
            "selected_region": code_info['selected_region'],
            "target_implementation": code_info['target_implementation'],
            "final_code_with_annotations": code_info['final_code_with_annotations'],
            "prompt": prompts,
            # 留空的字段
            "llm_response": "",
            "parsed_hunks": {},
            "validation_results": {},  # 添加验证结果字段
            "usage": {},  # 添加使用情况字段
            # 添加原始benchmark数据
            "original_benchmark": item
        }

        return output_data

    def create_directories(self):
        """创建必要的目录"""
        # 创建输出目录
        if not os.path.exists(OUTPUT_FOLDER_NAME):
            os.makedirs(OUTPUT_FOLDER_NAME)
            print(f"📁 创建输出目录: {OUTPUT_FOLDER_NAME}")

        # 创建GPT-5结果目录
        if not os.path.exists(GPT5_RESULTS_FOLDER):
            os.makedirs(GPT5_RESULTS_FOLDER)
            print(f"📁 创建GPT-5结果目录: {GPT5_RESULTS_FOLDER}")

    def process_single_item(self, item: Dict[str, Any]) -> bool:
        """处理单个benchmark项目"""
        try:
            # 提取benchmark ID
            benchmark_id = self.extract_benchmark_id(item)

            # 创建输出数据结构
            output_data = self.create_output_structure(item, benchmark_id)

            # 保存JSON文件到输出目录
            json_filename = f"{benchmark_id}{JSON_EXTENSION}"
            json_filepath = os.path.join(OUTPUT_FOLDER_NAME, json_filename)

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            # 创建空的TXT文件到GPT-5结果目录
            txt_filename = f"{benchmark_id}{TXT_EXTENSION}"
            txt_filepath = os.path.join(GPT5_RESULTS_FOLDER, txt_filename)

            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write("")  # 空文件

            print(f"✅ 处理完成: {benchmark_id}")
            return True

        except Exception as e:
            print(f"❌ 处理失败: {e}")
            self.failed_items.append(str(e))
            return False

    def process_all(self):
        """处理所有数据"""
        print("🚀 开始端到端处理...")

        # 创建目录
        self.create_directories()

        # 加载数据
        data = self.load_benchmark_data()

        # 处理每个项目
        for item in data:
            if self.process_single_item(item):
                self.processed_count += 1
            else:
                self.failed_count += 1

        # 输出统计信息
        print("\n🎉 处理完成!")
        print(f"✅ 成功处理: {self.processed_count} 条")
        print(f"❌ 处理失败: {self.failed_count} 条")

        if self.failed_items:
            print("\n失败项目:")
            for item in self.failed_items:
                print(f"  - {item}")

        print(f"\n📁 输出文件夹: {OUTPUT_FOLDER_NAME}")
        print(f"📁 GPT-5结果文件夹: {GPT5_RESULTS_FOLDER}")

def main():
    """主函数"""
    processor = EndToEndProcessor()
    processor.process_all()

if __name__ == "__main__":
    main()
