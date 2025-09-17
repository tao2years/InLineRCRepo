#!/usr/bin/env python3
"""
测试正确的prompt逻辑
"""

import json
import re
import requests
from datetime import datetime

def test_correct_prompt():
    print("=== 测试正确的prompt逻辑 ===")
    
    # 加载第一条benchmark
    with open('benchmark/nl2code_java_F10L.jsonl', 'r', encoding='utf-8') as f:
        first_line = f.readline()
        benchmark = json.loads(first_line)
    
    # 提取信息
    context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', benchmark['prompt'], re.DOTALL)
    context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', benchmark['prompt'], re.DOTALL)
    task_match = re.search(r'The new feature is (.+?)\.', benchmark['prompt'])
    method_match = re.search(r'```java\s*(.*?)\s*```', benchmark['prompt'].split('And here is the code snippet you are asked to modify:')[1])
    
    current_code = f"{context_above_match.group(1).strip()}\n{context_below_match.group(1).strip()}"
    task = task_match.group(1).strip()
    new_method_signature = method_match.group(1).strip()
    new_method_implementation = benchmark['good_example_response'].replace('```java\n', '').replace('\n```', '').strip()
    
    # 构造最终代码状态（插入新方法到合适位置）
    # 在loadAndInvoke方法之后插入新方法
    final_code = current_code.replace(
        '    }\n}',
        f'    }}\n\n{new_method_implementation}\n}}'
    )
    
    # 加载新的prompt模板
    with open('RC_prompt_v4_correct.txt', 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    parts = prompt_content.split('(2) User Prompt')
    system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
    user_template = parts[1].strip()
    
    # 构造用户prompt
    user_prompt = user_template.format(
        instruction=task,
        current_code=current_code,
        new_method_signature=new_method_signature,
        new_method_implementation=new_method_implementation,
        final_code_with_new_method=final_code
    )
    
    print("=== 构造的prompt内容 ===")
    print("任务:", task)
    print("新方法签名:", new_method_signature)
    print("当前代码长度:", len(current_code))
    print("最终代码长度:", len(final_code))
    print()
    
    # 保存prompt到文件
    with open('test_correct_prompt_content.txt', 'w', encoding='utf-8') as f:
        f.write("=== SYSTEM PROMPT ===\n")
        f.write(system_prompt)
        f.write("\n\n=== USER PROMPT ===\n")
        f.write(user_prompt)
    
    print("✅ Prompt内容已保存到: test_correct_prompt_content.txt")
    
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
        print("\n🚀 调用LLM测试新prompt...")
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        llm_response = result['choices'][0]['message']['content']
        
        print("\n=== LLM Response ===")
        print(llm_response)
        
        # 保存测试结果
        test_result = {
            'timestamp': datetime.now().isoformat(),
            'prompt_version': 'v4_correct',
            'task': task,
            'new_method_signature': new_method_signature,
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'llm_response': llm_response
        }
        
        with open('test_correct_prompt_result.json', 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 测试结果已保存到: test_correct_prompt_result.json")
        
        # 简单分析结果
        if 'loadClassWithApplicationLoader' in llm_response or 'Application' in llm_response:
            print("✅ LLM响应中提到了新功能相关内容")
        else:
            print("❌ LLM响应中没有提到新功能相关内容")
            
    except Exception as e:
        print(f"❌ 调用失败: {e}")

if __name__ == "__main__":
    test_correct_prompt()
