#!/usr/bin/env python3
"""
Recent Changes生成器
基于benchmark中的代码上下文，生成3个最近的微改动
"""
import json
import os
import re
import requests
from typing import Dict, List, Any, Optional

class RCGenerator:
    """Recent Changes生成器"""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = "gpt-4o"
        
    def extract_code_context(self, prompt: str) -> Dict[str, str]:
        """从prompt中提取代码上下文"""
        context = {}
        
        # 提取上下文代码
        above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        if above_match:
            context['above'] = above_match.group(1).strip()
        
        below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        if below_match:
            context['below'] = below_match.group(1).strip()
        
        # 提取要实现的功能
        feature_match = re.search(r'The new feature is\s+(.*?)\.', prompt)
        if feature_match:
            context['feature'] = feature_match.group(1).strip()
        
        # 提取要修改的代码片段
        snippet_match = re.search(r'And here is the code snippet you are asked to modify:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        if snippet_match:
            context['target_snippet'] = snippet_match.group(1).strip()
        
        return context
    
    def build_system_prompt(self) -> str:
        """构建系统提示"""
        return """你是资深 Java 工程师。现在要开始一个较大的功能改动，但在正式改动之前，你**刚刚**会做一些微小编辑（Recent Changes），以统一风格/增强健壮性/便于后续修改。

必须遵守：
1. 不新增 import/依赖；不修改方法签名/可见性；不创建/删除类；
2. 不要实现或接近实现"当前任务"（CURRENT_BENCHMARK_TASK）；
3. 只输出 `### hunks_1`、`### hunks_2`、`### hunks_3`（JSON 数组）与可选 `### notes`（≤2 行），不得输出其他内容；
4. 每个 hunk 包含：path、type("same_file")、overlap、nearby、mini_diff（单 @@ 块的统一 diff）、after（变更处 after±3 行文本）。
5. 不限制 hunk 行数，但修改应保持"像刚改过"的合理规模与风格。"""
    
    def build_user_prompt(self, context: Dict[str, str], file_path: str, start_line: int, end_line: int) -> str:
        """构建用户提示"""
        full_code = ""
        if context.get('above'):
            full_code += context['above'] + "\n"
        if context.get('target_snippet'):
            full_code += context['target_snippet'] + "\n"
        if context.get('below'):
            full_code += context['below']
        
        return f"""[CURRENT_BENCHMARK_TASK]
{context.get('feature', 'Unknown feature')}

[INPUT_META]
- file: {file_path}
- selection_lines: {start_line}-{end_line}

[FILE_FULL_SOURCE]
{full_code}

[INTENT]
- 倒推你刚刚会做的[3]次微改动，有一定的递进/逻辑关系，让后续实现 [CURRENT_BENCHMARK_TASK] 更顺滑，但不要实现任务本身。
- 优先选择与 selection 存在"行重叠（overlap）或 ≤30 行内的近邻（nearby）"的位置。
- 允许输出多个 hunk；每个 hunk 自行决定行数和范围。

[RETURN FORMAT]
### hunks_1 (最近1次修改， 按时间来说最接近马上执行的指令)
<JSON array>

### hunks_2 (倒数第二次修改)
<JSON array>

### hunks_3 (倒数第三次修改)
<JSON array>

### notes
<可选的简短说明>"""
    
    def call_llm_api(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Optional[str]:
        """调用LLM API，带重试机制"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        for attempt in range(max_retries):
            try:
                print(f"  API调用尝试 {attempt + 1}/{max_retries}...")
                response = requests.post(self.api_url, headers=headers, json=data, timeout=120)

                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        print(f"  ✓ API调用成功，响应长度: {len(content)} 字符")
                        return content
                    else:
                        print(f"  ✗ API响应格式异常: {result}")
                else:
                    print(f"  ✗ API返回错误状态码: {response.status_code}")
                    print(f"    错误内容: {response.text[:200]}...")

            except requests.exceptions.Timeout:
                print(f"  ✗ 请求超时 (尝试 {attempt + 1})")
            except requests.exceptions.ConnectionError as e:
                print(f"  ✗ 连接错误 (尝试 {attempt + 1}): {e}")
            except Exception as e:
                print(f"  ✗ 其他错误 (尝试 {attempt + 1}): {e}")

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"    等待 {wait_time} 秒后重试...")
                import time
                time.sleep(wait_time)

        print(f"  ✗ API调用失败，已重试 {max_retries} 次")
        return None
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        result = {
            "hunks_1": [],
            "hunks_2": [],
            "hunks_3": [],
            "notes": ""
        }

        # 解析hunks_1
        hunks_1_match = re.search(r'### hunks_1[^\n]*\n(.*?)(?=### hunks_2|### notes|$)', response, re.DOTALL)
        if hunks_1_match:
            try:
                json_str = hunks_1_match.group(1).strip()
                result["hunks_1"] = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"解析hunks_1失败: {e}")
                print(f"原始内容: {hunks_1_match.group(1)[:200]}...")

        # 解析hunks_2
        hunks_2_match = re.search(r'### hunks_2[^\n]*\n(.*?)(?=### hunks_3|### notes|$)', response, re.DOTALL)
        if hunks_2_match:
            try:
                json_str = hunks_2_match.group(1).strip()
                result["hunks_2"] = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"解析hunks_2失败: {e}")

        # 解析hunks_3
        hunks_3_match = re.search(r'### hunks_3[^\n]*\n(.*?)(?=### notes|$)', response, re.DOTALL)
        if hunks_3_match:
            try:
                json_str = hunks_3_match.group(1).strip()
                result["hunks_3"] = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"解析hunks_3失败: {e}")

        # 解析notes
        notes_match = re.search(r'### notes\s*(.*?)$', response, re.DOTALL)
        if notes_match:
            result["notes"] = notes_match.group(1).strip()

        return result
    
    def generate_rc_for_benchmark(self, benchmark_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """为单条benchmark生成RC"""
        prompt = benchmark_data.get('prompt', '')
        extra_content = benchmark_data.get('extra_content', {})
        
        # 提取代码上下文
        context = self.extract_code_context(prompt)
        if not context:
            print(f"无法提取代码上下文: {benchmark_data.get('id', 'Unknown')}")
            return None
        
        # 构建提示
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(
            context,
            extra_content.get('file_path', 'unknown.java'),
            extra_content.get('start_line', 1),
            extra_content.get('end_line', 10)
        )
        
        # 调用LLM
        response = self.call_llm_api(system_prompt, user_prompt)
        if not response:
            return None

        # 解析响应
        parsed = self.parse_llm_response(response)
        
        # 合并所有hunks
        all_hunks = []
        all_hunks.extend(parsed.get("hunks_1", []))
        all_hunks.extend(parsed.get("hunks_2", []))
        all_hunks.extend(parsed.get("hunks_3", []))
        
        return {
            "hunks": all_hunks,
            "notes": parsed.get("notes", "")
        }

def main():
    """主函数"""
    # API配置
    api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    generator = RCGenerator(api_key, api_url)
    
    # 测试单条数据
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        first_entry = json.loads(first_line.strip())
    
    print("=== 测试RC生成 ===")
    print(f"处理benchmark: {first_entry.get('id', 'Unknown')}")
    
    rc_context = generator.generate_rc_for_benchmark(first_entry)
    if rc_context:
        print("生成成功!")
        print(f"Hunks数量: {len(rc_context['hunks'])}")
        print(f"Notes: {rc_context['notes']}")
        
        # 保存测试结果
        with open("test_rc_output.json", 'w', encoding='utf-8') as f:
            json.dump(rc_context, f, indent=2, ensure_ascii=False)
        print("测试结果已保存到 test_rc_output.json")
    else:
        print("生成失败!")

if __name__ == "__main__":
    main()
