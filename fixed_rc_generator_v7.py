#!/usr/bin/env python3
"""
修正的RC生成器 - 正确的行号定位和禁止修改区域标注
"""

import json
import re
import requests
import os
import time
from datetime import datetime

class GPT5RCGeneratorV8:
    def __init__(self):
        self.api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
        self.api_url = "https://api2.aigcbest.top/v1/chat/completions"
        self.prompt_template = self.load_prompt_template()
        
        # 创建修正输出目录
        os.makedirs('fixed_output', exist_ok=True)
        
    def load_prompt_template(self):
        with open('RC_prompt_v7_fixed.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        parts = content.split('(2) User Prompt')
        system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
        user_template = parts[1].strip()
        return system_prompt, user_template
    
    def add_line_numbers_with_annotations(self, code_content, selected_region, target_implementation):
        """为代码添加行号和禁止修改标注"""
        lines = code_content.split('\n')
        numbered_lines = []

        # 找到目标实现的完整行号范围
        target_lines = set()

        if target_implementation.strip():
            # 清理target_implementation，移除markdown标记
            clean_target = target_implementation.replace('```java\n', '').replace('\n```', '').strip()
            target_lines_content = clean_target.split('\n')

            # 找到目标实现的开始行
            start_line = -1
            for i, line in enumerate(lines):
                # 查找包含方法签名的行（通常是第一行）
                first_target_line = target_lines_content[0].strip()
                if first_target_line in line.strip():
                    start_line = i + 1
                    break

            # 如果找到开始行，标注整个目标实现块
            if start_line > 0:
                # 计算目标实现的行数
                target_line_count = len(target_lines_content)
                for j in range(target_line_count):
                    if start_line + j <= len(lines):
                        target_lines.add(start_line + j)

        # 找到选中区域的行号（通常是方法签名行）
        selected_lines = set()
        if selected_region.strip():
            for i, line in enumerate(lines):
                if selected_region.strip() in line.strip():
                    selected_lines.add(i + 1)

        # 添加行号和标注
        for i, line in enumerate(lines, 1):
            line_annotation = ""
            if i in selected_lines and i not in target_lines:
                # 如果是选中区域但不在目标实现中（避免重复标注）
                line_annotation = " // [禁止修改-选中区域]"
            elif i in target_lines:
                line_annotation = " // [禁止修改-目标实现]"

            numbered_lines.append(f"{i:3d}: {line}{line_annotation}")

        return '\n'.join(numbered_lines)
    
    def parse_benchmark(self, benchmark_data):
        """解析benchmark数据"""
        prompt = benchmark_data['prompt']
        
        # 提取各部分
        context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        task_match = re.search(r'The new feature is (.+?)\.', prompt)
        selected_match = re.search(r'And here is the code snippet you are asked to modify:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        
        context_above = context_above_match.group(1).strip() if context_above_match else ''
        context_below = context_below_match.group(1).strip() if context_below_match else ''
        task = task_match.group(1).strip() if task_match else ''
        selected_region = selected_match.group(1).strip() if selected_match else ''
        target_implementation = benchmark_data['good_example_response'].replace('```java\n', '').replace('\n```', '').strip()
        
        # 构造最终完整代码（插入目标实现）
        final_complete_code = self.construct_final_code(context_above, context_below, target_implementation, selected_region)
        
        # 为最终代码添加行号和标注
        final_code_with_annotations = self.add_line_numbers_with_annotations(
            final_complete_code, selected_region, target_implementation
        )
        
        return {
            'task_description': task,
            'selected_region': selected_region,
            'target_implementation': target_implementation,
            'final_complete_code': final_complete_code,
            'final_code_with_annotations': final_code_with_annotations
        }
    
    def construct_final_code(self, context_above, context_below, target_implementation, selected_region):
        """构造最终完整代码"""
        # 找到选中区域在context中的位置，并替换为目标实现
        full_context = f"{context_above}\n{context_below}"
        
        # 如果能找到选中区域，直接替换
        if selected_region.strip() in full_context:
            final_code = full_context.replace(selected_region.strip(), target_implementation.strip())
        else:
            # 否则在类的最后插入目标实现
            if full_context.endswith('}'):
                final_code = full_context[:-1] + f"\n{target_implementation}\n}}"
            else:
                final_code = f"{full_context}\n{target_implementation}"
            
        return final_code
    
    def create_prompt(self, parsed_data):
        """创建完整的prompt"""
        system_prompt, user_template = self.prompt_template
        
        user_prompt = user_template.format(
            task_description=parsed_data['task_description'],
            selected_region=parsed_data['selected_region'],
            target_implementation=parsed_data['target_implementation'],
            final_code_with_annotations=parsed_data['final_code_with_annotations']
        )
        
        return system_prompt, user_prompt
    
    def call_llm_with_retry(self, system_prompt, user_prompt, max_retries=3):
        """调用LLM，带重试机制"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': "gpt-4o-2024-08-06",
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 3000
        }
        
        for attempt in range(max_retries):
            try:
                print(f"  尝试 {attempt + 1}/{max_retries}...")
                response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']
            except Exception as e:
                print(f"  尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"  等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise e
    
    def parse_llm_response(self, response_text):
        """解析LLM响应，提取hunks"""
        try:
            # 提取hunks_3
            hunks_3_match = response_text.find('### hunks_3')
            hunks_2_match = response_text.find('### hunks_2')
            if hunks_3_match != -1 and hunks_2_match != -1:
                hunks_3_section = response_text[hunks_3_match:hunks_2_match]
                json_start = hunks_3_section.find('```json\n') + 8
                json_end = hunks_3_section.find('\n```', json_start)
                if json_start > 7 and json_end != -1:
                    hunks_3_json = hunks_3_section[json_start:json_end]
                    hunks_3 = json.loads(hunks_3_json)
                else:
                    hunks_3 = []
            else:
                hunks_3 = []
            
            # 提取hunks_2
            hunks_1_match = response_text.find('### hunks_1')
            if hunks_2_match != -1 and hunks_1_match != -1:
                hunks_2_section = response_text[hunks_2_match:hunks_1_match]
                json_start = hunks_2_section.find('```json\n') + 8
                json_end = hunks_2_section.find('\n```', json_start)
                if json_start > 7 and json_end != -1:
                    hunks_2_json = hunks_2_section[json_start:json_end]
                    hunks_2 = json.loads(hunks_2_json)
                else:
                    hunks_2 = []
            else:
                hunks_2 = []
            
            # 提取hunks_1
            notes_match = response_text.find('### notes')
            if hunks_1_match != -1:
                if notes_match != -1:
                    hunks_1_section = response_text[hunks_1_match:notes_match]
                else:
                    hunks_1_section = response_text[hunks_1_match:]
                json_start = hunks_1_section.find('```json\n') + 8
                json_end = hunks_1_section.find('\n```', json_start)
                if json_start > 7 and json_end != -1:
                    hunks_1_json = hunks_1_section[json_start:json_end]
                    hunks_1 = json.loads(hunks_1_json)
                else:
                    hunks_1 = []
            else:
                hunks_1 = []
            
            return hunks_3, hunks_2, hunks_1
        except Exception as e:
            print(f"解析响应失败: {e}")
            return [], [], []
    
    def validate_line_numbers(self, hunks, final_code_lines, benchmark_id):
        """验证diff中的行号是否与最终代码匹配"""
        validation_results = []
        
        for hunk_name, hunk_list in hunks.items():
            for i, hunk in enumerate(hunk_list):
                start_line = hunk.get('start_line', 0)
                end_line = hunk.get('end_line', 0)
                
                # 检查行号是否在有效范围内
                if start_line < 1 or start_line > len(final_code_lines):
                    validation_results.append({
                        'hunk': f"{hunk_name}[{i}]",
                        'issue': f"start_line {start_line} 超出范围 (1-{len(final_code_lines)})",
                        'valid': False
                    })
                elif end_line < 1 or end_line > len(final_code_lines):
                    validation_results.append({
                        'hunk': f"{hunk_name}[{i}]",
                        'issue': f"end_line {end_line} 超出范围 (1-{len(final_code_lines)})",
                        'valid': False
                    })
                else:
                    validation_results.append({
                        'hunk': f"{hunk_name}[{i}]",
                        'issue': f"行号 {start_line}-{end_line} 有效",
                        'valid': True
                    })
        
        return validation_results
    
    def process_single_benchmark(self, benchmark_data, index):
        """处理单个benchmark"""
        benchmark_id = benchmark_data.get('id', f'benchmark_{index}')
        
        print(f"🚀 处理 {benchmark_id}...")
        
        try:
            # 解析benchmark
            parsed_data = self.parse_benchmark(benchmark_data)
            
            # 创建prompt
            system_prompt, user_prompt = self.create_prompt(parsed_data)
            
            # 调用LLM
            llm_response = self.call_llm_with_retry(system_prompt, user_prompt)
            
            # 解析响应
            hunks_3, hunks_2, hunks_1 = self.parse_llm_response(llm_response)
            
            # 验证行号
            final_code_lines = parsed_data['final_complete_code'].split('\n')
            hunks_dict = {'hunks_3': hunks_3, 'hunks_2': hunks_2, 'hunks_1': hunks_1}
            validation_results = self.validate_line_numbers(hunks_dict, final_code_lines, benchmark_id)
            
            # 统一保存所有数据
            complete_data = {
                'benchmark_id': benchmark_id,
                'timestamp': datetime.now().isoformat(),
                'task_description': parsed_data['task_description'],
                'selected_region': parsed_data['selected_region'],
                'target_implementation': parsed_data['target_implementation'],
                'final_code_with_annotations': parsed_data['final_code_with_annotations'],
                'prompt': {
                    'system_prompt': system_prompt,
                    'user_prompt': user_prompt
                },
                'llm_response': llm_response,
                'parsed_hunks': {
                    'hunks_3': hunks_3,
                    'hunks_2': hunks_2,
                    'hunks_1': hunks_1
                },
                'validation_results': validation_results,
                'original_benchmark': benchmark_data
            }
            
            # 保存到单个文件
            with open(f'fixed_output/{benchmark_id}.json', 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=2)
            
            # 检查验证结果
            invalid_hunks = [r for r in validation_results if not r['valid']]
            if invalid_hunks:
                print(f"⚠️ {benchmark_id} 处理成功但有行号问题:")
                for issue in invalid_hunks:
                    print(f"  - {issue['hunk']}: {issue['issue']}")
            else:
                print(f"✅ {benchmark_id} 处理成功，行号验证通过")
            
            return {
                'benchmark_id': benchmark_id,
                'status': 'success',
                'hunks_count': [len(hunks_3), len(hunks_2), len(hunks_1)],
                'validation_issues': len(invalid_hunks)
            }
            
        except Exception as e:
            print(f"❌ {benchmark_id} 处理失败: {e}")
            return {
                'benchmark_id': benchmark_id,
                'status': 'failed',
                'error': str(e)
            }

    def generate_all_fixed(self):
        """生成所有benchmark的修正版RC"""
        print("=== 开始生成修正版RC（正确标注、精确行号） ===")

        # 加载benchmark数据
        with open('benchmark/nl2code_java_F10L.jsonl', 'r', encoding='utf-8') as f:
            benchmarks = [json.loads(line) for line in f]

        results = []

        for i, benchmark in enumerate(benchmarks, 1):
            result = self.process_single_benchmark(benchmark, i)
            results.append(result)

            print(f"进度: {i}/{len(benchmarks)}")

        # 保存总结果
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_benchmarks': len(benchmarks),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'total_validation_issues': sum([r.get('validation_issues', 0) for r in results]),
            'results': results
        }

        with open('fixed_output/fixed_generation_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n🎉 修正版生成完成！")
        print(f"成功: {summary['successful']}/{summary['total_benchmarks']}")
        print(f"失败: {summary['failed']}/{summary['total_benchmarks']}")
        print(f"验证问题总数: {summary['total_validation_issues']}")

        return summary

if __name__ == "__main__":
    generator = FixedRCGeneratorV7()

    # 先测试第一条
    print("=== 测试修正版生成器 ===")
    with open('benchmark/nl2code_java_F10L.jsonl', 'r', encoding='utf-8') as f:
        first_benchmark = json.loads(f.readline())

    result = generator.process_single_benchmark(first_benchmark, 1)
    print(f"测试结果: {result}")

    if result['status'] == 'success' and result['validation_issues'] == 0:
        print("✅ 测试成功，开始处理所有benchmark")
        generator.generate_all_fixed()
    else:
        print("❌ 测试失败，请检查问题")
