#!/usr/bin/env python3
"""
只修复diff顺序问题：先删除行，再添加行，最后上下文行
保持行号格式不变
"""
import json
import re

def fix_diff_order(diff_text):
    """修复diff块的行顺序：先删除行，再添加行，最后上下文行"""
    lines = diff_text.split('\n')
    
    header_lines = []
    minus_lines = []
    plus_lines = []
    space_lines = []
    
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
            
        if line.startswith('@@'):
            header_lines.append(line)
        elif re.match(r'^-\s*\d+:', line):
            minus_lines.append(line)
        elif re.match(r'^\+\s*\d+:', line):
            plus_lines.append(line)
        elif re.match(r'^\s+\d+:', line):
            space_lines.append(line)
        else:
            # 其他行保持原位置
            header_lines.append(line)
    
    # 按行号排序每组
    def extract_line_num(line):
        match = re.search(r'\d+:', line)
        return int(match.group().rstrip(':')) if match else 999999
    
    minus_lines.sort(key=extract_line_num)
    plus_lines.sort(key=extract_line_num)
    space_lines.sort(key=extract_line_num)
    
    # 重新组合：header + 删除行 + 添加行 + 上下文行
    result_lines = header_lines + minus_lines + plus_lines + space_lines
    
    return '\n'.join(result_lines)

def fix_recent_changes_order(prompt_text):
    """修复Recent Changes中所有diff块的顺序"""
    
    # 找到Recent Changes部分
    rc_start = prompt_text.find('## Recent Changes Context')
    rc_end = prompt_text.find('These recent changes show the development progression')
    
    if rc_start == -1 or rc_end == -1:
        print("未找到Recent Changes部分")
        return prompt_text
    
    before = prompt_text[:rc_start]
    after = prompt_text[rc_end:]
    rc_section = prompt_text[rc_start:rc_end]
    
    # 修复每个diff块
    def replace_diff(match):
        header = match.group(1)
        diff_content = match.group(2)
        fixed_diff = fix_diff_order(diff_content)
        return f"{header}\n```diff\n{fixed_diff}\n```"
    
    # 替换所有diff块
    fixed_rc = re.sub(
        r'(### Recent Change \d+ \([^)]+\))\s*```diff\s*(.*?)```',
        replace_diff,
        rc_section,
        flags=re.DOTALL
    )
    
    return before + fixed_rc + after

def main():
    input_file = 'benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed.jsonl'
    output_file = 'benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed_ordered.jsonl'
    
    fixed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            item = json.loads(line.strip())
            
            # 修复diff顺序
            original_prompt = item['prompt']
            fixed_prompt = fix_recent_changes_order(original_prompt)
            
            if fixed_prompt != original_prompt:
                item['prompt'] = fixed_prompt
                fixed_count += 1
                print(f"✅ 修复第{line_num}条diff顺序: {item['id']}")
            else:
                print(f"⚠️  第{line_num}条无需修复: {item['id']}")
            
            # 写入结果
            outfile.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n🎉 diff顺序修复完成!")
    print(f"✅ 修复了 {fixed_count} 条数据")
    print(f"📄 输出文件: {output_file}")

if __name__ == "__main__":
    main()
