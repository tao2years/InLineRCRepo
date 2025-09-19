#!/usr/bin/env python3
"""
端到端自动化运行脚本 - 可配置的处理器入口
使用方法：
    python run_end_to_end.py benchmark/nl2code_F20-40.jsonl 20-40
    python run_end_to_end.py benchmark/nl2code_F40-60.jsonl 40-60
"""

import sys
import os
import importlib.util

def update_config(input_file: str, suffix: str):
    """动态更新配置文件"""
    config_content = f'''# 配置文件 - 端到端自动化流程配置

# 输入配置
INPUT_BENCHMARK_FILE = "{input_file}"  # 输入的benchmark文件

# 输出配置
OUTPUT_FOLDER_PREFIX = "final_gpt4o_output"  # 输出文件夹前缀
OUTPUT_FOLDER_SUFFIX = "{suffix}"  # 输出文件夹后缀
OUTPUT_FOLDER_NAME = f"{{OUTPUT_FOLDER_PREFIX}}_{{OUTPUT_FOLDER_SUFFIX}}"  # 完整输出文件夹名

# GPT-5结果文件夹配置
GPT5_RESULTS_FOLDER = f"gpt5_results_{{OUTPUT_FOLDER_SUFFIX}}"  # GPT-5结果文件夹名

# RC生成配置
RC_PROMPT_TEMPLATE = "RC_prompt_v9_improved.txt"  # RC生成的prompt模板

# 模型配置
MODEL_NAME = "gpt-4o-2024-11-20"  # 模型名称（虽然不真实调用）

# 文件扩展名配置
JSON_EXTENSION = ".json"
TXT_EXTENSION = ".txt"

# 必需字段配置（留空的字段）
EMPTY_FIELDS = [
    "llm_response",
    "parsed_hunks"
]

# 必需字段配置（必须有的字段）
REQUIRED_FIELDS = [
    "prompt"  # 包含system_prompt和user_prompt
]

# 时间戳格式
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

print("✅ 配置文件加载完成")
print(f"📁 输入文件: {{INPUT_BENCHMARK_FILE}}")
print(f"📁 输出文件夹: {{OUTPUT_FOLDER_NAME}}")
print(f"📁 GPT-5结果文件夹: {{GPT5_RESULTS_FOLDER}}")
'''
    
    # 写入配置文件
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)

def run_processor():
    """运行处理器"""
    # 动态导入处理器模块
    spec = importlib.util.spec_from_file_location("end_to_end_processor", "end_to_end_processor.py")
    processor_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(processor_module)
    
    # 运行处理器
    processor = processor_module.EndToEndProcessor()
    processor.process_all()

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("使用方法:")
        print("  python run_end_to_end.py <输入文件路径> <输出后缀>")
        print()
        print("示例:")
        print("  python run_end_to_end.py benchmark/nl2code_F20-40.jsonl 20-40")
        print("  python run_end_to_end.py benchmark/nl2code_F40-60.jsonl 40-60")
        print("  python run_end_to_end.py benchmark/nl2code_F60-80.jsonl 60-80")
        print()
        print("这将生成:")
        print("  - final_gpt4o_output_<后缀>/  (包含JSON文件)")
        print("  - gpt5_results_<后缀>/       (包含空的TXT文件)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    suffix = sys.argv[2]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 输入文件不存在: {input_file}")
        sys.exit(1)
    
    print(f"🚀 开始处理: {input_file} -> 后缀: {suffix}")
    
    # 更新配置
    update_config(input_file, suffix)
    
    # 运行处理器
    run_processor()
    
    print(f"\n🎉 处理完成!")
    print(f"📁 输出文件夹: final_gpt4o_output_{suffix}")
    print(f"📁 GPT-5结果文件夹: gpt5_results_{suffix}")
    print(f"\n💡 下一步:")
    print(f"1. 手动填入GPT-5结果到 gpt5_results_{suffix}/ 文件夹中的txt文件")
    print(f"2. 运行合并脚本生成最终的benchmark文件")

if __name__ == "__main__":
    main()
