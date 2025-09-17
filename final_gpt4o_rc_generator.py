#!/usr/bin/env python3
"""
最终GPT-4o RC生成器 - 使用最新prompt和优化的API调用
"""

import json
import requests
import os
import re
import time
from datetime import datetime

class FinalGPT4oRCGenerator:
    def __init__(self):
        self.api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
        self.api_url = "https://api2.aigcbest.top/v1/chat/completions"
        self.model = "gpt-4o-2024-11-20"  # 使用最新的GPT-4o
        self.output_dir = "final_gpt4o_output_20"
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载最新的prompt模板
        self.system_prompt, self.user_prompt_template = self.load_prompt_template()
        
    def load_prompt_template(self):
        """加载最新的prompt模板"""
        with open('RC_prompt_v8_gpt5.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        parts = content.split('(2) User Prompt')
        system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
        user_template = parts[1].strip()
        return system_prompt, user_template
    
    def parse_benchmark(self, benchmark):
        """解析benchmark数据"""
        # 提取基本信息
        benchmark_id = benchmark.get('id', 'unknown')
        
        # 从prompt字符串中提取context
        prompt_text = benchmark.get('prompt', '')
        
        # 解析context_above
        context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt_text, re.DOTALL)
        context_above = context_above_match.group(1) if context_above_match else ''
        
        # 解析context_below
        context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt_text, re.DOTALL)
        context_below = context_below_match.group(1) if context_below_match else ''
        
        # 解析选中区域
        selected_match = re.search(r'And here is the code snippet you are asked to modify:\s*```java\s*(.*?)\s*```', prompt_text, re.DOTALL)
        selected_region = selected_match.group(1).strip() if selected_match else ''
        
        # 目标实现
        good_example = benchmark.get('good_example_response', '')
        # 清理good_example中的```java标记
        target_implementation = re.sub(r'```java\s*|\s*```', '', good_example).strip()
        
        # 完整代码 = context_above + target_implementation + context_below
        full_code = context_above + '\n' + target_implementation + '\n' + context_below
        
        return {
            'benchmark_id': benchmark_id,
            'full_code': full_code,
            'selected_region': selected_region,
            'target_implementation': target_implementation
        }
    
    def add_line_numbers_with_annotations(self, code_content, selected_region, target_implementation):
        """添加行号和正确的禁止修改标注"""
        lines = code_content.split('\n')
        numbered_lines = []
        
        # 找到目标实现的行号范围
        target_lines = set()
        if target_implementation.strip():
            # 清理目标实现内容
            clean_target = target_implementation.replace('```java\n', '').replace('\n```', '').strip()
            target_lines_content = clean_target.split('\n')
            
            # 找到目标实现的开始行
            first_target_line = target_lines_content[0].strip()
            target_start_line = None
            
            for i, line in enumerate(lines):
                if first_target_line in line.strip():
                    target_start_line = i + 1  # 行号从1开始
                    break
            
            if target_start_line:
                # 计算目标实现的完整行号范围
                for j in range(len(target_lines_content)):
                    if target_start_line + j <= len(lines):
                        target_lines.add(target_start_line + j)
        
        # 生成带行号和标注的代码
        for i, line in enumerate(lines):
            line_number = i + 1
            if line_number in target_lines:
                numbered_lines.append(f"{line_number:3d}: {line} // [禁止修改-目标实现]")
            else:
                numbered_lines.append(f"{line_number:3d}: {line}")
        
        return '\n'.join(numbered_lines)
    
    def create_prompt(self, parsed_data):
        """创建优化的prompt"""
        # 添加行号和标注
        final_code_with_annotations = self.add_line_numbers_with_annotations(
            parsed_data['full_code'],
            parsed_data['selected_region'],
            parsed_data['target_implementation']
        )
        
        # 填充用户prompt模板（移除TASK_DESCRIPTION）
        user_prompt = self.user_prompt_template.format(
            selected_region=parsed_data['selected_region'],
            target_implementation=parsed_data['target_implementation'],
            final_code_with_annotations=final_code_with_annotations
        )
        
        return {
            'system_prompt': self.system_prompt,
            'user_prompt': user_prompt,
            'final_code_with_annotations': final_code_with_annotations
        }
    
    def call_gpt4o_api(self, system_prompt, user_prompt, max_retries=3):
        """调用GPT-4o API - 优化的重试机制"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 3000
        }
        
        for attempt in range(max_retries):
            timeout = 30 + attempt * 15  # 30s, 45s, 60s
            
            try:
                print(f"  API调用 (超时: {timeout}秒, 尝试: {attempt + 1}/{max_retries})...")
                response = requests.post(self.api_url, headers=headers, json=data, timeout=timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        usage = result.get('usage', {})
                        print(f"  ✅ API调用成功 (响应长度: {len(content)} 字符)")
                        return content, usage
                    else:
                        print(f"  ❌ 响应格式错误: {result}")
                        
                elif response.status_code == 429:
                    print(f"  ⚠️ 速率限制 (429)")
                    if attempt < max_retries - 1:
                        print(f"  等待 5 秒后重试...")
                        time.sleep(5)
                    continue
                    
                elif response.status_code >= 500:
                    print(f"  ⚠️ 服务器错误 {response.status_code}")
                    
                else:
                    print(f"  ❌ HTTP错误 {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⚠️ 请求超时 ({timeout}秒)")
                
            except requests.exceptions.ConnectionError:
                print(f"  ⚠️ 连接错误")
                
            except Exception as e:
                print(f"  ❌ API调用异常: {e}")
            
            # 重试等待
            if attempt < max_retries - 1:
                wait_time = 2  # 固定2秒等待
                print(f"  等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        print(f"  ❌ API调用失败，已重试 {max_retries} 次")
        return None, {}
    
    def parse_hunks_response(self, response_text):
        """解析hunks响应"""
        hunks_data = {}
        
        # 提取hunks_3, hunks_2, hunks_1
        for hunk_name in ['hunks_3', 'hunks_2', 'hunks_1']:
            pattern = rf'### {hunk_name}.*?```json\s*(.*?)\s*```'
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if match:
                try:
                    json_content = match.group(1).strip()
                    hunks_list = json.loads(json_content)
                    hunks_data[hunk_name] = hunks_list
                except json.JSONDecodeError as e:
                    print(f"  解析{hunk_name}失败: {e}")
                    hunks_data[hunk_name] = []
            else:
                print(f"  未找到{hunk_name}")
                hunks_data[hunk_name] = []
        
        return hunks_data
    
    def validate_line_numbers(self, hunks_data, final_code_lines):
        """验证行号有效性"""
        total_lines = len(final_code_lines)
        validation_issues = 0
        
        for hunk_name, hunks_list in hunks_data.items():
            for hunk in hunks_list:
                start_line = hunk.get('start_line', 0)
                end_line = hunk.get('end_line', 0)
                
                if start_line < 1 or start_line > total_lines:
                    print(f"  ⚠️ {hunk_name}: start_line {start_line} 超出范围 [1, {total_lines}]")
                    validation_issues += 1
                
                if end_line < 1 or end_line > total_lines:
                    print(f"  ⚠️ {hunk_name}: end_line {end_line} 超出范围 [1, {total_lines}]")
                    validation_issues += 1
                
                if start_line > end_line:
                    print(f"  ⚠️ {hunk_name}: start_line {start_line} > end_line {end_line}")
                    validation_issues += 1
        
        return validation_issues

    def process_single_benchmark(self, benchmark, index):
        """处理单个benchmark"""
        parsed_data = self.parse_benchmark(benchmark)
        benchmark_id = parsed_data['benchmark_id']

        print(f"🚀 处理 {benchmark_id}...")

        # 创建prompt
        prompt_data = self.create_prompt(parsed_data)

        # 调用GPT-4o API
        llm_response, usage = self.call_gpt4o_api(
            prompt_data['system_prompt'],
            prompt_data['user_prompt']
        )

        if llm_response:
            # 解析响应
            hunks_data = self.parse_hunks_response(llm_response)

            # 验证行号
            final_code_lines = prompt_data['final_code_with_annotations'].split('\n')
            validation_issues = self.validate_line_numbers(hunks_data, final_code_lines)

            # 保存完整结果
            complete_result = {
                'benchmark_id': benchmark_id,
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model,
                'selected_region': parsed_data['selected_region'],
                'target_implementation': parsed_data['target_implementation'],
                'final_code_with_annotations': prompt_data['final_code_with_annotations'],
                'prompt': {
                    'system_prompt': prompt_data['system_prompt'],
                    'user_prompt': prompt_data['user_prompt']
                },
                'llm_response': llm_response,
                'parsed_hunks': hunks_data,
                'validation_results': {
                    'total_issues': validation_issues,
                    'total_lines': len(final_code_lines)
                },
                'usage': usage,
                'original_benchmark': benchmark
            }

            # 保存到文件
            output_file = os.path.join(self.output_dir, f"{benchmark_id}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(complete_result, f, ensure_ascii=False, indent=2)

            if validation_issues == 0:
                print(f"✅ {benchmark_id} 处理成功，行号验证通过")
            else:
                print(f"⚠️ {benchmark_id} 处理成功，但有 {validation_issues} 个验证问题")

            return {
                'benchmark_id': benchmark_id,
                'status': 'success',
                'hunks_count': [len(hunks_data.get('hunks_3', [])),
                               len(hunks_data.get('hunks_2', [])),
                               len(hunks_data.get('hunks_1', []))],
                'validation_issues': validation_issues
            }

        print(f"❌ {benchmark_id} 处理失败")
        return {
            'benchmark_id': benchmark_id,
            'status': 'failed',
            'hunks_count': [0, 0, 0],
            'validation_issues': 0
        }

    def generate_all_final(self):
        """生成所有benchmark的最终RC"""
        print("=== 开始最终GPT-4o RC生成（最新prompt） ===")
        print(f"使用模型: {self.model}")

        # 加载benchmark数据
        with open('benchmark/nl2code_java_F20L.jsonl', 'r', encoding='utf-8') as f:
            benchmarks = [json.loads(line) for line in f]

        print(f"总benchmark数: {len(benchmarks)}")

        results = []
        successful_count = 0
        failed_count = 0

        for i, benchmark in enumerate(benchmarks, 1):
            print(f"\n--- 处理第 {i}/{len(benchmarks)} 个benchmark ---")
            result = self.process_single_benchmark(benchmark, i)
            results.append(result)

            if result['status'] == 'success':
                successful_count += 1
                print(f"✅ 成功: {successful_count}, 失败: {failed_count}")
            else:
                failed_count += 1
                print(f"❌ 成功: {successful_count}, 失败: {failed_count}")

            # 每处理5个保存一次进度
            if i % 5 == 0:
                self.save_progress_summary(results, i, len(benchmarks))

        # 保存最终结果
        final_summary = self.save_progress_summary(results, len(benchmarks), len(benchmarks), is_final=True)

        print(f"\n🎉 最终GPT-4o生成完成！")
        print(f"模型: {self.model}")
        print(f"成功: {final_summary['successful']}/{final_summary['total_benchmarks']}")
        print(f"失败: {final_summary['failed']}/{final_summary['total_benchmarks']}")
        print(f"验证问题总数: {final_summary['total_validation_issues']}")

        return final_summary

    def save_progress_summary(self, results, current, total, is_final=False):
        """保存进度摘要"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'model_used': self.model,
            'progress': f"{current}/{total}",
            'total_benchmarks': total,
            'processed': current,
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'total_validation_issues': sum([r.get('validation_issues', 0) for r in results]),
            'results': results
        }

        filename = 'final_gpt4o_summary.json' if is_final else 'final_gpt4o_progress.json'
        with open(f'{self.output_dir}/{filename}', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        if not is_final:
            print(f"📊 进度已保存: {current}/{total}")

        return summary

if __name__ == "__main__":
    generator = FinalGPT4oRCGenerator()

    print("=== 启动最终GPT-4o批量生成 ===")
    print(f"使用模型: {generator.model}")

    # 开始批量处理
    summary = generator.generate_all_final()

    print(f"\n🎉 批量生成完成！")
    print(f"最终结果: 成功 {summary['successful']}/{summary['total_benchmarks']}")
