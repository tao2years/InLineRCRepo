#!/usr/bin/env python3
"""
改进的RC生成器 - 使用正确的逻辑递进关系
"""

import json
import re
import os
from datetime import datetime
import requests
from typing import Dict, List, Any, Optional

class ImprovedRCGenerator:
    def __init__(self):
        self.api_key = "sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8"
        
        self.api_url = "https://api2.aigcbest.top/v1/chat/completions"
        self.model = "gpt-4o-2024-08-06"
        
        # 加载改进的prompt
        with open('RC_prompt_improved.txt', 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # 解析prompt
        parts = prompt_content.split('(2) User Prompt - 同文件轮')
        self.system_prompt = parts[0].replace('(1) System Prompt\n', '').strip()
        self.user_template = parts[1].split('(3) User Prompt - 邻居轮')[0].strip()
        
    def load_benchmark(self, file_path: str) -> List[Dict]:
        """加载benchmark数据"""
        benchmarks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    benchmarks.append(json.loads(line))
        return benchmarks
    
    def extract_code_context(self, prompt: str) -> Dict[str, str]:
        """从prompt中提取代码上下文"""
        context_above_match = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        context_below_match = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt, re.DOTALL)
        task_match = re.search(r'The new feature is (.+?)\.', prompt)
        
        return {
            'context_above': context_above_match.group(1).strip() if context_above_match else '',
            'context_below': context_below_match.group(1).strip() if context_below_match else '',
            'task': task_match.group(1).strip() if task_match else ''
        }
    
    def create_user_prompt(self, benchmark: Dict) -> str:
        """创建用户prompt"""
        context = self.extract_code_context(benchmark['prompt'])
        
        # 构建完整的文件内容
        full_content = f"{context['context_above']}\n\n// [CURRENT TASK LOCATION]\n\n{context['context_below']}"
        
        # 替换模板变量
        user_prompt = self.user_template.format(
            instruction=context['task'],
            repo_path="/mock/repo",
            resolved_file_path=benchmark['extra_content']['file_path'],
            start=benchmark['extra_content']['start_line'],
            end=benchmark['extra_content']['end_line'],
            full_file_content=full_content
        )
        
        return user_prompt
    
    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"API调用失败: {e}")
            raise
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        result = {'hunks': []}
        
        # 提取hunks_1, hunks_2, hunks_3
        for i in range(1, 4):
            pattern = f'### hunks_{i}.*?\n(.*?)(?=### hunks_|### notes|$)'
            match = re.search(pattern, response, re.DOTALL)
            if match:
                json_content = match.group(1).strip()
                # 清理JSON内容
                json_content = re.sub(r'```json\s*', '', json_content)
                json_content = re.sub(r'\s*```', '', json_content)
                
                try:
                    hunks = json.loads(json_content)
                    if isinstance(hunks, list):
                        result['hunks'].extend(hunks)
                    else:
                        result['hunks'].append(hunks)
                except json.JSONDecodeError as e:
                    print(f"解析hunks_{i}失败: {e}")
                    print(f"内容: {json_content}")
        
        # 提取notes
        notes_match = re.search(r'### notes\s*(.*?)$', response, re.DOTALL)
        if notes_match:
            result['notes'] = notes_match.group(1).strip()
        else:
            result['notes'] = "递进式准备工作，为实现当前任务铺平道路。"
        
        return result
    
    def generate_rc_for_benchmark(self, benchmark: Dict, index: int) -> Optional[Dict]:
        """为单个benchmark生成RC"""
        print(f"\n处理第{index}条benchmark: {benchmark['id']}")
        
        try:
            # 创建用户prompt
            user_prompt = self.create_user_prompt(benchmark)
            
            # 调用LLM
            print("调用LLM...")
            response = self.call_llm(self.system_prompt, user_prompt)
            
            # 保存响应缓存
            cache_file = f"cache/improved_llm_cache_{index}_{benchmark['id'].replace('#', '_')}.json"
            os.makedirs('cache', exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({'response': response, 'timestamp': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            
            print(f"LLM响应已缓存到: {cache_file}")
            print(f"响应内容:\n{response}\n")
            
            # 解析响应
            parsed = self.parse_llm_response(response)
            
            if not parsed['hunks']:
                print("❌ 未能解析出有效的hunks")
                return None
            
            print(f"✅ 成功解析出{len(parsed['hunks'])}个hunks")
            return {
                'hunks': parsed['hunks'],
                'notes': parsed['notes']
            }
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            return None
    
    def process_all_benchmarks(self, input_file: str, output_file: str):
        """处理所有benchmark"""
        print("🚀 开始处理所有benchmark...")
        
        # 加载数据
        benchmarks = self.load_benchmark(input_file)
        print(f"加载了{len(benchmarks)}条benchmark")
        
        results = []
        success_count = 0
        
        for i, benchmark in enumerate(benchmarks, 1):
            rc_context = self.generate_rc_for_benchmark(benchmark, i)
            
            if rc_context:
                benchmark['rc_context'] = rc_context
                success_count += 1
                print(f"✅ 第{i}条处理成功")
            else:
                print(f"❌ 第{i}条处理失败")
            
            results.append(benchmark)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # 生成统计
        stats = {
            'generation_time': datetime.now().isoformat(),
            'total_benchmarks': len(benchmarks),
            'successful_generations': success_count,
            'failed_generations': len(benchmarks) - success_count,
            'success_rate': f"{success_count/len(benchmarks)*100:.1f}%",
            'model': self.model
        }
        
        with open('logs/improved_gen_log.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 处理完成!")
        print(f"成功率: {stats['success_rate']} ({success_count}/{len(benchmarks)})")
        print(f"结果保存到: {output_file}")
        print(f"日志保存到: logs/improved_gen_log.json")

def main():
    generator = ImprovedRCGenerator()
    generator.process_all_benchmarks(
        'benchmark/nl2code_java_F10L.jsonl',
        'benchmark/nl2code_java_F10L_improved_rc.jsonl'
    )

if __name__ == "__main__":
    main()
