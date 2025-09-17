#!/usr/bin/env python3
"""
测试LLM API调用
"""
import requests
import json
import time

def test_api_connection():
    """测试API连接"""
    api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 简单的测试请求
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Hello, please respond with 'API test successful'"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    print("=== API连接测试 ===")
    print(f"URL: {api_url}")
    print(f"Model: {data['model']}")
    print(f"Headers: {headers}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print()
    
    try:
        print("发送请求...")
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API调用成功!")
            print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"LLM回复: {content}")
                return True
        else:
            print("✗ API调用失败!")
            print(f"错误响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ 连接错误: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求异常: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON解析错误: {e}")
        print(f"原始响应: {response.text}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return False

def test_different_models():
    """测试不同的模型名称"""
    api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    models_to_test = [
        "gpt-4o",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "gpt-4o-mini"
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    print("\n=== 测试不同模型 ===")
    
    for model in models_to_test:
        print(f"\n测试模型: {model}")
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "temperature": 0.7,
            "max_tokens": 10
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ {model} 可用")
                if 'choices' in result:
                    content = result['choices'][0]['message']['content']
                    print(f"    回复: {content}")
            else:
                print(f"  ✗ {model} 不可用 - 状态码: {response.status_code}")
                print(f"    错误: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  ✗ {model} 测试失败: {e}")
        
        time.sleep(1)  # 避免请求过快

def test_api_endpoint():
    """测试API端点是否可达"""
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    print("\n=== 测试API端点 ===")
    
    try:
        # 先测试基本连接
        base_url = "https://api2.aigcbest.top"
        response = requests.get(base_url, timeout=10)
        print(f"基础URL {base_url} 状态码: {response.status_code}")
        
        # 测试models端点
        models_url = "https://api2.aigcbest.top/v1/models"
        api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
        headers = {'Authorization': f'Bearer {api_key}'}
        
        response = requests.get(models_url, headers=headers, timeout=10)
        print(f"Models端点状态码: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print("可用模型:")
            if 'data' in models:
                for model in models['data'][:5]:  # 只显示前5个
                    print(f"  - {model.get('id', 'unknown')}")
        else:
            print(f"Models端点错误: {response.text[:200]}...")
            
    except Exception as e:
        print(f"端点测试失败: {e}")

def main():
    """主函数"""
    print("开始API调试...")
    
    # 1. 测试基本连接
    success = test_api_connection()
    
    if not success:
        # 2. 测试端点可达性
        test_api_endpoint()
        
        # 3. 测试不同模型
        test_different_models()
    
    print("\n=== 调试完成 ===")

if __name__ == "__main__":
    main()
