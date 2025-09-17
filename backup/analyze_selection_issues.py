#!/usr/bin/env python3
"""
分析选中区域和重叠问题
"""

import json
import re

def analyze_benchmark_structure():
    print("=== 分析Benchmark结构和选中区域问题 ===")
    
    with open('benchmark/nl2code_java_F10L.jsonl', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines[:3], 1):  # 分析前3条
        benchmark = json.loads(line)
        print(f"\n--- Benchmark {i} ---")
        
        # 提取选中区域
        selected_match = re.search(r'And here is the code snippet you are asked to modify:\s*```java\s*(.*?)\s*```', 
                                 benchmark['prompt'], re.DOTALL)
        if selected_match:
            selected_code = selected_match.group(1).strip()
            print(f"选中区域: {selected_code}")
        
        # 提取good_example_response
        good_example = benchmark['good_example_response']
        good_example_clean = good_example.replace('```java\n', '').replace('\n```', '').strip()
        print(f"good_example长度: {len(good_example_clean)}")
        print(f"good_example预览: {good_example_clean[:100]}...")
        
        # 分析重叠问题
        if selected_match:
            print(f"\n重叠分析:")
            print(f"- 选中区域是方法签名: {selected_code}")
            print(f"- good_example是完整实现")
            
            # 检查签名是否在good_example中
            if selected_code.replace('\n', '').replace(' ', '') in good_example_clean.replace('\n', '').replace(' ', ''):
                print("✅ 选中区域包含在good_example中")
            else:
                print("❌ 选中区域与good_example不匹配")

def analyze_rc_constraints():
    print("\n=== RC生成约束分析 ===")
    print("1. 不能修改good_example_response内容")
    print("2. 不能修改选中区域（方法签名）")
    print("3. 只能修改Context Above + Context Below中的其他部分")
    print("4. RC应该为实现选中区域的功能做准备")

def design_correct_prompt():
    print("\n=== 设计正确的prompt约束 ===")
    print("需要在prompt中明确:")
    print("1. [SELECTED_REGION] - 不可修改的选中区域")
    print("2. [GOOD_EXAMPLE] - 不可修改的目标实现")
    print("3. [MODIFIABLE_CONTEXT] - 可以修改的上下文区域")
    print("4. [RC_CONSTRAINTS] - RC只能修改可修改区域")

def analyze_insertion_logic():
    print("\n=== 分析插入逻辑 ===")
    print("最终状态构造:")
    print("1. Context Above + Context Below = 当前代码")
    print("2. 在合适位置插入good_example_response")
    print("3. 选中区域标记插入位置")
    print("4. RC倒推这个插入过程的准备工作")

if __name__ == "__main__":
    analyze_benchmark_structure()
    analyze_rc_constraints()
    design_correct_prompt()
    analyze_insertion_logic()
