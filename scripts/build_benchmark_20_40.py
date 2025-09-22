#!/usr/bin/env python3
"""
构建F20-40 Benchmark - 基于separated格式和GPT-5结果
将final_gpt4o_output_20-40和gpt5_results_20-40合并生成最终benchmark
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any

class BenchmarkBuilder:
    """Benchmark构建器"""

    def __init__(self):
        self.final_gpt4o_dir = "final_gpt4o_output_20-40"
        self.gpt5_results_dir = "gpt5_results_20-40"
        self.output_file = "benchmark/nl2code_java_F20-40_with_rc_separated.jsonl"
    
    def parse_gpt5_result(self, gpt5_content: str) -> Dict[str, Any]:
        """解析GPT-5结果内容"""
        result = {
            'hunks_3': [],
            'hunks_2': [],
            'hunks_1': [],
            'notes': ''
        }

        # 提取hunks_3 (支持转义符)
        hunks_3_pattern = r'### hunks[_\\]*3.*?```json\n(.*?)\n```'
        hunks_3_match = re.search(hunks_3_pattern, gpt5_content, re.DOTALL)
        if hunks_3_match:
            try:
                result['hunks_3'] = json.loads(hunks_3_match.group(1))
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse hunks_3: {e}")

        # 提取hunks_2 (支持转义符)
        hunks_2_pattern = r'### hunks[_\\]*2.*?```json\n(.*?)\n```'
        hunks_2_match = re.search(hunks_2_pattern, gpt5_content, re.DOTALL)
        if hunks_2_match:
            try:
                result['hunks_2'] = json.loads(hunks_2_match.group(1))
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse hunks_2: {e}")

        # 提取hunks_1 (支持转义符)
        hunks_1_pattern = r'### hunks[_\\]*1.*?```json\n(.*?)\n```'
        hunks_1_match = re.search(hunks_1_pattern, gpt5_content, re.DOTALL)
        if hunks_1_match:
            try:
                result['hunks_1'] = json.loads(hunks_1_match.group(1))
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse hunks_1: {e}")

        # 提取notes
        notes_pattern = r'### notes\n(.*?)(?=\n###|\Z)'
        notes_match = re.search(notes_pattern, gpt5_content, re.DOTALL)
        if notes_match:
            result['notes'] = notes_match.group(1).strip()

        return result
    
    def generate_rc_context(self, hunks_3: List, hunks_2: List, hunks_1: List) -> str:
        """生成Recent Changes上下文"""
        rc_context = ""
        
        # Recent Change 3 (最早的修改)
        if hunks_3:
            rc_context += "### Recent Change 3 (最早的准备工作)\n"
            rc_context += "开发者在实现目标功能前，首先进行了以下修改：\n\n"
            for hunk in hunks_3:
                rc_context += f"**文件**: {hunk.get('file_path', 'unknown')}\n"
                rc_context += f"**修改位置**: 第{hunk.get('start_line', 0)}-{hunk.get('end_line', 0)}行\n"
                rc_context += "```diff\n"
                rc_context += hunk.get('diff_content', '')
                rc_context += "\n```\n\n"
        
        # Recent Change 2 (中间修改)
        if hunks_2:
            rc_context += "### Recent Change 2 (中间准备工作)\n"
            rc_context += "接着，开发者进行了进一步的修改：\n\n"
            for hunk in hunks_2:
                rc_context += f"**文件**: {hunk.get('file_path', 'unknown')}\n"
                rc_context += f"**修改位置**: 第{hunk.get('start_line', 0)}-{hunk.get('end_line', 0)}行\n"
                rc_context += "```diff\n"
                rc_context += hunk.get('diff_content', '')
                rc_context += "\n```\n\n"
        
        # Recent Change 1 (最近修改)
        if hunks_1:
            rc_context += "### Recent Change 1 (最近的准备工作)\n"
            rc_context += "最后，开发者进行了最终的准备修改：\n\n"
            for hunk in hunks_1:
                rc_context += f"**文件**: {hunk.get('file_path', 'unknown')}\n"
                rc_context += f"**修改位置**: 第{hunk.get('start_line', 0)}-{hunk.get('end_line', 0)}行\n"
                rc_context += "```diff\n"
                rc_context += hunk.get('diff_content', '')
                rc_context += "\n```\n\n"
        
        return rc_context
    
    def extract_prompt_sections(self, prompt: str) -> Dict[str, str]:
        """从原始prompt中提取各个部分"""
        sections = {
            'external_imports': '',
            'context_above': '',
            'context_below': '',
            'task_description': '',
            'selected_region': ''
        }

        # 提取external imports
        if 'external classes imported' in prompt:
            start = prompt.find('```java\n') + 8
            end = prompt.find('\n```', start)
            if start > 7 and end > start:
                sections['external_imports'] = prompt[start:end]

        # 提取context above
        if 'The context above is:' in prompt:
            start = prompt.find('The context above is:\n```java\n') + 31
            end = prompt.find('\n```\n\nThe context below is:', start)
            if start > 30 and end > start:
                sections['context_above'] = prompt[start:end]

        # 提取context below
        if 'The context below is:' in prompt:
            start = prompt.find('The context below is:\n```java\n') + 31
            end = prompt.find('\n```\n\nThe new feature is', start)
            if start > 30 and end > start:
                sections['context_below'] = prompt[start:end]

        # 提取task description
        if 'The new feature is' in prompt:
            start = prompt.find('The new feature is ') + 19
            end = prompt.find('\n\nAnd here is the code snippet', start)
            if start > 18 and end > start:
                sections['task_description'] = prompt[start:end].strip()

        # 提取selected region
        if 'And here is the code snippet you are asked to modify:' in prompt:
            start = prompt.rfind('```java\n') + 8
            end = prompt.rfind('\n```')
            if start > 7 and end > start:
                sections['selected_region'] = prompt[start:end]

        return sections

    def build_benchmark_entry(self, gpt4o_data: Dict, gpt5_result: Dict) -> Dict[str, Any]:
        """构建单个benchmark条目 - 直接在原始prompt基础上添加RC"""
        original_benchmark = gpt4o_data['original_benchmark']
        original_prompt = original_benchmark['prompt']

        # 生成Recent Changes上下文
        rc_context = self.generate_rc_context(
            gpt5_result['hunks_3'],
            gpt5_result['hunks_2'],
            gpt5_result['hunks_1']
        )

        # 在原始prompt中插入Recent Changes
        # 找到"The new feature is"的位置，在其前面插入RC
        if "The new feature is" in original_prompt:
            parts = original_prompt.split("The new feature is", 1)
            final_prompt = parts[0] + "\n## Recent Changes Context\n"
            final_prompt += "Here are some recent changes that were made to this file to help you understand the development context:\n\n"
            final_prompt += rc_context
            final_prompt += "\nThese recent changes show the development progression leading up to the current task.\n\n"
            final_prompt += "The new feature is" + parts[1]
        else:
            # 如果没找到标准位置，就在末尾添加
            final_prompt = original_prompt + "\n\n## Recent Changes Context\n" + rc_context

        # 构建最终的benchmark条目
        benchmark_entry = {
            'prompt': final_prompt,
            'domain': original_benchmark['domain'],
            'id': original_benchmark['id'],
            'good_example_response': original_benchmark['good_example_response'],
            'reward_command': original_benchmark['reward_command'],
            'extra_content': original_benchmark['extra_content'],
            'recent_changes': {
                'hunks_3': gpt5_result['hunks_3'],
                'hunks_2': gpt5_result['hunks_2'],
                'hunks_1': gpt5_result['hunks_1'],
                'notes': gpt5_result['notes']
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'template_version': 'v4_separated',
                'source_gpt4o': gpt4o_data['benchmark_id'],
                'source_gpt5': f"gpt5_results_20-40/{original_benchmark['id']}.txt"
            }
        }

        return benchmark_entry
    
    def build_benchmark(self):
        """构建完整的benchmark"""
        print("🚀 开始构建F20-40 Benchmark...")
        
        # 获取所有GPT-4o输出文件
        gpt4o_files = [f for f in os.listdir(self.final_gpt4o_dir) if f.endswith('.json')]
        gpt4o_files.sort()
        
        benchmark_entries = []
        success_count = 0
        
        for gpt4o_file in gpt4o_files:
            benchmark_id = gpt4o_file.replace('.json', '')
            gpt5_file = f"{benchmark_id}.txt"
            
            print(f"📋 处理: {benchmark_id}")
            
            # 加载GPT-4o数据
            gpt4o_path = os.path.join(self.final_gpt4o_dir, gpt4o_file)
            with open(gpt4o_path, 'r', encoding='utf-8') as f:
                gpt4o_data = json.load(f)
            
            # 加载GPT-5结果
            gpt5_path = os.path.join(self.gpt5_results_dir, gpt5_file)
            if not os.path.exists(gpt5_path):
                print(f"  ❌ 缺少GPT-5结果: {gpt5_file}")
                continue
            
            with open(gpt5_path, 'r', encoding='utf-8') as f:
                gpt5_content = f.read()
            
            if not gpt5_content.strip():
                print(f"  ❌ GPT-5结果为空: {gpt5_file}")
                continue
            
            # 解析GPT-5结果
            gpt5_result = self.parse_gpt5_result(gpt5_content)
            
            # 验证GPT-5结果完整性
            if not any([gpt5_result['hunks_3'], gpt5_result['hunks_2'], gpt5_result['hunks_1']]):
                print(f"  ❌ GPT-5结果不完整: {gpt5_file}")
                continue
            
            # 构建benchmark条目
            try:
                benchmark_entry = self.build_benchmark_entry(gpt4o_data, gpt5_result)
                benchmark_entries.append(benchmark_entry)
                success_count += 1
                print(f"  ✅ 成功处理")
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
        
        # 保存benchmark
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for entry in benchmark_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"\n🎉 Benchmark构建完成!")
        print(f"✅ 成功处理: {success_count}/{len(gpt4o_files)} 条")
        print(f"📄 输出文件: {self.output_file}")
        
        return benchmark_entries

def main():
    """主函数"""
    builder = BenchmarkBuilder()
    benchmark_entries = builder.build_benchmark()
    
    # 生成统计信息
    stats = {
        'total_entries': len(benchmark_entries),
        'entries_with_rc3': len([e for e in benchmark_entries if e['recent_changes']['hunks_3']]),
        'entries_with_rc2': len([e for e in benchmark_entries if e['recent_changes']['hunks_2']]),
        'entries_with_rc1': len([e for e in benchmark_entries if e['recent_changes']['hunks_1']]),
        'created_at': datetime.now().isoformat()
    }
    
    stats_file = "benchmark/nl2code_java_F20-40_with_rc_separated_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"📊 统计信息已保存: {stats_file}")

if __name__ == "__main__":
    main()
