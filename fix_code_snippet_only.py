#!/usr/bin/env python3
"""
只修复代码片段问题，不动Recent Changes部分
"""
import json
import re

def fix_code_snippet_in_prompt(prompt_text, original_benchmark):
    """只修复prompt中的代码片段部分，保持其他部分不变"""
    
    # 从原始benchmark中获取正确的代码片段
    original_prompt = original_benchmark['prompt']
    
    # 提取原始的代码片段
    snippet_marker = 'And here is the code snippet you are asked to modify:'
    snippet_start = original_prompt.find(snippet_marker)
    if snippet_start != -1:
        java_start = original_prompt.find('```java\n', snippet_start) + 8
        java_end = original_prompt.find('\n```', java_start)
        if java_start > 7 and java_end > java_start:
            correct_snippet = original_prompt[java_start:java_end].strip()
        else:
            print("无法从原始benchmark提取代码片段")
            return prompt_text
    else:
        print("原始benchmark中没有找到代码片段标记")
        return prompt_text
    
    # 在当前prompt中找到代码片段位置并替换
    current_snippet_start = prompt_text.find(snippet_marker)
    if current_snippet_start != -1:
        # 找到```java和```的位置
        current_java_start = prompt_text.find('```java\n', current_snippet_start)
        current_java_end = prompt_text.find('\n```', current_java_start)
        
        if current_java_start != -1 and current_java_end != -1:
            # 替换代码片段内容
            before = prompt_text[:current_java_start + 8]  # 包含```java\n
            after = prompt_text[current_java_end:]  # 从\n```开始
            
            new_prompt = before + correct_snippet + after
            print(f"✅ 代码片段已修复: {correct_snippet[:50]}...")
            return new_prompt
        else:
            print("当前prompt中代码片段格式有问题")
            return prompt_text
    else:
        print("当前prompt中没有找到代码片段标记")
        return prompt_text

def main():
    # 读取原始benchmark以获取正确的代码片段
    original_file = 'benchmark/nl2code_F20-40.jsonl'
    current_file = 'benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl'
    output_file = 'benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed.jsonl'
    
    # 加载原始数据
    original_data = {}
    with open(original_file, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            original_data[item['id']] = item
    
    print(f"📖 加载了 {len(original_data)} 条原始数据")
    
    # 处理当前文件
    fixed_count = 0
    with open(current_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            item = json.loads(line.strip())
            item_id = item['id']
            
            if item_id in original_data:
                # 修复代码片段
                original_item = original_data[item_id]
                fixed_prompt = fix_code_snippet_in_prompt(item['prompt'], original_item)
                
                if fixed_prompt != item['prompt']:
                    item['prompt'] = fixed_prompt
                    fixed_count += 1
                    print(f"✅ 修复第{line_num}条: {item_id}")
                else:
                    print(f"⚠️  第{line_num}条无需修复: {item_id}")
            else:
                print(f"❌ 第{line_num}条在原始数据中未找到: {item_id}")
            
            # 写入结果
            outfile.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n🎉 修复完成!")
    print(f"✅ 修复了 {fixed_count} 条数据的代码片段")
    print(f"📄 输出文件: {output_file}")

if __name__ == "__main__":
    main()
