#!/usr/bin/env python3
"""验证生成的分离式benchmark格式"""

import json

def validate_benchmark():
    """验证benchmark格式"""
    print("=== 新格式验证 ===")
    
    # 读取第一条数据进行验证
    with open('benchmark/nl2code_java_all_20_with_rc_separated_final.jsonl', 'r', encoding='utf-8') as f:
        first_line = f.readline()
        data = json.loads(first_line)

    print("✅ 数据结构完整")
    print(f"✅ ID: {data.get('id', 'N/A')}")
    print(f"✅ Domain: {data.get('domain', 'N/A')}")

    # 检查prompt结构
    prompt = data['prompt']
    print("\n=== Prompt结构检查 ===")
    
    checks = [
        ('The context above is:', '包含context above'),
        ('The context below is:', '包含context below'),
        ('Recent Changes Context', '包含Recent Changes'),
        ('Recent Change 3', '包含RC3'),
        ('Recent Change 2', '包含RC2'),
        ('Recent Change 1', '包含RC1'),
        ('The new feature is', '包含功能描述'),
        ('And here is the code snippet', '包含代码片段')
    ]
    
    for check_text, description in checks:
        if check_text in prompt:
            print(f"✅ {description}")
        else:
            print(f"❌ 缺少{description}")

    print("\n=== 统计信息 ===")
    
    # 统计所有数据
    total_count = 0
    with open('benchmark/nl2code_java_all_20_with_rc_separated_final.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                total_count += 1
    
    print(f"✅ 总数据条数: {total_count}")
    
    # 对比原始文件
    original_count = 0
    with open('benchmark/nl2code_java_all_20_with_rc.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                original_count += 1
    
    print(f"✅ 原始数据条数: {original_count}")
    
    if total_count == original_count:
        print("✅ 数据条数匹配")
    else:
        print("❌ 数据条数不匹配")

    print("\n🎉 验证完成！")

if __name__ == "__main__":
    validate_benchmark()
