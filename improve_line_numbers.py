#!/usr/bin/env python3
"""改进分离式benchmark的行号处理"""

import json
import re

def add_line_numbers_to_context(context_lines, start_line_num=1):
    """为context添加行号，如果已有行号则跳过"""
    if not context_lines.strip():
        return context_lines

    lines = context_lines.split('\n')
    numbered_lines = []
    current_line = start_line_num

    for line in lines:
        if line.strip():  # 只为非空行添加行号
            # 检查是否已经有行号格式
            if re.match(r'^\s*\d+:\s*', line):
                # 已经有行号，直接使用
                numbered_lines.append(line)
            else:
                # 没有行号，添加行号
                numbered_lines.append(f"{current_line:3d}: {line}")
            current_line += 1
        else:
            numbered_lines.append("")

    return '\n'.join(numbered_lines)

def improve_benchmark_item(item):
    """改进单个benchmark项目的行号"""
    prompt = item['prompt']
    
    # 提取context above和below
    above_match = re.search(r'The context above is:\n```java\n(.*?)\n```', prompt, re.DOTALL)
    below_match = re.search(r'The context below is:\n```java\n(.*?)\n```', prompt, re.DOTALL)
    
    if above_match and below_match:
        context_above = above_match.group(1)
        context_below = below_match.group(1)
        
        # 为context above添加行号（从1开始）
        above_lines = [line for line in context_above.split('\n') if line.strip()]
        numbered_above = add_line_numbers_to_context('\n'.join(above_lines), 1)
        
        # 为context below添加行号（接续above的行号）
        below_lines = [line for line in context_below.split('\n') if line.strip()]
        start_line_for_below = len(above_lines) + 2  # +2 是为目标实现预留空间
        numbered_below = add_line_numbers_to_context('\n'.join(below_lines), start_line_for_below)
        
        # 替换prompt中的内容
        new_prompt = prompt.replace(
            f'The context above is:\n```java\n{context_above}\n```',
            f'The context above is:\n```java\n{numbered_above}\n```'
        )
        new_prompt = new_prompt.replace(
            f'The context below is:\n```java\n{context_below}\n```',
            f'The context below is:\n```java\n{numbered_below}\n```'
        )
        
        item['prompt'] = new_prompt
    
    return item

def main():
    """主函数"""
    print("🔧 改进分离式benchmark的行号处理...")
    
    input_file = 'benchmark/nl2code_java_all_20_with_rc_separated.jsonl'
    output_file = 'benchmark/nl2code_java_all_20_with_rc_separated_improved.jsonl'
    
    processed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            try:
                item = json.loads(line.strip())
                improved_item = improve_benchmark_item(item)
                
                # 写入新文件
                outfile.write(json.dumps(improved_item, ensure_ascii=False) + '\n')
                processed_count += 1
                
                print(f"✅ 改进完成 {line_num}/20: {item.get('id', 'unknown')}")
                
            except Exception as e:
                print(f"❌ 处理第{line_num}行时出错: {e}")
    
    print(f"\n🎉 改进完成!")
    print(f"✅ 处理条数: {processed_count}")
    print(f"📁 输出文件: {output_file}")

if __name__ == "__main__":
    main()
