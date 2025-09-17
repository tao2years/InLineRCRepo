#!/usr/bin/env python3
"""
测试解析器修复
"""
import json
from auto_rc_generator import AutoRCGenerator

def test_cached_responses():
    """测试已缓存的LLM响应"""
    generator = AutoRCGenerator()
    
    # 测试第5条（之前成功解析了1个hunk）
    cache_file = "llm_cache_5_devspore-cic_30036124_22.json"
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            llm_response = cached_data.get('llm_response', '')
        
        print("=== 测试第5条缓存响应 ===")
        print(f"响应长度: {len(llm_response)} 字符")
        
        # 使用修复后的解析器
        result = generator.parse_cached_response(llm_response, 5, "devspore-cic_30036124_22")
        
        print(f"解析结果: {result['status']}")
        if result['rc_context']:
            hunks = result['rc_context']['hunks']
            print(f"成功解析 {len(hunks)} 个hunks")
            
            for i, hunk in enumerate(hunks, 1):
                print(f"\nHunk {i}:")
                print(f"  Path: {hunk.get('path', 'N/A')}")
                print(f"  Type: {hunk.get('type', 'N/A')}")
                print(f"  Overlap: {hunk.get('overlap', 'N/A')}")
                print(f"  Nearby: {hunk.get('nearby', 'N/A')}")
                print(f"  Mini_diff: {hunk.get('mini_diff', 'N/A')[:100]}...")
                print(f"  After lines: {len(hunk.get('after', []))}")
        
    except Exception as e:
        print(f"测试失败: {e}")

def test_all_cached_responses():
    """测试所有缓存的响应"""
    generator = AutoRCGenerator()
    
    import os
    cache_files = [f for f in os.listdir('.') if f.startswith('llm_cache_')]
    cache_files.sort()
    
    print(f"=== 测试所有 {len(cache_files)} 个缓存文件 ===")
    
    success_count = 0
    
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                llm_response = cached_data.get('llm_response', '')
                line_num = cached_data.get('line_num', 0)
                benchmark_id = cached_data.get('benchmark_id', 'unknown')
            
            print(f"\n测试 {cache_file}:")
            print(f"  Line {line_num}: {benchmark_id}")
            
            # 直接测试解析器
            parsed = generator.enhanced_parse_response(llm_response)
            
            all_hunks = []
            all_hunks.extend(parsed.get("hunks_1", []))
            all_hunks.extend(parsed.get("hunks_2", []))
            all_hunks.extend(parsed.get("hunks_3", []))
            
            valid_hunks = []
            for hunk in all_hunks:
                if generator.validate_hunk(hunk):
                    valid_hunks.append(hunk)
            
            if valid_hunks:
                print(f"  ✓ 成功解析 {len(valid_hunks)} 个有效hunks")
                success_count += 1
            else:
                print(f"  ✗ 没有有效hunks")
                print(f"    hunks_1: {len(parsed.get('hunks_1', []))}")
                print(f"    hunks_2: {len(parsed.get('hunks_2', []))}")
                print(f"    hunks_3: {len(parsed.get('hunks_3', []))}")
                
                # 显示原始响应的一部分来调试
                print(f"    响应预览: {llm_response[:200]}...")
        
        except Exception as e:
            print(f"  ✗ 解析失败: {e}")
    
    print(f"\n=== 测试完成 ===")
    print(f"成功: {success_count}/{len(cache_files)}")
    print(f"成功率: {success_count/len(cache_files)*100:.1f}%")

def main():
    print("开始测试解析器修复...")
    
    # 先测试单个文件
    test_cached_responses()
    
    print("\n" + "="*60)
    
    # 测试所有文件
    test_all_cached_responses()

if __name__ == "__main__":
    main()
