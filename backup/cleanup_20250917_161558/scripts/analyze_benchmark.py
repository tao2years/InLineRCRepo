#!/usr/bin/env python3
"""
分析benchmark数据结构的脚本
"""
import json
import os
from typing import Dict, List, Any

def analyze_benchmark_structure():
    """分析benchmark文件的结构"""
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    
    if not os.path.exists(benchmark_file):
        print(f"Benchmark文件不存在: {benchmark_file}")
        return
    
    print("=== Benchmark数据结构分析 ===\n")
    
    entries = []
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"第{line_num}行JSON解析错误: {e}")
    
    print(f"总共找到 {len(entries)} 条benchmark数据\n")
    
    # 分析字段结构
    all_fields = set()
    for entry in entries:
        all_fields.update(entry.keys())
    
    print("所有字段:")
    for field in sorted(all_fields):
        print(f"  - {field}")
    print()
    
    # 分析每条数据的详细信息
    for i, entry in enumerate(entries, 1):
        print(f"=== 第{i}条数据 ===")
        print(f"ID: {entry.get('id', 'N/A')}")
        print(f"Domain: {entry.get('domain', 'N/A')}")
        
        # 分析extra_content
        extra = entry.get('extra_content', {})
        if extra:
            print("Extra Content:")
            for key, value in extra.items():
                if key == 'file_path':
                    print(f"  文件路径: {value}")
                elif key == 'start_line' and 'end_line' in extra:
                    print(f"  行号范围: {value}-{extra['end_line']}")
                elif key == 'query':
                    print(f"  查询: {value}")
                elif key == 'test_result':
                    print(f"  测试结果: {value}")
                elif key == 'work_dir':
                    print(f"  工作目录: {value}")
        
        # 分析prompt中的代码上下文
        prompt = entry.get('prompt', '')
        if 'The context above is:' in prompt and 'The context below is:' in prompt:
            print("  包含上下文代码")
        
        print()

def extract_file_paths():
    """提取所有文件路径"""
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    
    file_paths = []
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            extra = entry.get('extra_content', {})
            if 'file_path' in extra:
                file_paths.append(extra['file_path'])
    
    print("=== 提取的文件路径 ===")
    for i, path in enumerate(file_paths, 1):
        print(f"{i}. {path}")
    
    return file_paths

def analyze_code_context():
    """分析代码上下文"""
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    
    print("=== 代码上下文分析 ===\n")
    
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            entry = json.loads(line.strip())
            prompt = entry.get('prompt', '')
            
            print(f"第{line_num}条数据:")
            
            # 提取类名
            if 'public class ' in prompt:
                import re
                class_matches = re.findall(r'public class (\w+)', prompt)
                if class_matches:
                    print(f"  主要类: {class_matches[0]}")
            
            # 提取要实现的功能
            if 'The new feature is ' in prompt:
                feature_start = prompt.find('The new feature is ') + len('The new feature is ')
                feature_end = prompt.find('\n', feature_start)
                if feature_end == -1:
                    feature_end = prompt.find('.', feature_start)
                feature = prompt[feature_start:feature_end].strip()
                print(f"  新功能: {feature}")
            
            # 提取要修改的代码片段
            if 'And here is the code snippet you are asked to modify:' in prompt:
                snippet_start = prompt.find('```java', prompt.find('And here is the code snippet you are asked to modify:'))
                if snippet_start != -1:
                    snippet_end = prompt.find('```', snippet_start + 7)
                    if snippet_end != -1:
                        snippet = prompt[snippet_start+7:snippet_end].strip()
                        print(f"  要修改的代码: {snippet}")
            
            print()

if __name__ == "__main__":
    analyze_benchmark_structure()
    print("\n" + "="*50 + "\n")
    extract_file_paths()
    print("\n" + "="*50 + "\n")
    analyze_code_context()
