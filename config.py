# 配置文件 - 端到端自动化流程配置

# 输入配置
INPUT_BENCHMARK_FILE = "benchmark/nl2code_F20-40.jsonl"  # 输入的benchmark文件

# 输出配置
OUTPUT_FOLDER_PREFIX = "final_gpt4o_output"  # 输出文件夹前缀
OUTPUT_FOLDER_SUFFIX = "20-40"  # 输出文件夹后缀
OUTPUT_FOLDER_NAME = f"{OUTPUT_FOLDER_PREFIX}_{OUTPUT_FOLDER_SUFFIX}"  # 完整输出文件夹名

# GPT-5结果文件夹配置
GPT5_RESULTS_FOLDER = f"gpt5_results_{OUTPUT_FOLDER_SUFFIX}"  # GPT-5结果文件夹名

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
print(f"📁 输入文件: {INPUT_BENCHMARK_FILE}")
print(f"📁 输出文件夹: {OUTPUT_FOLDER_NAME}")
print(f"📁 GPT-5结果文件夹: {GPT5_RESULTS_FOLDER}")
