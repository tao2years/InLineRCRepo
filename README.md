# InLineRC Benchmark Repository

## 📋 项目概述

InLineRC是一个基于Java代码补全的Benchmark项目，专注于通过Recent Changes (RC)上下文增强来提升代码生成质量。项目基于ShenYu开源项目，构建了包含40条高质量benchmark数据的测试集。

## 🏗️ 项目结构

```
InLineRCRepo/
├── benchmark/                    # Benchmark数据文件
│   ├── nl2code_java_all_20_with_rc_separated_final.jsonl    # 前20条separated格式
│   ├── nl2code_java_F20-40_with_rc_separated.jsonl          # 后20条separated格式
│   └── nl2code_F20-40.jsonl                                 # 原始F20-40数据
├── final_gpt4o_output_*/         # GPT-4o输出文件夹
│   ├── final_gpt4o_output_10/    # 前10条处理结果
│   ├── final_gpt4o_output_20/    # 前20条处理结果
│   └── final_gpt4o_output_20-40/ # F20-40条处理结果
├── gpt5_results_20-40/           # GPT-5手动生成的RC结果
├── scripts/                      # 核心脚本
│   ├── build_benchmark_20_40.py          # F20-40 benchmark构建脚本
│   ├── end_to_end_processor.py           # 端到端处理器
│   ├── run_end_to_end.py                 # 一键运行脚本
│   ├── generate_separated_benchmark.py   # 生成separated格式
│   ├── validate_separated_benchmark.py   # 验证benchmark质量
│   └── improve_line_numbers.py           # 行号改进工具
├── templates/                    # 模板文件
│   ├── evaluation_prompt_template_v4_separated.txt  # V4 separated模板
│   ├── evaluation_prompt_template_v3.txt           # V3模板
│   └── RC_prompt_v9_improved.txt                   # RC生成提示模板
├── tools/                        # 工具脚本
│   ├── modify_rc_diff.py         # RC diff修改工具
│   └── config.py                 # 配置文件
├── docs/                         # 文档
│   ├── README.md                 # 项目说明
│   ├── instruction.md            # 详细指令文档
│   ├── QUICK_START.md           # 快速开始指南
│   └── Recent Changes设计.pptx   # RC设计文档
├── backup/                       # 备份文件
└── LICENSE
```

## 🚀 快速开始

### 1. 处理新的benchmark数据

```bash
# 处理新的JSONL数据（例如F40-60）
python scripts/run_end_to_end.py benchmark/nl2code_F40-60.jsonl 40-60
```

### 2. 构建完整benchmark

```bash
# 构建F20-40的完整benchmark（需要先填入GPT-5结果）
python scripts/build_benchmark_20_40.py
```

### 3. 修改RC diff格式

```bash
# 修改benchmark中的RC diff格式
python tools/modify_rc_diff.py
```

## 📊 当前状态

- ✅ **F1-10**: 已完成 (10条)
- ✅ **F11-20**: 已完成 (10条) 
- ✅ **F21-40**: 已完成 (20条) - **新增**
- 🔄 **总计**: 40条高质量benchmark数据

## 🎯 核心特性

### Recent Changes (RC) 上下文增强
- **RC3 (最早准备)**: 基础设施和常量定义
- **RC2 (中间准备)**: 核心逻辑和方法实现  
- **RC1 (最近准备)**: 最终优化和错误处理

### Separated格式支持
- 分离的context above/below结构
- 保持代码缩进的完整性
- 支持行号标注和精确定位

### 端到端自动化
- 一键处理新数据
- 自动生成文件夹结构
- 配置驱动的灵活处理

## 📖 详细文档

- [详细指令文档](docs/instruction.md) - 完整的操作指南
- [快速开始指南](docs/QUICK_START.md) - 新手入门
- [RC设计文档](docs/Recent%20Changes设计.pptx) - Recent Changes设计理念

## 🔧 工具说明

| 工具 | 功能 | 用途 |
|------|------|------|
| `run_end_to_end.py` | 端到端处理 | 处理新的JSONL数据 |
| `build_benchmark_20_40.py` | Benchmark构建 | 合并GPT-5结果生成最终benchmark |
| `modify_rc_diff.py` | RC修改 | 调整diff格式和内容 |
| `validate_separated_benchmark.py` | 质量验证 | 验证benchmark数据质量 |

## 📈 质量保证

- **100%成功率**: 所有40条数据处理成功
- **格式一致性**: 统一的JSON结构和字段
- **内容完整性**: 保留所有原始信息和metadata
- **可追溯性**: 完整的处理链路记录

## 🤝 贡献指南

1. 新增数据请使用标准JSONL格式
2. 运行验证脚本确保质量
3. 更新相关文档和统计信息
4. 遵循现有的命名和结构规范

---

**最后更新**: 2025-09-19  
**版本**: v2.0 (F20-40扩展版)
