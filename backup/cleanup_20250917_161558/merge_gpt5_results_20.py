#!/usr/bin/env python3
"""
合并GPT-5结果（后10条数据）并检查diff方向
"""

import json
import os
import re
from datetime import datetime

class GPT5ResultsMerger20:
    def __init__(self):
        self.gpt5_result_dir = "gpt5_result_20"
        self.gpt4o_template_dir = "final_gpt4o_output_20"
        self.output_dir = "gpt5_manual_20"
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def read_gpt5_result(self, filename):
        """读取GPT-5结果文件"""
        filepath = os.path.join(self.gpt5_result_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content
    
    def parse_hunks_from_gpt5(self, content):
        """解析GPT-5结果中的hunks"""
        hunks_data = {}
        
        # 提取hunks_3, hunks_2, hunks_1
        for hunk_name in ['hunks_3', 'hunks_2', 'hunks_1']:
            # 匹配各种可能的格式，包括转义符
            escaped_name = hunk_name.replace('_', r'\\_')
            patterns = [
                rf'### {escaped_name}.*?```json\s*(.*?)\s*```',
                rf'### {hunk_name}.*?```json\s*(.*?)\s*```',
                rf'## {escaped_name}.*?```json\s*(.*?)\s*```',
                rf'## {hunk_name}.*?```json\s*(.*?)\s*```',
                rf'{escaped_name}.*?```json\s*(.*?)\s*```',
                rf'{hunk_name}.*?```json\s*(.*?)\s*```'
            ]
            
            found = False
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        json_content = match.group(1).strip()
                        # 清理可能的转义字符
                        json_content = json_content.replace('\\_', '_')
                        hunks_list = json.loads(json_content)
                        hunks_data[hunk_name] = hunks_list
                        found = True
                        print(f"  ✅ 成功解析 {hunk_name}: {len(hunks_list)} 个hunks")
                        break
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️ 解析{hunk_name}失败: {e}")
                        continue
            
            if not found:
                print(f"  ❌ 未找到 {hunk_name}")
                hunks_data[hunk_name] = []
        
        return hunks_data
    
    def check_diff_direction(self, hunks_data, final_code_lines):
        """检查diff方向是否正确"""
        fix_info = []
        total_fixes = 0
        
        for hunk_name, hunks_list in hunks_data.items():
            for i, hunk in enumerate(hunks_list):
                diff_content = hunk.get('diff_content', '')
                if not diff_content:
                    continue
                
                # 解析diff内容
                lines = diff_content.split('\\n')
                fixed_lines = []
                hunk_fixes = 0
                
                for line in lines:
                    if line.startswith('+') and len(line) > 1:
                        # 检查+行内容是否在最终代码中存在
                        line_content = line[1:].strip()
                        # 提取行号（如果有）
                        line_match = re.match(r'\s*(\d+):\s*(.*)', line_content)
                        if line_match:
                            line_num = int(line_match.group(1))
                            actual_content = line_match.group(2)
                            
                            # 检查是否在最终代码中
                            if line_num <= len(final_code_lines):
                                final_line = final_code_lines[line_num - 1].strip()
                                if actual_content not in final_line:
                                    print(f"  ⚠️ {hunk_name}[{i}]: +行内容不在最终代码中")
                                    print(f"    期望: {actual_content}")
                                    print(f"    实际: {final_line}")
                        
                        fixed_lines.append(line)
                        
                    elif line.startswith('-') and len(line) > 1:
                        # 检查-行内容是否在最终代码中存在
                        line_content = line[1:].strip()
                        line_match = re.match(r'\s*(\d+):\s*(.*)', line_content)
                        if line_match:
                            line_num = int(line_match.group(1))
                            actual_content = line_match.group(2)
                            
                            # 检查是否在最终代码中
                            if line_num <= len(final_code_lines):
                                final_line = final_code_lines[line_num - 1].strip()
                                if actual_content in final_line:
                                    # 在最终代码中存在，应该是+
                                    fixed_line = '+' + line[1:]
                                    fixed_lines.append(fixed_line)
                                    hunk_fixes += 1
                                    total_fixes += 1
                                    print(f"  🔧 {hunk_name}[{i}]: 修复方向 - → +")
                                else:
                                    # 不在最终代码中，确实应该删除
                                    fixed_lines.append(line)
                            else:
                                fixed_lines.append(line)
                        else:
                            fixed_lines.append(line)
                    else:
                        fixed_lines.append(line)
                
                # 更新diff内容
                if hunk_fixes > 0:
                    hunk['diff_content'] = '\\n'.join(fixed_lines)
                    fix_info.append(f"{hunk_name}[{i}]: {hunk_fixes}个修复")
        
        return total_fixes, fix_info
    
    def merge_single_file(self, benchmark_id):
        """合并单个文件"""
        print(f"🔄 处理 {benchmark_id}...")
        
        # 读取GPT-5结果
        gpt5_filename = f"{benchmark_id}.txt"
        gpt5_content = self.read_gpt5_result(gpt5_filename)
        
        # 读取GPT-4o模板
        gpt4o_filename = f"{benchmark_id}.json"
        gpt4o_filepath = os.path.join(self.gpt4o_template_dir, gpt4o_filename)
        
        with open(gpt4o_filepath, 'r', encoding='utf-8') as f:
            gpt4o_data = json.load(f)
        
        # 解析GPT-5的hunks
        hunks_data = self.parse_hunks_from_gpt5(gpt5_content)
        
        # 检查diff方向
        final_code_lines = gpt4o_data.get('final_code_with_annotations', '').split('\n')
        total_fixes, fix_info = self.check_diff_direction(hunks_data, final_code_lines)
        
        # 创建合并后的数据
        merged_data = {
            'benchmark_id': benchmark_id,
            'timestamp': datetime.now().isoformat(),
            'model_used': 'gpt-5-manual-20',
            'prompt_version': 'v9_improved',
            'selected_region': gpt4o_data.get('selected_region', ''),
            'target_implementation': gpt4o_data.get('target_implementation', ''),
            'final_code_with_annotations': gpt4o_data.get('final_code_with_annotations', ''),
            'prompt': gpt4o_data.get('prompt', {}),
            'llm_response': gpt5_content,
            'parsed_hunks': hunks_data,
            'validation_results': gpt4o_data.get('validation_results', {}),
            'fix_info': {
                'total_fixes': total_fixes,
                'fix_details': fix_info,
                'fixed_at': datetime.now().isoformat()
            },
            'original_benchmark': gpt4o_data.get('original_benchmark', {})
        }
        
        # 保存合并结果
        output_filepath = os.path.join(self.output_dir, f"{benchmark_id}.json")
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        
        if total_fixes > 0:
            print(f"  🔧 {benchmark_id}: 修复了 {total_fixes} 个diff方向问题")
        else:
            print(f"  ✅ {benchmark_id}: diff方向正确，无需修复")
        
        return {
            'benchmark_id': benchmark_id,
            'hunks_count': [len(hunks_data.get('hunks_3', [])), 
                           len(hunks_data.get('hunks_2', [])), 
                           len(hunks_data.get('hunks_1', []))],
            'fixes_applied': total_fixes
        }
    
    def merge_all_files(self):
        """合并所有文件"""
        print("=== 开始合并GPT-5结果（后10条数据）===")
        
        # 获取所有txt文件
        txt_files = [f for f in os.listdir(self.gpt5_result_dir) if f.endswith('.txt')]
        
        results = []
        total_fixes = 0
        
        for txt_file in sorted(txt_files):
            benchmark_id = txt_file[:-4]  # 移除.txt后缀
            result = self.merge_single_file(benchmark_id)
            results.append(result)
            total_fixes += result['fixes_applied']
        
        # 保存摘要
        summary = {
            'timestamp': datetime.now().isoformat(),
            'model_used': 'gpt-5-manual-20',
            'prompt_version': 'v9_improved',
            'total_benchmarks': len(results),
            'total_fixes_applied': total_fixes,
            'results': results
        }
        
        summary_filepath = os.path.join(self.output_dir, 'gpt5_manual_20_summary.json')
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 合并完成！")
        print(f"处理文件数: {len(results)}")
        print(f"总修复数: {total_fixes}")
        print(f"输出目录: {self.output_dir}")
        
        return summary

if __name__ == "__main__":
    merger = GPT5ResultsMerger20()
    summary = merger.merge_all_files()
