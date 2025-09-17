#!/usr/bin/env python3
"""
最终RC生成器 - 使用缓存的响应重新生成benchmark
"""
import json
import os
from datetime import datetime
from auto_rc_generator import AutoRCGenerator

def regenerate_from_cache():
    """使用缓存的LLM响应重新生成增强的benchmark"""
    generator = AutoRCGenerator()
    
    # 读取原始benchmark
    benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
    entries = []
    
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        for line in f:
            entries.append(json.loads(line.strip()))
    
    print(f"=== 最终RC生成器 ===")
    print(f"读取到 {len(entries)} 条benchmark数据")
    
    enhanced_benchmarks = []
    results = []
    
    for i, entry in enumerate(entries, 1):
        benchmark_id = entry.get('id', f'unknown_{i}')
        
        print(f"\n处理第{i}条: {benchmark_id}")
        
        # 检查缓存文件
        cache_file = f"llm_cache_{i}_{benchmark_id.replace('#', '_').replace('/', '_')}.json"
        
        if os.path.exists(cache_file):
            print(f"  使用缓存: {cache_file}")
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                llm_response = cached_data.get('llm_response', '')
            
            # 解析缓存的响应
            result = generator.parse_cached_response(llm_response, i, benchmark_id)
            
            # 创建增强的benchmark条目
            enhanced_entry = entry.copy()
            if result["rc_context"]:
                enhanced_entry["rc_context"] = result["rc_context"]
            
            enhanced_benchmarks.append(enhanced_entry)
            
            # 记录结果
            results.append({
                "line_num": i,
                "benchmark_id": benchmark_id,
                "status": result["status"],
                "hunks_count": len(result["rc_context"]["hunks"]) if result["rc_context"] else 0,
                "timestamp": datetime.now().isoformat()
            })
            
            if result["status"] == "success":
                hunks_count = len(result["rc_context"]["hunks"])
                print(f"  ✓ 成功生成 {hunks_count} 个hunks")
            else:
                print(f"  ✗ 解析失败，状态: {result['status']}")
        else:
            print(f"  ✗ 缓存文件不存在: {cache_file}")
            
            # 使用原始条目
            enhanced_benchmarks.append(entry)
            results.append({
                "line_num": i,
                "benchmark_id": benchmark_id,
                "status": "no_cache",
                "hunks_count": 0,
                "timestamp": datetime.now().isoformat()
            })
    
    # 生成最终文件
    generate_final_files(enhanced_benchmarks, results)

def generate_final_files(enhanced_benchmarks, results):
    """生成最终的文件"""
    print(f"\n=== 生成最终文件 ===")
    
    # 1. 保存增强的benchmark
    output_file = "benchmark/nl2code_java_F10L_with_rc.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in enhanced_benchmarks:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✓ 增强benchmark已保存: {output_file}")
    
    # 2. 生成统计报告
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] not in ['success']])
    
    report = {
        "generation_time": datetime.now().isoformat(),
        "total_benchmarks": len(results),
        "successful_generations": successful,
        "failed_generations": failed,
        "success_rate": f"{successful/len(results)*100:.1f}%",
        "model": "gpt-4o",
        "details": results
    }
    
    with open("gen_log.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 生成日志已保存: gen_log.json")
    
    # 3. 生成预览文件
    generate_preview(enhanced_benchmarks)
    
    print(f"\n=== 完成统计 ===")
    print(f"总计: {len(results)} 条")
    print(f"成功: {successful} 条")
    print(f"失败: {failed} 条")
    print(f"成功率: {successful/len(results)*100:.1f}%")

def generate_preview(enhanced_benchmarks):
    """生成预览文件"""
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
            
            f.write(f"**Recent Changes**: {len(hunks)} 个微改动\n\n")
            
            if hunks:
                for j, hunk in enumerate(hunks, 1):
                    f.write(f"### 改动 {j}\n\n")
                    f.write(f"- **文件**: `{hunk.get('path', 'unknown')}`\n")
                    f.write(f"- **类型**: {hunk.get('type', 'unknown')}\n")
                    f.write(f"- **重叠**: {hunk.get('overlap', False)}\n")
                    f.write(f"- **邻近**: {hunk.get('nearby', False)}\n\n")
                    
                    if 'mini_diff' in hunk:
                        f.write("**Diff**:\n```diff\n")
                        f.write(hunk['mini_diff'][:500])  # 限制长度
                        if len(hunk['mini_diff']) > 500:
                            f.write("\n... (truncated)")
                        f.write("\n```\n\n")
            
            if notes:
                f.write(f"**说明**: {notes}\n\n")
            
            f.write("---\n\n")
    
    print(f"✓ RC预览已保存: {preview_file}")

def main():
    regenerate_from_cache()

if __name__ == "__main__":
    main()
