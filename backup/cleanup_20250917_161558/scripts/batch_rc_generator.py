#!/usr/bin/env python3
"""
批量生成Recent Changes并创建增强的benchmark
"""
import json
import os
import time
from datetime import datetime
from rc_generator import RCGenerator

def process_all_benchmarks():
    """处理所有benchmark数据"""
    # API配置
    api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
    api_url = "https://api2.aigcbest.top/v1/chat/completions"
    
    generator = RCGenerator(api_key, api_url)
    
    # 读取原始benchmark
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    enhanced_benchmarks = []
    generation_log = []
    
    print("=== 开始批量生成Recent Changes ===")
    
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            entry = json.loads(line.strip())
            benchmark_id = entry.get('id', f'unknown_{line_num}')
            
            print(f"\n处理第{line_num}条: {benchmark_id}")
            
            # 记录开始时间
            start_time = time.time()
            
            # 生成RC
            rc_context = generator.generate_rc_for_benchmark(entry)
            
            # 记录结束时间
            end_time = time.time()
            duration = end_time - start_time
            
            if rc_context:
                # 成功生成
                enhanced_entry = entry.copy()
                enhanced_entry['rc_context'] = rc_context
                enhanced_benchmarks.append(enhanced_entry)
                
                log_entry = {
                    "benchmark_id": benchmark_id,
                    "status": "success",
                    "hunks_count": len(rc_context.get('hunks', [])),
                    "duration_seconds": round(duration, 2),
                    "timestamp": datetime.now().isoformat(),
                    "notes": rc_context.get('notes', '')
                }
                print(f"  ✓ 成功生成 {len(rc_context.get('hunks', []))} 个hunks")
            else:
                # 生成失败，使用原始数据
                enhanced_benchmarks.append(entry)
                
                log_entry = {
                    "benchmark_id": benchmark_id,
                    "status": "failed",
                    "hunks_count": 0,
                    "duration_seconds": round(duration, 2),
                    "timestamp": datetime.now().isoformat(),
                    "error": "RC generation failed"
                }
                print(f"  ✗ 生成失败")
            
            generation_log.append(log_entry)
            
            # 避免API限制，稍作延迟
            time.sleep(2)
    
    return enhanced_benchmarks, generation_log

def save_enhanced_benchmark(enhanced_benchmarks):
    """保存增强的benchmark"""
    output_file = "benchmark/nl2code_java_F10L_with_rc.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in enhanced_benchmarks:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"\n增强的benchmark已保存到: {output_file}")
    return output_file

def save_generation_log(generation_log):
    """保存生成日志"""
    log_file = "gen_log.json"
    
    log_summary = {
        "generation_time": datetime.now().isoformat(),
        "total_benchmarks": len(generation_log),
        "successful_generations": len([log for log in generation_log if log['status'] == 'success']),
        "failed_generations": len([log for log in generation_log if log['status'] == 'failed']),
        "model": "gpt-4o",
        "api_url": "https://api2.aigcbest.top/v1/chat/completions",
        "details": generation_log
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_summary, f, indent=2, ensure_ascii=False)
    
    print(f"生成日志已保存到: {log_file}")
    return log_file

def generate_rc_preview(enhanced_benchmarks):
    """生成RC预览markdown文件"""
    preview_file = "rc_preview.md"
    
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write("# Recent Changes Preview\n\n")
        f.write(f"Generated at: {datetime.now().isoformat()}\n\n")
        
        for i, entry in enumerate(enhanced_benchmarks, 1):
            benchmark_id = entry.get('id', f'unknown_{i}')
            rc_context = entry.get('rc_context', {})
            
            f.write(f"## {i}. {benchmark_id}\n\n")
            
            # 原始功能描述
            extra = entry.get('extra_content', {})
            if 'query' in extra:
                f.write(f"**原始功能**: {extra['query']}\n\n")
            
            # RC信息
            hunks = rc_context.get('hunks', [])
            notes = rc_context.get('notes', '')
            
            if hunks:
                f.write(f"**Recent Changes**: {len(hunks)} 个微改动\n\n")
                
                for j, hunk in enumerate(hunks, 1):
                    f.write(f"### 改动 {j}\n\n")
                    f.write(f"- **文件**: `{hunk.get('path', 'unknown')}`\n")
                    f.write(f"- **类型**: {hunk.get('type', 'unknown')}\n")
                    f.write(f"- **重叠**: {hunk.get('overlap', False)}\n")
                    f.write(f"- **邻近**: {hunk.get('nearby', False)}\n\n")
                    
                    if 'mini_diff' in hunk:
                        f.write("**Diff**:\n```diff\n")
                        f.write(hunk['mini_diff'])
                        f.write("\n```\n\n")
                
                if notes:
                    f.write(f"**说明**: {notes}\n\n")
            else:
                f.write("**Recent Changes**: 无\n\n")
            
            f.write("---\n\n")
    
    print(f"RC预览已保存到: {preview_file}")
    return preview_file

def main():
    """主函数"""
    print("开始批量生成Recent Changes...")
    
    # 处理所有benchmark
    enhanced_benchmarks, generation_log = process_all_benchmarks()
    
    # 保存结果
    enhanced_file = save_enhanced_benchmark(enhanced_benchmarks)
    log_file = save_generation_log(generation_log)
    preview_file = generate_rc_preview(enhanced_benchmarks)
    
    # 统计信息
    total = len(generation_log)
    success = len([log for log in generation_log if log['status'] == 'success'])
    failed = total - success
    
    print(f"\n=== 生成完成 ===")
    print(f"总计: {total} 条")
    print(f"成功: {success} 条")
    print(f"失败: {failed} 条")
    print(f"成功率: {success/total*100:.1f}%")
    
    print(f"\n生成的文件:")
    print(f"- 增强benchmark: {enhanced_file}")
    print(f"- 生成日志: {log_file}")
    print(f"- RC预览: {preview_file}")

if __name__ == "__main__":
    main()
