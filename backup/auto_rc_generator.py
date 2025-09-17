#!/usr/bin/env python3
"""
全自动RC生成器，自动处理所有问题并生成最终benchmark
"""
import json
import os
import time
import re
from datetime import datetime
from rc_generator import RCGenerator

class AutoRCGenerator:
    def __init__(self):
        self.api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
        self.api_url = "https://api2.aigcbest.top/v1/chat/completions"
        self.generator = RCGenerator(self.api_key, self.api_url)
        self.results = []
        self.enhanced_benchmarks = []
        
    def fix_json_response(self, response: str) -> str:
        """修复LLM响应中的JSON格式问题"""
        # 修复常见的JSON格式问题
        fixed = response
        
        # 修复布尔值
        fixed = re.sub(r'\btrue\b', 'true', fixed)
        fixed = re.sub(r'\bfalse\b', 'false', fixed)
        
        # 修复字符串中的换行符
        fixed = re.sub(r'\\n', '\\\\n', fixed)
        
        # 修复未转义的引号
        fixed = re.sub(r'(?<!\\)"(?=\w)', '\\"', fixed)
        
        return fixed
    
    def enhanced_parse_response(self, response: str) -> dict:
        """增强的响应解析，带自动修复功能"""
        result = {
            "hunks_1": [],
            "hunks_2": [],
            "hunks_3": [],
            "notes": ""
        }

        # 解析各个部分
        sections = ['hunks_1', 'hunks_2', 'hunks_3']

        for section in sections:
            # 匹配 ### section_name 后面的内容
            pattern = rf'### {section}[^\n]*\n(.*?)(?=### |$)'
            match = re.search(pattern, response, re.DOTALL)

            if match:
                content = match.group(1).strip()

                # 提取JSON代码块
                json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if not json_blocks:
                    # 如果没有```json代码块，尝试直接提取JSON数组
                    json_blocks = re.findall(r'\[(.*?)\]', content, re.DOTALL)
                    if json_blocks:
                        json_blocks = ['[' + block + ']' for block in json_blocks]

                # 解析JSON
                for json_str in json_blocks:
                    try:
                        # 简单清理
                        cleaned_json = json_str.strip()
                        parsed = json.loads(cleaned_json)

                        if isinstance(parsed, list):
                            result[section].extend(parsed)
                        elif isinstance(parsed, dict):
                            result[section].append(parsed)

                        break  # 成功解析后跳出循环

                    except json.JSONDecodeError as e:
                        print(f"    JSON解析错误 ({section}): {e}")
                        # 尝试手动提取
                        try:
                            manual_hunk = self.extract_hunk_manually(json_str)
                            if manual_hunk:
                                result[section].append(manual_hunk)
                                break
                        except Exception as manual_e:
                            print(f"    手动提取也失败: {manual_e}")
                            continue

                # 如果JSON解析失败，尝试手动提取
                if not result[section]:
                    manual_hunks = self.manual_extract_hunks_from_section(content)
                    result[section] = manual_hunks

        # 解析notes
        notes_match = re.search(r'### notes\s*(.*?)$', response, re.DOTALL | re.IGNORECASE)
        if notes_match:
            result["notes"] = notes_match.group(1).strip()

        return result

    def manual_extract_hunks_from_section(self, content: str) -> list:
        """从section内容中手动提取hunks"""
        hunks = []

        # 尝试提取包含path字段的JSON对象
        json_objects = re.findall(r'\{[^{}]*"path"[^{}]*\}', content, re.DOTALL)

        for obj_str in json_objects:
            try:
                # 清理和修复JSON
                cleaned = obj_str.strip()
                cleaned = re.sub(r'\n\s*', ' ', cleaned)
                cleaned = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"', r'"\1"', cleaned)

                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and 'path' in parsed:
                    hunks.append(parsed)
            except:
                continue

        return hunks

    def extract_hunk_manually(self, json_str: str) -> dict:
        """手动提取单个hunk的基本信息"""
        hunk = {}

        # 提取path
        path_match = re.search(r'"path"\s*:\s*"([^"]*)"', json_str)
        if path_match:
            hunk['path'] = path_match.group(1)

        # 提取type
        type_match = re.search(r'"type"\s*:\s*"([^"]*)"', json_str)
        if type_match:
            hunk['type'] = type_match.group(1)
        else:
            hunk['type'] = 'same_file'

        # 提取overlap
        overlap_match = re.search(r'"overlap"\s*:\s*(true|false|\[[^\]]*\])', json_str)
        if overlap_match:
            overlap_val = overlap_match.group(1)
            if overlap_val in ['true', 'false']:
                hunk['overlap'] = overlap_val == 'true'
            else:
                hunk['overlap'] = False
        else:
            hunk['overlap'] = False

        # 提取nearby
        nearby_match = re.search(r'"nearby"\s*:\s*(true|false|\[[^\]]*\])', json_str)
        if nearby_match:
            nearby_val = nearby_match.group(1)
            if nearby_val in ['true', 'false']:
                hunk['nearby'] = nearby_val == 'true'
            else:
                hunk['nearby'] = True
        else:
            hunk['nearby'] = True

        # 提取mini_diff
        mini_diff_match = re.search(r'"mini_diff"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str, re.DOTALL)
        if mini_diff_match:
            hunk['mini_diff'] = mini_diff_match.group(1).replace('\\"', '"').replace('\\n', '\n')
        else:
            hunk['mini_diff'] = "// Auto-extracted change"

        # 提取after数组
        after_match = re.search(r'"after"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if after_match:
            after_content = after_match.group(1)
            # 提取字符串数组
            after_items = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', after_content)
            hunk['after'] = [item.replace('\\"', '"').replace('\\n', '\n') for item in after_items]
        else:
            hunk['after'] = ["// Auto-extracted after content"]

        # 只有包含path的才是有效hunk
        return hunk if 'path' in hunk else None

    def manual_extract_hunks(self, response: str) -> dict:
        """手动提取hunks，用于标准解析失败的情况"""
        result = {
            "hunks_1": [],
            "hunks_2": [],
            "hunks_3": [],
            "notes": ""
        }

        # 尝试提取JSON块
        json_blocks = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)

        for block in json_blocks:
            try:
                parsed_block = json.loads(block)
                if isinstance(parsed_block, dict) and 'path' in parsed_block:
                    # 这是一个hunk
                    result["hunks_1"].append(parsed_block)
            except:
                continue

        # 提取notes
        notes_patterns = [
            r'notes["\']?\s*:\s*["\']([^"\']*)["\']',
            r'说明[：:]\s*([^\n]*)',
            r'这些改动([^\n]*)',
        ]

        for pattern in notes_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                result["notes"] = match.group(1).strip()
                break

        return result

    def validate_hunk(self, hunk: dict) -> bool:
        """验证hunk格式"""
        required_fields = ['path', 'type', 'overlap', 'nearby', 'mini_diff', 'after']
        
        for field in required_fields:
            if field not in hunk:
                return False
        
        # 验证字段类型
        if not isinstance(hunk['overlap'], bool):
            hunk['overlap'] = str(hunk['overlap']).lower() == 'true'
        
        if not isinstance(hunk['nearby'], bool):
            hunk['nearby'] = str(hunk['nearby']).lower() == 'true'
        
        if not isinstance(hunk['after'], list):
            if isinstance(hunk['after'], str):
                hunk['after'] = hunk['after'].split('\n')
            else:
                hunk['after'] = []
        
        return True
    
    def process_benchmark(self, entry: dict, line_num: int) -> dict:
        """处理单条benchmark"""
        benchmark_id = entry.get('id', f'unknown_{line_num}')

        print(f"\n处理第{line_num}条: {benchmark_id}")

        # 检查是否已有缓存的响应
        cache_file = f"llm_cache_{line_num}_{benchmark_id.replace('#', '_').replace('/', '_')}.json"

        if os.path.exists(cache_file):
            print(f"  发现缓存文件: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                llm_response = cached_data.get('llm_response', '')
                if llm_response:
                    print(f"  使用缓存的LLM响应 (长度: {len(llm_response)} 字符)")
                    return self.parse_cached_response(llm_response, line_num, benchmark_id)

        # 提取代码上下文
        context = self.generator.extract_code_context(entry.get('prompt', ''))
        if not context:
            print(f"  ✗ 代码上下文提取失败")
            return {"status": "context_failed", "rc_context": None}

        # 构建prompt
        extra = entry.get('extra_content', {})
        system_prompt = self.generator.build_system_prompt()
        user_prompt = self.generator.build_user_prompt(
            context,
            extra.get('file_path', 'unknown.java'),
            extra.get('start_line', 1),
            extra.get('end_line', 10)
        )

        # 调用LLM
        print(f"  调用LLM API...")
        llm_response = self.generator.call_llm_api(system_prompt, user_prompt)

        if not llm_response:
            print(f"  ✗ LLM调用失败")
            default_rc = self.generate_default_rc(context, extra.get('file_path', 'unknown.java'))
            return {"status": "llm_failed", "rc_context": default_rc}

        # 缓存LLM响应
        cache_data = {
            "benchmark_id": benchmark_id,
            "line_num": line_num,
            "timestamp": datetime.now().isoformat(),
            "llm_response": llm_response,
            "response_length": len(llm_response)
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        print(f"  ✓ LLM响应已缓存到: {cache_file}")
        print(f"  响应长度: {len(llm_response)} 字符")

        return self.parse_cached_response(llm_response, line_num, benchmark_id)

    def parse_cached_response(self, llm_response: str, line_num: int, benchmark_id: str) -> dict:
        """解析缓存的LLM响应"""
        print(f"\n=== LLM原始响应 (第{line_num}条) ===")
        print(llm_response)
        print(f"=== 响应结束 ===\n")

        # 尝试多种解析方法
        for attempt in range(3):
            try:
                if attempt == 0:
                    print(f"  解析尝试 {attempt + 1}: 标准解析")
                    parsed = self.enhanced_parse_response(llm_response)
                elif attempt == 1:
                    print(f"  解析尝试 {attempt + 1}: 清理后解析")
                    cleaned_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', llm_response)
                    parsed = self.enhanced_parse_response(cleaned_response)
                else:
                    print(f"  解析尝试 {attempt + 1}: 手动提取")
                    parsed = self.manual_extract_hunks(llm_response)

                # 合并所有hunks
                all_hunks = []
                all_hunks.extend(parsed.get("hunks_1", []))
                all_hunks.extend(parsed.get("hunks_2", []))
                all_hunks.extend(parsed.get("hunks_3", []))

                print(f"    提取到 hunks_1: {len(parsed.get('hunks_1', []))} 个")
                print(f"    提取到 hunks_2: {len(parsed.get('hunks_2', []))} 个")
                print(f"    提取到 hunks_3: {len(parsed.get('hunks_3', []))} 个")
                print(f"    提取到 notes: {'✓' if parsed.get('notes') else '✗'}")

                # 验证和修复hunks
                valid_hunks = []
                for i, hunk in enumerate(all_hunks):
                    if self.validate_hunk(hunk):
                        valid_hunks.append(hunk)
                        print(f"    ✓ hunk {i+1} 验证通过")
                    else:
                        print(f"    ✗ hunk {i+1} 验证失败，已跳过")

                if valid_hunks:
                    rc_context = {
                        "hunks": valid_hunks,
                        "notes": parsed.get("notes", "")
                    }

                    print(f"  ✓ 解析成功! 有效hunks: {len(valid_hunks)} 个")
                    return {"status": "success", "rc_context": rc_context}
                else:
                    print(f"    没有有效的hunks，继续尝试...")

            except Exception as e:
                print(f"    解析失败: {e}")
                continue

        # 所有解析尝试都失败，生成默认RC
        print(f"  ✗ 所有解析尝试都失败，使用默认RC")
        default_rc = self.generate_default_rc({}, "unknown.java")
        return {"status": "parse_failed", "rc_context": default_rc}
    
    def generate_default_rc(self, context: dict, file_path: str) -> dict:
        """生成默认的RC上下文"""
        return {
            "hunks": [
                {
                    "path": file_path,
                    "type": "same_file",
                    "overlap": False,
                    "nearby": True,
                    "mini_diff": "@@ -1,3 +1,4 @@\n // Auto-generated default change\n+// TODO: Implement feature enhancement\n class Example {",
                    "after": [
                        "// Auto-generated default change",
                        "// TODO: Implement feature enhancement", 
                        "class Example {"
                    ]
                }
            ],
            "notes": "Auto-generated default recent changes for code preparation"
        }
    
    def save_progress(self, line_num: int):
        """保存当前进度"""
        progress_file = f"progress_checkpoint_{line_num}.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "processed_count": len(self.results),
                "enhanced_benchmarks": self.enhanced_benchmarks,
                "results": self.results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
    
    def run(self):
        """运行自动生成流程"""
        print("=== 全自动RC生成器启动 ===")
        
        # 读取benchmark数据
        benchmark_file = "benchmark/nl2code_java_F10L.jsonl"
        entries = []
        
        with open(benchmark_file, 'r', encoding='utf-8') as f:
            for line in f:
                entries.append(json.loads(line.strip()))
        
        print(f"读取到 {len(entries)} 条benchmark数据")
        
        # 逐条处理
        for i, entry in enumerate(entries, 1):
            result = self.process_benchmark(entry, i)
            
            # 创建增强的benchmark条目
            enhanced_entry = entry.copy()
            if result["rc_context"]:
                enhanced_entry["rc_context"] = result["rc_context"]
            
            self.enhanced_benchmarks.append(enhanced_entry)
            
            # 记录结果
            self.results.append({
                "line_num": i,
                "benchmark_id": entry.get('id', f'unknown_{i}'),
                "status": result["status"],
                "hunks_count": len(result["rc_context"]["hunks"]) if result["rc_context"] else 0,
                "timestamp": datetime.now().isoformat()
            })
            
            # 每处理一条就保存进度
            self.save_progress(i)
            
            # 添加延迟
            time.sleep(2)
        
        # 生成最终文件
        self.generate_final_files()
    
    def generate_final_files(self):
        """生成最终的文件"""
        print(f"\n=== 生成最终文件 ===")
        
        # 1. 保存增强的benchmark
        output_file = "benchmark/nl2code_java_F10L_with_rc.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in self.enhanced_benchmarks:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✓ 增强benchmark已保存: {output_file}")
        
        # 2. 生成统计报告
        successful = len([r for r in self.results if r['status'] == 'success'])
        default_used = len([r for r in self.results if r['status'] == 'default'])
        failed = len([r for r in self.results if r['status'] not in ['success', 'default']])
        
        report = {
            "generation_time": datetime.now().isoformat(),
            "total_benchmarks": len(self.results),
            "successful_generations": successful,
            "default_generations": default_used,
            "failed_generations": failed,
            "success_rate": f"{successful/len(self.results)*100:.1f}%",
            "model": "gpt-4o",
            "details": self.results
        }
        
        with open("gen_log.json", 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 生成日志已保存: gen_log.json")
        
        # 3. 生成预览文件
        self.generate_preview()
        
        print(f"\n=== 完成统计 ===")
        print(f"总计: {len(self.results)} 条")
        print(f"成功: {successful} 条")
        print(f"默认: {default_used} 条") 
        print(f"失败: {failed} 条")
        print(f"成功率: {successful/len(self.results)*100:.1f}%")
    
    def generate_preview(self):
        """生成预览文件"""
        preview_file = "rc_preview.md"
        
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write("# Recent Changes Preview\n\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n\n")
            
            for i, entry in enumerate(self.enhanced_benchmarks, 1):
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
                
                if notes:
                    f.write(f"**说明**: {notes}\n\n")
                
                f.write("---\n\n")
        
        print(f"✓ RC预览已保存: {preview_file}")

def main():
    generator = AutoRCGenerator()
    generator.run()

if __name__ == "__main__":
    main()
