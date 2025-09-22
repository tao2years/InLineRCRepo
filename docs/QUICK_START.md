# InLineRCRepo 快速上手指南

## 📋 项目状态
**✅ 项目已完成！** 所有目标已达成，数据质量完美。

## 📁 关键文件
```
InLineRCRepo/
├── benchmark/
│   ├── nl2code_java_all_20_with_rc.jsonl          # 🎯 最终评测数据 (20条)
│   └── nl2code_java_all_20_with_rc_stats.json     # 📊 统计信息
├── modify_rc_diff.py                              # 🔧 RC diff修改工具
├── evaluation_prompt_template_v3.txt              # 📝 最终prompt模板
├── gpt5_manual_10/ 和 gpt5_manual_20/             # 📂 高质量GPT-5数据源
├── instruction.md                                 # 📚 完整项目历史
└── README.md                                      # 📖 项目说明
```

## 🎯 核心成果

### 最终benchmark数据
- **文件**: `benchmark/nl2code_java_all_20_with_rc.jsonl`
- **数量**: 20条完整benchmark
- **质量**: 100%来自GPT-5手动修复版本
- **特点**: 
  - ✅ 行号完美对应
  - ✅ 所有RC都是添加操作(+)
  - ✅ 正确的演进逻辑 RC3→RC2→RC1→最终实现

### RC diff修改工具
- **文件**: `modify_rc_diff.py`
- **功能**: 动态修改任意行的Recent Changes diff符号
- **用法**: `python modify_rc_diff.py <行号> <RC3标志> <RC2标志> <RC1标志>`
- **标志**: 0=反转符号(+↔-)，1=保持不变

## 🚀 常用命令

### 查看benchmark内容
```bash
# 查看文件行数
wc -l benchmark/nl2code_java_all_20_with_rc.jsonl

# 查看第5行的RC内容
python modify_rc_diff.py 5 1 1 1 --preview
```

### 修改RC diff符号

0: 变
1：不变

```bash
# 修改第5行：RC3不变，RC2反转，RC1不变
python modify_rc_diff.py 5 1 0 1

# 预览模式（不实际修改）
python modify_rc_diff.py 5 1 0 1 --preview

# 输出到新文件
python modify_rc_diff.py 5 1 0 1 --output modified_benchmark.jsonl
```

## 📊 数据质量保证

### RC演进逻辑
每个benchmark都遵循正确的演进逻辑：
1. **RC3 (最早准备)**: 添加基础方法/功能 (+)
2. **RC2 (中期准备)**: 添加辅助方法/配置 (+)
3. **RC1 (最新准备)**: 添加注解/最后准备 (+)
4. **最终任务**: 实现目标功能

### 技术特点
- **行号对应**: diff行号与代码行号完美匹配
- **Diff方向**: 所有RC都是正确的添加操作
- **混合diff支持**: 正确处理同一diff中的+/-混合情况
- **数据来源**: 100%使用GPT-5手动验证和修复的高质量数据

## 🔧 技术细节

### Prompt结构
```
External Imports
↓
Current File Content (带行号)
↓
Recent Changes Context
├── Recent Change 3 (最早准备)
├── Recent Change 2 (中期准备)
└── Recent Change 1 (最新准备)
↓
Task Description
```

### 关键修复点
1. **目标实现行删除**: 删除带有`// [禁止修改-目标实现]`注释的行
2. **Diff方向修正**: 修正GPT-5的倒推逻辑错误
3. **行号一致性**: 基于final_code_with_annotations确保行号对应
4. **数据源统一**: 完全使用gpt5_manual_X文件夹的数据

## 📈 使用场景

### 模型评测
- 评估Recent Changes对InlineEdit效果的提升
- 对比不同模型在RC上下文下的表现
- 研究RC信息对代码生成质量的影响

### 数据分析
- 分析不同类型RC的效果差异
- 研究RC演进逻辑对模型理解的影响
- 评估行号对应的重要性

## 🎉 项目价值

现在您拥有了：
- **完美的评测数据**: 20条高质量benchmark
- **灵活的修改工具**: 可动态调整RC diff符号
- **完整的技术文档**: 便于后续维护和扩展
- **标准化格式**: 兼容主流评测框架

**🎯 项目目标100%达成！**

---

*创建时间: 2025-09-17*
*最后更新: 2025-09-17*
