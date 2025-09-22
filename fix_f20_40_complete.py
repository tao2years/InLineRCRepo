#!/usr/bin/env python3
"""
完全重新构造F20-40 benchmark文件
从gpt5_results_20-40目录和原始benchmark数据构造完整的separated格式
"""

import json
import os
import re
from typing import Dict, List, Any

def load_original_benchmark_data():
    """加载原始benchmark数据"""
    original_data = {}
    
    # 加载原始F20-40数据
    with open('benchmark/nl2code_F20-40.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                original_data[data['id']] = data
    
    print(f"加载了 {len(original_data)} 个原始条目")
    return original_data

def parse_gpt5_file(file_path: str) -> Dict[str, Any]:
    """解析GPT-5结果文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取文件ID
    filename = os.path.basename(file_path)
    file_id = filename.replace('.txt', '')
    
    # 解析hunks_3, hunks_2, hunks_1
    hunks = {}
    for hunk_name in ['hunks_3', 'hunks_2', 'hunks_1']:
        # GPT-5文件中使用 hunks\_3 格式（转义下划线）
        hunk_number = hunk_name.split('_')[1]  # 提取数字部分

        # 使用更简单的方法：先找到section，再提取JSON
        section_patterns = [
            f'### hunks\\_{hunk_number}',  # hunks\_3 格式
            f'### {hunk_name}',           # hunks_3 格式
        ]

        found = False
        for section_pattern in section_patterns:
            # 找到section的开始位置
            section_start = content.find(section_pattern)
            if section_start != -1:
                # 从section开始位置查找JSON块
                json_start = content.find('```json', section_start)
                if json_start != -1:
                    json_start += 7  # 跳过 ```json
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                        try:
                            hunks[hunk_name] = json.loads(json_content)
                            found = True
                            print(f"✅ 成功解析 {hunk_name}: {len(hunks[hunk_name])} 个hunks")
                            break
                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误 {hunk_name}: {e}")
                            continue

        if not found:
            print(f"警告: 在 {filename} 中未找到 {hunk_name}")
            hunks[hunk_name] = []
    
    return {
        'id': file_id,
        'hunks': hunks
    }

def add_line_numbers_to_code(code_content: str, start_line: int = 1) -> str:
    """为代码添加行号"""
    lines = code_content.split('\n')
    numbered_lines = []
    
    for i, line in enumerate(lines):
        line_num = start_line + i
        numbered_lines.append(f"{line_num:3d}: {line}")
    
    return '\n'.join(numbered_lines)

def normalize_code_content(content: str) -> str:
    """标准化代码内容用于匹配，但保留缩进结构"""
    if not content:
        return ""

    # 保留缩进，只标准化行内空格
    lines = content.split('\n')
    normalized_lines = []
    for line in lines:
        # 保留行首缩进，标准化行内空格
        stripped = line.strip()
        if stripped:
            # 标准化引号和行尾标点
            normalized = stripped.replace('\\"', '"').replace("\\'", "'")
            normalized = re.sub(r'[;,]\s*$', '', normalized)
            normalized_lines.append(normalized.lower())

    return '\n'.join(normalized_lines)

def preserve_original_indentation(content: str, original_content: str) -> str:
    """保留原始代码的缩进格式"""
    if not content or not original_content:
        return content

    # 如果内容匹配，返回原始格式
    content_normalized = normalize_code_content(content)
    original_normalized = normalize_code_content(original_content)

    if content_normalized in original_normalized or original_normalized in content_normalized:
        return original_content.strip()

    return content

def find_best_match_in_context(target_content: str, context_lines: List[str]) -> tuple:
    """在context中找到最佳匹配的行号和原始内容"""
    if not target_content.strip():
        return -1, target_content

    target_normalized = normalize_code_content(target_content)
    if not target_normalized:
        return -1, target_content

    best_match_line = -1
    best_score = 0
    best_original_content = target_content

    for i, context_line in enumerate(context_lines):
        # 提取行号和内容
        if ':' in context_line and context_line.strip():
            try:
                line_num_str = context_line.split(':', 1)[0].strip()
                if line_num_str.isdigit():
                    line_content = context_line.split(':', 1)[1]  # 保留原始缩进
                    line_normalized = normalize_code_content(line_content)

                    if not line_normalized:
                        continue

                    # 计算相似度
                    if target_normalized == line_normalized:
                        # 完全匹配，返回原始格式的内容
                        return int(line_num_str), line_content.strip()

                    # 检查包含关系
                    if target_normalized in line_normalized or line_normalized in target_normalized:
                        score = 0.9
                        if score > best_score:
                            best_score = score
                            best_match_line = int(line_num_str)
                            best_original_content = line_content.strip()

                    # 关键词匹配
                    target_words = set(re.findall(r'\w+', target_normalized))
                    line_words = set(re.findall(r'\w+', line_normalized))

                    if target_words and line_words:
                        overlap = len(target_words & line_words)
                        total = len(target_words | line_words)
                        if total > 0:
                            score = overlap / total
                            # 提高阈值到0.8，确保更准确的匹配
                            if score >= 0.8 and score > best_score:
                                best_score = score
                                best_match_line = int(line_num_str)
                                best_original_content = line_content.strip()
            except (ValueError, IndexError):
                continue

    if best_score >= 0.8:
        return best_match_line, best_original_content
    else:
        return -1, target_content

def parse_unified_diff_header(header_line: str) -> tuple:
    """解析unified diff的@@头，返回(old_start, old_count, new_start, new_count)"""
    # 格式: @@ -old_start,old_count +new_start,new_count @@
    match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', header_line)
    if match:
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1
        return old_start, old_count, new_start, new_count
    return None, None, None, None

def format_diff_with_line_numbers(diff_content: str, full_context: str) -> str:
    """为diff内容添加正确的行号标注，保留原始缩进"""
    if not diff_content.strip():
        return diff_content

    lines = diff_content.split('\n')
    formatted_lines = []
    context_lines = full_context.split('\n')

    # 当前处理状态
    old_line_num = 1
    new_line_num = 1

    for line in lines:
        if line.startswith('@@'):
            # 解析diff头，获取起始行号
            old_start, old_count, new_start, new_count = parse_unified_diff_header(line)
            if old_start is not None:
                old_line_num = old_start
                new_line_num = new_start
            formatted_lines.append(line)

        elif line.startswith('+') and not line.startswith('+++'):
            # 处理新增行
            content = line[1:]  # 保留原始空格
            if content.strip():  # 只检查是否为空行
                # 在context中查找这行代码的真实位置和原始格式
                real_line_num, original_content = find_best_match_in_context(content, context_lines)
                if real_line_num > 0:
                    formatted_lines.append(f"+ {real_line_num:2d}: {original_content}")
                else:
                    # 如果找不到，使用预期的新行号和原始内容
                    formatted_lines.append(f"+ {new_line_num:2d}: {content.strip()}")
                new_line_num += 1
            else:
                formatted_lines.append(line)

        elif line.startswith('-') and not line.startswith('---'):
            # 处理删除行
            content = line[1:]  # 保留原始空格
            if content.strip():  # 只检查是否为空行
                # 删除的行使用原始行号和内容
                formatted_lines.append(f"- {old_line_num:2d}: {content.strip()}")
                old_line_num += 1
            else:
                formatted_lines.append(line)

        elif line.startswith(' '):
            # 上下文行（未变更的行）
            content = line[1:]  # 保留原始空格
            if content.strip():  # 只检查是否为空行
                # 在context中查找真实行号和原始格式
                real_line_num, original_content = find_best_match_in_context(content, context_lines)
                if real_line_num > 0:
                    formatted_lines.append(f"  {real_line_num:2d}: {original_content}")
                else:
                    # 使用当前行号和原始内容
                    formatted_lines.append(f"  {old_line_num:2d}: {content.strip()}")
                old_line_num += 1
                new_line_num += 1
            else:
                formatted_lines.append(line)
        else:
            # 其他行（如空行），保持不变
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)

def format_recent_changes(hunks: Dict[str, List], full_context: str) -> str:
    """格式化Recent Changes"""
    rc_parts = []

    # RC3 (Earliest preparation work)
    if hunks.get('hunks_3'):
        rc_parts.append("### Recent Change 3 (Earliest preparation work)")
        for hunk in hunks['hunks_3']:
            rc_parts.append("```diff")
            diff_content = hunk.get('diff_content', '')
            formatted_diff = format_diff_with_line_numbers(diff_content, full_context)
            rc_parts.append(formatted_diff)
            rc_parts.append("```")
        rc_parts.append("")

    # RC2 (Intermediate preparation)
    if hunks.get('hunks_2'):
        rc_parts.append("### Recent Change 2 (Intermediate preparation)")
        for hunk in hunks['hunks_2']:
            rc_parts.append("```diff")
            diff_content = hunk.get('diff_content', '')
            formatted_diff = format_diff_with_line_numbers(diff_content, full_context)
            rc_parts.append(formatted_diff)
            rc_parts.append("```")
        rc_parts.append("")

    # RC1 (Latest preparation work)
    if hunks.get('hunks_1'):
        rc_parts.append("### Recent Change 1 (Latest preparation work)")
        for hunk in hunks['hunks_1']:
            rc_parts.append("```diff")
            diff_content = hunk.get('diff_content', '')
            formatted_diff = format_diff_with_line_numbers(diff_content, full_context)
            rc_parts.append(formatted_diff)
            rc_parts.append("```")
        rc_parts.append("")

    return '\n'.join(rc_parts)

def extract_context_from_prompt(prompt: str) -> Dict[str, str]:
    """从原始prompt中提取context above和context below"""
    # 提取context above
    above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
    context_above = above_match.group(1) if above_match else ""
    
    # 提取context below
    below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
    context_below = below_match.group(1) if below_match else ""
    
    # 提取external classes
    external_match = re.search(r'Below are some information from external classes imported by current file:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
    external_classes = external_match.group(1) if external_match else ""
    
    return {
        'context_above': context_above,
        'context_below': context_below,
        'external_classes': external_classes
    }

def calculate_line_numbers(context_above: str, good_example: str) -> Dict[str, int]:
    """计算行号分配"""
    above_lines = len(context_above.split('\n')) if context_above.strip() else 0
    good_lines = len(good_example.split('\n')) if good_example.strip() else 0
    
    # context above从1开始
    above_start = 1
    
    # good example紧接着context above
    good_start = above_start + above_lines
    
    # context below在good example之后，留一些间隔
    below_start = good_start + good_lines + 2
    
    return {
        'above_start': above_start,
        'good_start': good_start,
        'below_start': below_start
    }

def create_complete_prompt(original_data: Dict, hunks: Dict[str, List]) -> str:
    """创建完整的prompt"""
    # 提取原始数据
    contexts = extract_context_from_prompt(original_data['prompt'])
    good_example = original_data['good_example_response']
    query = original_data['extra_content']['query']

    # 计算行号
    line_nums = calculate_line_numbers(contexts['context_above'], good_example)

    # 为代码添加行号
    context_above_numbered = add_line_numbers_to_code(contexts['context_above'], line_nums['above_start'])
    context_below_numbered = add_line_numbers_to_code(contexts['context_below'], line_nums['below_start'])

    # 构建完整的context用于行号匹配
    full_context = context_above_numbered + '\n' + context_below_numbered

    # 格式化Recent Changes（传入完整context用于行号匹配）
    recent_changes = format_recent_changes(hunks, full_context)

    # 构建完整prompt
    prompt = f"""A user is developing a new feature. Based on the known code information, help him implement this new feature.

Below are some information from external classes imported by current file:
```java
{contexts['external_classes']}
```

The context above is:
```java
{context_above_numbered}
```

The context below is:
```java
{context_below_numbered}
```

## Recent Changes Context
Here are some recent changes that were made to this file to help you understand the development context:

{recent_changes}

These recent changes show the development progression leading up to the current task.

The new feature is {query}.

And here is the code snippet you are asked to modify:
```java
{original_data['prompt'].split('And here is the code snippet you are asked to modify:')[-1].split('```java')[-1].split('```')[0].strip()}
```

Please analyze the mission carefully and thoroughly first, and then give a definitely runnable code. You should put your code between ```java and ```."""

    return prompt

def main():
    """主函数"""
    print("开始重新构造F20-40 benchmark...")
    
    # 加载原始数据
    original_data = load_original_benchmark_data()
    
    # 处理所有GPT-5结果文件
    gpt5_dir = 'gpt5_results_20-40'
    benchmark_entries = []
    
    for filename in sorted(os.listdir(gpt5_dir)):
        if filename.endswith('.txt'):
            file_path = os.path.join(gpt5_dir, filename)
            file_id = filename.replace('.txt', '')
            
            print(f"处理文件: {filename}")
            
            if file_id not in original_data:
                print(f"警告: 未找到 {file_id} 的原始数据")
                continue
            
            try:
                # 解析GPT-5结果
                gpt5_data = parse_gpt5_file(file_path)
                
                # 创建完整prompt
                new_prompt = create_complete_prompt(original_data[file_id], gpt5_data['hunks'])
                
                # 创建新的benchmark条目
                new_entry = original_data[file_id].copy()
                new_entry['prompt'] = new_prompt
                
                benchmark_entries.append(new_entry)
                print(f"✅ {file_id} 处理成功")
                
            except Exception as e:
                print(f"❌ 处理 {filename} 时出错: {e}")
                continue
    
    # 保存结果
    output_file = 'benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in benchmark_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"\n🎉 转换完成！")
    print(f"成功处理: {len(benchmark_entries)}/20 条数据")
    print(f"输出文件: {output_file}")

if __name__ == "__main__":
    main()
