#!/usr/bin/env python3
"""
测试最终正确的理解
"""

import json
import re
import requests
from datetime import datetime

def test_final_understanding():
    print("=== 测试最终正确的理解 ===")
    
    # 加载第一条benchmark
    with open('benchmark/nl2code_java_F10L.jsonl', 'r', encoding='utf-8') as f:
        first_line = f.readline()
        benchmark = json.loads(first_line)
    
    # 提取信息
    context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', benchmark['prompt'], re.DOTALL)
    context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', benchmark['prompt'], re.DOTALL)
    task_match = re.search(r'The new feature is (.+?)\.', benchmark['prompt'])
    
    context_above = context_above_match.group(1).strip()
    context_below = context_below_match.group(1).strip()
    task = task_match.group(1).strip()
    new_method_impl = benchmark['good_example_response'].replace('```java\n', '').replace('\n```', '').strip()
    
    print("=== 正确理解 ===")
    print("Context Above + Context Below = 最终代码状态（但缺少新方法）")
    print("good_example_response = 要插入的新方法")
    print("最终完整状态 = Context + 新方法插入到合适位置")
    print()
    
    # 构造最终完整代码（在类的最后插入新方法）
    # 找到类的结束位置，在最后一个}之前插入新方法
    final_complete_code = f"{context_above}\n{context_below}"
    
    # 在最后的}之前插入新方法
    final_complete_code = final_complete_code.replace(
        '    }\n}',
        f'    }}\n\n{new_method_impl}\n}}'
    )
    
    print("任务描述:", task)
    print("最终完整代码长度:", len(final_complete_code))
    print()
    print("最终完整代码预览:")
    print("=" * 50)
    # 只显示最后几行来确认新方法被正确插入
    lines = final_complete_code.split('\n')
    print('\n'.join(lines[-15:]))
    print("=" * 50)
    
    # 加载新的prompt模板
    with open('RC_prompt_v5_final.txt', 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    parts = prompt_content.split('(2) User Prompt')
    system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
    user_template = parts[1].strip()
    
    # 构造用户prompt
    user_prompt = user_template.format(
        task_description=task,
        final_complete_code=final_complete_code
    )
    
    # 保存prompt到文件
    with open('test_final_understanding_prompt.txt', 'w', encoding='utf-8') as f:
        f.write("=== SYSTEM PROMPT ===\n")
        f.write(system_prompt)
        f.write("\n\n=== USER PROMPT ===\n")
        f.write(user_prompt)
    
    print("✅ Prompt内容已保存到: test_final_understanding_prompt.txt")
    
    # 调用LLM测试
    api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': "gpt-4o-2024-08-06",
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 2500
    }
    
    try:
        print("\n🚀 调用LLM测试最终正确理解...")
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        llm_response = result['choices'][0]['message']['content']
        
        print("\n=== LLM Response ===")
        print(llm_response)
        
        # 保存测试结果
        test_result = {
            'timestamp': datetime.now().isoformat(),
            'prompt_version': 'v5_final_correct',
            'task': task,
            'final_code_length': len(final_complete_code),
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'llm_response': llm_response
        }
        
        with open('test_final_understanding_result.json', 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 测试结果已保存到: test_final_understanding_result.json")
        
        # 分析结果质量
        if 'loadClassWithApplicationLoader' in llm_response:
            print("✅ LLM响应中提到了目标方法")
        
        if 'hunks_1' in llm_response and 'hunks_2' in llm_response and 'hunks_3' in llm_response:
            print("✅ LLM返回了完整的3个hunks")
        
        if '```json' in llm_response:
            print("✅ LLM使用了正确的JSON格式")
            
    except Exception as e:
        print(f"❌ 调用失败: {e}")

if __name__ == "__main__":
    test_final_understanding()
