#!/usr/bin/env python3
"""
生成分离式context + RC的新版本benchmark
基于nl2code_java_all_20_with_rc.jsonl生成新的格式
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

def extract_external_imports(prompt: str) -> str:
    """从prompt中提取external imports"""
    match = re.search(r'Below are some information from external classes imported by current file:\n```java\n(.*?)\n```', prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_user_edit_instruction(prompt: str) -> str:
    """从prompt中提取用户编辑指令"""
    match = re.search(r'The new feature is (.+?)\.', prompt)
    if match:
        return match.group(1).strip()
    return ""

def extract_selected_code_snippet(prompt: str) -> str:
    """从prompt中提取选中的代码片段"""
    match = re.search(r'And here is the code snippet you are asked to modify:\n```java\n(.*?)\n```', prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_rc_diffs(prompt: str) -> Tuple[str, str, str]:
    """从prompt中提取3个RC diff"""
    rc3_match = re.search(r'### Recent Change 3 \(Earliest preparation work\)\n```diff\n(.*?)\n```', prompt, re.DOTALL)
    rc2_match = re.search(r'### Recent Change 2 \(Intermediate preparation\)\n```diff\n(.*?)\n```', prompt, re.DOTALL)
    rc1_match = re.search(r'### Recent Change 1 \(Latest preparation work\)\n```diff\n(.*?)\n```', prompt, re.DOTALL)
    
    rc3 = rc3_match.group(1).strip() if rc3_match else ""
    rc2 = rc2_match.group(1).strip() if rc2_match else ""
    rc1 = rc1_match.group(1).strip() if rc1_match else ""
    
    return rc3, rc2, rc1

def parse_code_with_line_numbers(code_content: str) -> List[Tuple[int, str]]:
    """解析带行号的代码内容，保留原始缩进"""
    lines = []
    for line in code_content.split('\n'):
        if not line.strip():
            continue
        # 匹配行号格式: "  1: code content"，保留code content的原始缩进
        match = re.match(r'^\s*(\d+):\s?(.*)', line)
        if match:
            line_num = int(match.group(1))
            content = match.group(2)  # 保留原始缩进，不再strip
            lines.append((line_num, content))
    return lines

def find_target_implementation_position(lines: List[Tuple[int, str]], selected_snippet: str) -> Optional[Tuple[int, int]]:
    """找到目标实现在代码中的位置"""
    # 提取选中代码片段的方法签名
    snippet_lines = [line.strip() for line in selected_snippet.split('\n') if line.strip()]
    if not snippet_lines:
        return None
    
    # 查找方法签名在代码中的位置
    first_snippet_line = snippet_lines[0]
    
    for i, (line_num, content) in enumerate(lines):
        if first_snippet_line in content or content in first_snippet_line:
            # 找到了起始位置，现在需要找到结束位置
            start_line = line_num
            
            # 简单的启发式：找到下一个方法或类结束
            brace_count = 0
            end_line = start_line
            
            for j in range(i, len(lines)):
                _, line_content = lines[j]
                end_line = lines[j][0]
                
                # 计算大括号
                brace_count += line_content.count('{') - line_content.count('}')
                
                # 如果找到了完整的方法（大括号平衡）
                if brace_count == 0 and j > i:
                    break
            
            return (start_line, end_line)
    
    return None

def split_code_context(lines: List[Tuple[int, str]], target_start: int, target_end: int) -> Tuple[str, str]:
    """将代码分割为上方和下方context，保持原始格式"""
    context_above = []
    context_below = []

    for line_num, content in lines:
        if line_num < target_start:
            # 保持原始格式，包括行号和缩进
            context_above.append(f"{line_num:3d}: {content}")
        elif line_num > target_end:
            # 保持原始格式，包括行号和缩进
            context_below.append(f"{line_num:3d}: {content}")

    return '\n'.join(context_above), '\n'.join(context_below)

def generate_separated_prompt(template: str, external_imports: str, context_above: str, 
                            context_below: str, rc3: str, rc2: str, rc1: str, 
                            user_instruction: str, selected_snippet: str) -> str:
    """生成分离式prompt"""
    return template.format(
        external_imports=external_imports,
        context_above_with_line_numbers=context_above,
        context_below_with_line_numbers=context_below,
        rc_3_diff=rc3,
        rc_2_diff=rc2,
        rc_1_diff=rc1,
        user_edit_instruction=user_instruction,
        selected_code_snippet=selected_snippet
    )

def process_benchmark_item(item: Dict, template: str) -> Dict:
    """处理单个benchmark项目"""
    prompt = item['prompt']
    
    # 提取各个组件
    external_imports = extract_external_imports(prompt)
    user_instruction = extract_user_edit_instruction(prompt)
    selected_snippet = extract_selected_code_snippet(prompt)
    rc3, rc2, rc1 = extract_rc_diffs(prompt)
    
    # 从prompt中提取完整代码内容
    code_match = re.search(r'## Current File Content\n```java\n(.*?)\n```', prompt, re.DOTALL)
    if not code_match:
        print(f"Warning: Could not extract code content for {item.get('id', 'unknown')}")
        return item
    
    full_code = code_match.group(1)
    lines = parse_code_with_line_numbers(full_code)
    
    # 找到目标实现位置
    target_pos = find_target_implementation_position(lines, selected_snippet)
    if not target_pos:
        print(f"Warning: Could not find target position for {item.get('id', 'unknown')}")
        return item
    
    target_start, target_end = target_pos
    
    # 分割代码
    context_above, context_below = split_code_context(lines, target_start, target_end)
    
    # 生成新的prompt
    new_prompt = generate_separated_prompt(
        template, external_imports, context_above, context_below,
        rc3, rc2, rc1, user_instruction, selected_snippet
    )
    
    # 创建新的item
    new_item = item.copy()
    new_item['prompt'] = new_prompt
    
    return new_item

def main():
    """主函数"""
    print("🚀 开始生成分离式context + RC的benchmark...")
    
    # 读取模板
    with open('evaluation_prompt_template_v4_separated.txt', 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 读取原始数据
    input_file = 'benchmark/nl2code_java_all_20_with_rc.jsonl'
    output_file = 'benchmark/nl2code_java_all_20_with_rc_separated.jsonl'
    
    processed_count = 0
    error_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            try:
                item = json.loads(line.strip())
                new_item = process_benchmark_item(item, template)
                
                # 写入新文件
                outfile.write(json.dumps(new_item, ensure_ascii=False) + '\n')
                processed_count += 1
                
                print(f"✅ 处理完成 {line_num}/20: {item.get('id', 'unknown')}")
                
            except Exception as e:
                print(f"❌ 处理第{line_num}行时出错: {e}")
                error_count += 1
    
    print(f"\n🎉 处理完成!")
    print(f"✅ 成功处理: {processed_count} 条")
    print(f"❌ 处理失败: {error_count} 条")
    print(f"📁 输出文件: {output_file}")

if __name__ == "__main__":
    main()
