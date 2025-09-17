#!/usr/bin/env python3
"""
测试新的prompt逻辑
"""

import json
import requests
from datetime import datetime

def test_new_prompt():
    # 模拟一个benchmark数据
    test_benchmark = {
        "prompt": """A user is developing a new feature. Based on the known code information, help him implement this new feature.

The context above is:
```java
public class SortingAlgorithm {
    
    /**
     * 快速排序算法
     */
    public static void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high);
            quickSort(arr, low, pi - 1);
            quickSort(arr, pi + 1, high);
        }
    }
    
    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = (low - 1);
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
        
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;
        
        return i + 1;
    }
    
    private static void printArray(int[] arr) {
        for (int value : arr) {
            System.out.print(value + " ");
        }
        System.out.println();
    }
    
    public static void main(String[] args) {
        // 基本测试用例
        int[] arr1 = {64, 34, 25, 12, 22, 11, 90};
        System.out.println("原数组:");
        printArray(arr1);
        
        quickSort(arr1, 0, arr1.length - 1);
        System.out.println("排序后:");
        printArray(arr1);
        
        // 边界测试
        int[] arr2 = {5};
        quickSort(arr2, 0, arr2.length - 1);
        System.out.println("单元素数组排序:");
        printArray(arr2);
```

The context below is:
```java
    }
}
```

The new feature is 新增更多测试用例验证排序算法的正确性.

And here is the code snippet you are asked to modify:
```java

// 在main方法中新增测试用例
```""",
        "id": "test_sorting_algorithm",
        "extra_content": {
            "file_path": "/test/SortingAlgorithm.java"
        }
    }
    
    # 加载新的prompt模板
    with open('RC_prompt_v3.txt', 'r', encoding='utf-8') as f:
        prompt_content = f.read()
    
    # 解析prompt
    parts = prompt_content.split('(2) User Prompt')
    system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
    user_template = parts[1].strip()
    
    # 提取代码内容
    import re
    context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', test_benchmark['prompt'], re.DOTALL)
    context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', test_benchmark['prompt'], re.DOTALL)
    task_match = re.search(r'The new feature is (.+?)\.', test_benchmark['prompt'])
    
    full_content = f"{context_above_match.group(1).strip()}\n{context_below_match.group(1).strip()}"
    task = task_match.group(1).strip()
    
    # 创建用户prompt
    user_prompt = user_template.format(
        instruction=task,
        full_file_content=full_content
    )
    
    print("=== System Prompt ===")
    print(system_prompt)
    print("\n=== User Prompt ===")
    print(user_prompt)
    
    # 调用LLM
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
        'max_tokens': 2000
    }
    
    try:
        print("\n🚀 调用LLM...")
        response = requests.post(api_url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        llm_response = result['choices'][0]['message']['content']
        
        print("\n=== LLM Response ===")
        print(llm_response)
        
        # 保存测试结果
        test_result = {
            'timestamp': datetime.now().isoformat(),
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'llm_response': llm_response
        }
        
        with open('test_new_prompt_result.json', 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 测试结果已保存到: test_new_prompt_result.json")
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")

if __name__ == "__main__":
    test_new_prompt()
