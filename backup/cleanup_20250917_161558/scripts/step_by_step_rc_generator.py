#!/usr/bin/env python3
"""
逐步生成RC，遇到问题及时停止调试
"""
import json
import os
import time
from datetime import datetime
from rc_generator import RCGenerator

def process_single_benchmark(generator, entry, line_num):
    """处理单条benchmark，详细输出调试信息"""
    benchmark_id = entry.get('id', f'unknown_{line_num}')
    
    print(f"\n{'='*60}")
    print(f"处理第{line_num}条: {benchmark_id}")
    print(f"{'='*60}")
    
    # 显示基本信息
    extra = entry.get('extra_content', {})
    print(f"原始功能: {extra.get('query', 'Unknown')}")
    print(f"文件路径: {extra.get('file_path', 'Unknown')}")
    print(f"行号范围: {extra.get('start_line', '?')}-{extra.get('end_line', '?')}")
    print(f"测试结果: {extra.get('test_result', 'Unknown')}")
    
    # 提取代码上下文
    context = generator.extract_code_context(entry.get('prompt', ''))
    print(f"\n代码上下文提取:")
    print(f"  - 上方代码: {'✓' if context.get('above') else '✗'}")
    print(f"  - 下方代码: {'✓' if context.get('below') else '✗'}")
    print(f"  - 目标功能: {context.get('feature', 'Unknown')}")
    print(f"  - 目标代码片段: {'✓' if context.get('target_snippet') else '✗'}")
    
    if not context:
        print("✗ 代码上下文提取失败，跳过此条目")
        return None, "context_extraction_failed"
    
    # 显示要发送给LLM的prompt预览
    system_prompt = generator.build_system_prompt()
    user_prompt = generator.build_user_prompt(
        context,
        extra.get('file_path', 'unknown.java'),
        extra.get('start_line', 1),
        extra.get('end_line', 10)
    )
    
    print(f"\nPrompt信息:")
    print(f"  - System prompt长度: {len(system_prompt)} 字符")
    print(f"  - User prompt长度: {len(user_prompt)} 字符")
    
    # 询问是否继续
    response = input("\n是否继续调用LLM API? (y/n/s=显示prompt): ").strip().lower()
    
    if response == 's':
        print("\n=== System Prompt ===")
        print(system_prompt)
        print("\n=== User Prompt ===")
        print(user_prompt[:1000] + "..." if len(user_prompt) > 1000 else user_prompt)
        response = input("\n现在是否继续调用LLM API? (y/n): ").strip().lower()
    
    if response != 'y':
        print("跳过此条目")
        return None, "user_skipped"
    
    # 调用LLM
    print("\n开始调用LLM...")
    start_time = time.time()
    
    llm_response = generator.call_llm_api(system_prompt, user_prompt)
    
    end_time = time.time()
    duration = end_time - start_time
    
    if not llm_response:
        print("✗ LLM调用失败")
        return None, "llm_call_failed"
    
    print(f"✓ LLM调用成功，耗时: {duration:.2f}秒")
    print(f"响应长度: {len(llm_response)} 字符")
    
    # 显示原始响应
    print(f"\n=== LLM原始响应 ===")
    print(llm_response)
    print(f"=== 响应结束 ===")
    
    # 解析响应
    print(f"\n开始解析响应...")
    parsed = generator.parse_llm_response(llm_response)
    
    # 检查解析结果
    hunks_1 = parsed.get("hunks_1", [])
    hunks_2 = parsed.get("hunks_2", [])
    hunks_3 = parsed.get("hunks_3", [])
    notes = parsed.get("notes", "")
    
    print(f"解析结果:")
    print(f"  - hunks_1: {len(hunks_1)} 个")
    print(f"  - hunks_2: {len(hunks_2)} 个")
    print(f"  - hunks_3: {len(hunks_3)} 个")
    print(f"  - notes: {'✓' if notes else '✗'}")
    
    # 合并所有hunks
    all_hunks = []
    all_hunks.extend(hunks_1)
    all_hunks.extend(hunks_2)
    all_hunks.extend(hunks_3)
    
    if not all_hunks:
        print("✗ 没有解析到任何hunks")
        return None, "no_hunks_parsed"
    
    # 验证hunks格式
    print(f"\n验证hunks格式:")
    for i, hunk in enumerate(all_hunks, 1):
        print(f"  Hunk {i}:")
        required_fields = ['path', 'type', 'overlap', 'nearby', 'mini_diff', 'after']
        for field in required_fields:
            if field in hunk:
                print(f"    ✓ {field}")
            else:
                print(f"    ✗ 缺少字段: {field}")
                return None, f"hunk_{i}_missing_{field}"
    
    rc_context = {
        "hunks": all_hunks,
        "notes": notes
    }
    
    print(f"\n✓ RC生成成功!")
    print(f"  - 总hunks数: {len(all_hunks)}")
    print(f"  - Notes: {notes}")
    
    return rc_context, "success"

def main():
    """主函数"""
    # API配置
    api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    generator = RCGenerator(api_key, api_url)
    
    # 读取benchmark数据
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    
    print("=== 逐步RC生成器 ===")
    print(f"读取文件: {benchmark_file}")
    
    entries = []
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line in f:
            entries.append(json.loads(line.strip()))
    
    print(f"总共 {len(entries)} 条benchmark数据")
    
    # 询问从哪一条开始
    start_from = input(f"\n从第几条开始处理? (1-{len(entries)}, 默认1): ").strip()
    try:
        start_index = int(start_from) - 1 if start_from else 0
        start_index = max(0, min(start_index, len(entries) - 1))
    except ValueError:
        start_index = 0
    
    print(f"从第 {start_index + 1} 条开始处理")
    
    # 逐条处理
    results = []
    
    for i in range(start_index, len(entries)):
        entry = entries[i]
        line_num = i + 1
        
        rc_context, status = process_single_benchmark(generator, entry, line_num)
        
        result = {
            "line_num": line_num,
            "benchmark_id": entry.get('id', f'unknown_{line_num}'),
            "status": status,
            "rc_context": rc_context,
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)
        
        # 保存当前结果
        with open(f"step_results_{line_num}.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        if status != "success":
            print(f"\n处理失败，状态: {status}")
            
            # 询问是否继续
            continue_choice = input("是否继续处理下一条? (y/n/q=退出): ").strip().lower()
            if continue_choice == 'q':
                print("用户选择退出")
                break
            elif continue_choice != 'y':
                print("停止处理")
                break
        else:
            # 成功的情况下也询问是否继续
            if i < len(entries) - 1:
                continue_choice = input("\n是否继续处理下一条? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    print("停止处理")
                    break
        
        # 添加延迟避免API限制
        if status == "success":
            print("等待3秒...")
            time.sleep(3)
    
    # 保存总结果
    summary = {
        "total_processed": len(results),
        "successful": len([r for r in results if r['status'] == 'success']),
        "failed": len([r for r in results if r['status'] != 'success']),
        "results": results
    }
    
    with open("step_by_step_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== 处理完成 ===")
    print(f"总处理: {summary['total_processed']} 条")
    print(f"成功: {summary['successful']} 条")
    print(f"失败: {summary['failed']} 条")
    print(f"详细结果已保存到: step_by_step_summary.json")

if __name__ == "__main__":
    main()
