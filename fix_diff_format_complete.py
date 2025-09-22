#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复benchmark文件中的diff格式问题
- 移除diff块中的行号标注
- 保持原始代码缩进
- 移除多余的空行
"""

import json
import os
import re
from typing import Dict, List, Tuple


def parse_gpt5_file(file_path: str) -> Dict:
    """解析GPT-5结果文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {}
    
    # 解析hunks_3
    hunks3_start = content.find('### hunks_3') if '### hunks_3' in content else content.find('### hunks\\_3')
    hunks2_start = content.find('### hunks_2') if '### hunks_2' in content else content.find('### hunks\\_2')
    
    if hunks3_start != -1 and hunks2_start != -1:
        hunks3_section = content[hunks3_start:hunks2_start]
        json_start = hunks3_section.find('[')
        json_end = hunks3_section.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            try:
                result['hunks_3'] = json.loads(hunks3_section[json_start:json_end])
            except json.JSONDecodeError:
                result['hunks_3'] = []
    
    # 解析hunks_2
    hunks1_start = content.find('### hunks_1') if '### hunks_1' in content else content.find('### hunks\\_1')
    
    if hunks2_start != -1 and hunks1_start != -1:
        hunks2_section = content[hunks2_start:hunks1_start]
        json_start = hunks2_section.find('[')
        json_end = hunks2_section.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            try:
                result['hunks_2'] = json.loads(hunks2_section[json_start:json_end])
            except json.JSONDecodeError:
                result['hunks_2'] = []
    
    # 解析hunks_1
    if hunks1_start != -1:
        hunks1_section = content[hunks1_start:]
        json_start = hunks1_section.find('[')
        json_end = hunks1_section.rfind(']') + 1
        if json_start != -1 and json_end > json_start:
            try:
                result['hunks_1'] = json.loads(hunks1_section[json_start:json_end])
            except json.JSONDecodeError:
                result['hunks_1'] = []
    
    return result


def format_recent_change(hunks_data: List[Dict], change_number: int) -> str:
    """格式化Recent Change，保持原始diff格式"""
    if not hunks_data:
        return ""
    
    change_names = {3: "Earliest preparation work", 2: "Intermediate preparation", 1: "Latest preparation work"}
    change_name = change_names.get(change_number, f"Change {change_number}")
    
    result = f"### Recent Change {change_number} ({change_name})\n```diff\n"
    
    for hunk in hunks_data:
        diff_content = hunk.get('diff_content', '')
        if diff_content:
            # 直接使用原始diff内容，不添加行号
            result += diff_content
            if not diff_content.endswith('\n'):
                result += '\n'
    
    result += "```\n\n"
    return result


def fix_recent_changes_format(prompt: str, gpt5_data: Dict) -> str:
    """修复prompt中的Recent Changes格式"""

    # 找到Recent Changes部分
    recent_changes_start = prompt.find('## Recent Changes Context')
    if recent_changes_start == -1:
        return prompt

    # 找到Recent Changes部分的结束
    suffix_start = prompt.find('\nThe new feature is', recent_changes_start)
    if suffix_start == -1:
        suffix_start = len(prompt)

    # 提取前缀和后缀
    prefix = prompt[:recent_changes_start]
    suffix = prompt[suffix_start:]

    # 生成新的Recent Changes
    recent_changes = "\n## Recent Changes Context\n"
    recent_changes += "Here are some recent changes that were made to this file to help you understand the development context:\n\n"

    # 按照3->2->1的顺序添加Recent Changes
    for change_num in [3, 2, 1]:
        hunks_key = f'hunks_{change_num}'
        if hunks_key in gpt5_data and gpt5_data[hunks_key]:
            recent_changes += format_recent_change(gpt5_data[hunks_key], change_num)

    recent_changes += "\nThese recent changes show the development progression leading up to the current task."

    # 组合完整的prompt
    return prefix + recent_changes + suffix


def process_single_entry(entry_data: Dict, gpt5_data: Dict) -> Dict:
    """处理单个条目，修复Recent Changes格式"""

    # 修复prompt中的Recent Changes格式
    fixed_prompt = fix_recent_changes_format(entry_data['prompt'], gpt5_data)

    # 创建新的数据条目
    result = {
        "prompt": fixed_prompt,
        "domain": entry_data.get("domain", "nl2code_java"),
        "id": entry_data.get("id", ""),
        "good_example_response": entry_data.get("good_example_response", ""),
        "reward_command": entry_data.get("reward_command", ""),
        "extra_content": entry_data.get("extra_content", {})
    }

    return result


def main():
    """主函数"""
    gpt5_dir = "gpt5_results_20-40"
    input_file = "benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl"
    output_file = "benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl"

    # 读取当前的benchmark数据
    with open(input_file, 'r', encoding='utf-8') as f:
        current_entries = [json.loads(line) for line in f]

    # 获取所有GPT-5文件
    gpt5_files = [f for f in os.listdir(gpt5_dir) if f.endswith('.txt')]

    # 创建GPT-5数据的映射
    gpt5_data_map = {}
    for gpt5_file in gpt5_files:
        gpt5_file_path = os.path.join(gpt5_dir, gpt5_file)
        try:
            gpt5_data = parse_gpt5_file(gpt5_file_path)
            # 从文件名提取ID
            file_id = gpt5_file.replace('.txt', '')
            gpt5_data_map[file_id] = gpt5_data
        except Exception as e:
            print(f"❌ 解析GPT-5文件失败: {gpt5_file}, 错误: {e}")

    results = []

    for entry in current_entries:
        entry_id = entry.get('id', '')
        if entry_id in gpt5_data_map:
            try:
                result = process_single_entry(entry, gpt5_data_map[entry_id])
                results.append(result)
                print(f"✅ 成功修复: {entry_id}")
            except Exception as e:
                print(f"❌ 修复失败: {entry_id}, 错误: {e}")
                results.append(entry)  # 保留原始数据
        else:
            print(f"⚠️  找不到对应的GPT-5数据: {entry_id}")
            results.append(entry)  # 保留原始数据

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"\n🎉 修复完成！")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 总条目数: {len(results)}")


if __name__ == "__main__":
    main()
