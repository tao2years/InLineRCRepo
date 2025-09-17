#!/usr/bin/env python3
"""
调试prompt内容 - 检查发送给LLM的实际内容
"""

import json
import re

def analyze_first_benchmark():
    """分析第一条benchmark的prompt构造"""
    print("=== 分析第1条benchmark的prompt构造 ===")
    
    # 加载原始benchmark
    with open('benchmark/nl2code_java_F10L.jsonl', 'r', encoding='utf-8') as f:
        first_line = f.readline()
        benchmark = json.loads(first_line)
    
    print("原始任务:")
    task_match = re.search(r'The new feature is (.+?)\.', benchmark['prompt'])
    if task_match:
        print(f"  {task_match.group(1)}")
    
    print("\n要实现的方法:")
    method_match = re.search(r'```java\s*(.*?)\s*```', benchmark['prompt'].split('And here is the code snippet you are asked to modify:')[1])
    if method_match:
        print(f"  {method_match.group(1).strip()}")
    
    # 提取context
    context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', benchmark['prompt'], re.DOTALL)
    context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', benchmark['prompt'], re.DOTALL)
    
    context_above = context_above_match.group(1).strip() if context_above_match else ''
    context_below = context_below_match.group(1).strip() if context_below_match else ''
    
    print(f"\nContext Above 长度: {len(context_above)} 字符")
    print(f"Context Below 长度: {len(context_below)} 字符")
    
    # 构建完整内容（这是我们发送给LLM的）
    full_content = f"{context_above}\n{context_below}"
    
    print(f"\n发送给LLM的完整代码长度: {len(full_content)} 字符")
    print("\n发送给LLM的完整代码内容:")
    print("=" * 50)
    print(full_content)
    print("=" * 50)
    
    return benchmark, full_content

def analyze_prompt_template():
    """分析prompt模板"""
    print("\n=== 分析prompt模板 ===")
    
    with open('RC_prompt_v3.txt', 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    parts = prompt_content.split('(2) User Prompt')
    system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
    user_template = parts[1].strip()
    
    print("System Prompt:")
    print("-" * 30)
    print(system_prompt)
    print("-" * 30)
    
    print("\nUser Template:")
    print("-" * 30)
    print(user_template)
    print("-" * 30)
    
    return system_prompt, user_template

def construct_actual_prompt():
    """构造实际发送给LLM的prompt"""
    print("\n=== 构造实际发送的prompt ===")
    
    benchmark, full_content = analyze_first_benchmark()
    system_prompt, user_template = analyze_prompt_template()
    
    # 提取任务
    task_match = re.search(r'The new feature is (.+?)\.', benchmark['prompt'])
    task = task_match.group(1).strip() if task_match else ''
    
    # 构造用户prompt
    actual_user_prompt = user_template.format(
        instruction=task,
        full_file_content=full_content
    )
    
    print("实际发送给LLM的User Prompt:")
    print("=" * 60)
    print(actual_user_prompt)
    print("=" * 60)
    
    # 保存到文件
    with open('debug_actual_prompt.txt', 'w', encoding='utf-8') as f:
        f.write("=== SYSTEM PROMPT ===\n")
        f.write(system_prompt)
        f.write("\n\n=== USER PROMPT ===\n")
        f.write(actual_user_prompt)
    
    print(f"\n✅ 实际prompt已保存到: debug_actual_prompt.txt")
    
    return system_prompt, actual_user_prompt

def analyze_problem():
    """分析问题所在"""
    print("\n=== 问题分析 ===")
    
    benchmark, full_content = analyze_first_benchmark()
    
    print("问题1: 我们告诉LLM的是什么？")
    print("- 我们说这是'当前的最终代码状态'")
    print("- 但实际上这是'当前状态 + 要实现的新方法的位置'")
    print()
    
    print("问题2: LLM理解成了什么？")
    print("- LLM认为整个代码都是'最终状态'")
    print("- 所以它倒推出了修改现有方法的RC")
    print()
    
    print("问题3: 我们应该怎么做？")
    print("- 明确区分'当前状态'和'要实现的新功能'")
    print("- 告诉LLM新功能是什么，RC应该为新功能做准备")
    print("- 不要让LLM认为整个context都是'最终状态'")

if __name__ == "__main__":
    construct_actual_prompt()
    analyze_problem()
