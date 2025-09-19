# Agent调试工具套件

## 🎯 概述

这是一套专门用于调试和观察Agent执行流程的工具集，通过多样化的场景模拟和断点设置，帮助深入理解Agent的内部机制、context组织方式和决策过程。

## 📦 工具组件

### 1. 核心调试工具

| 文件名 | 功能描述 | 主要用途 |
|--------|----------|----------|
| `agent_debug_master.py` | 主控制器 | 统一入口，整合所有调试功能 |
| `agent_debug_tracer.py` | 基础追踪器 | 模拟基本Agent能力调用 |
| `agent_runtime_monitor.py` | 运行时监控器 | 实时性能和资源监控 |
| `agent_interaction_simulator.py` | 交互模拟器 | 复杂工作流和并发场景 |

### 2. 文档和指南

| 文件名 | 内容描述 |
|--------|----------|
| `agent_debug_guide.md` | 详细使用指南 |
| `README_agent_debug.md` | 快速入门指南 |

## 🚀 快速开始

### 基础使用

```bash
# 运行综合调试模式（推荐）
python agent_debug_master.py comprehensive --save-results

# 运行特定模式
python agent_debug_master.py basic          # 基础追踪
python agent_debug_master.py performance    # 性能监控
python agent_debug_master.py interaction    # 复杂交互
```

### 单独工具使用

```bash
# 基础追踪器
python agent_debug_tracer.py

# 运行时监控器
python agent_runtime_monitor.py

# 交互模拟器
python agent_interaction_simulator.py
```

## 🔍 调试模式详解

### 1. 基础追踪模式 (`basic`)
**目标**: 观察基本Agent能力调用
- ✅ 代码库分析场景 (`codebase-retrieval`)
- ✅ 文件操作场景 (`view`, `str-replace-editor`)
- ✅ 代码生成场景 (代码编写能力)
- ✅ 任务管理场景 (`add_tasks`, `update_tasks`)
- ✅ 错误处理场景 (异常处理机制)

### 2. 性能监控模式 (`performance`)
**目标**: 深度性能分析和资源监控
- 📊 实时CPU、内存、IO监控
- 📈 性能趋势分析
- 🔍 方法调用统计
- 💾 内存快照捕获
- ⚡ 热点方法识别

### 3. 复杂交互模式 (`interaction`)
**目标**: 复杂工作流和并发场景
- 🔄 多步骤工作流编排
- ⚡ 并发任务处理
- 🔗 依赖关系管理
- 🛡️ 资源竞争处理
- 🔄 错误恢复机制

### 4. 综合调试模式 (`comprehensive`)
**目标**: 全面的Agent能力评估
- 🎯 执行所有调试模式
- 📊 生成综合分析报告
- 💡 提供优化建议
- 📄 完整的调试记录

## 🎯 关键断点位置

### 高价值断点 (必设)

```python
# 1. 初始化和配置
# BREAKPOINT: 监控器初始化完成 - 观察初始状态

# 2. 查询和检索
# BREAKPOINT: 查询context构建完成 - 观察context结构

# 3. 文件操作
# BREAKPOINT: 文件context准备完成 - 观察文件元数据

# 4. 任务管理
# BREAKPOINT: 任务创建完成 - 观察任务管理逻辑

# 5. 性能监控
# BREAKPOINT: 每次监控循环 - 观察性能数据采集

# 6. 并发处理
# BREAKPOINT: 并发执行开始 - 观察线程调度

# 7. 错误处理
# BREAKPOINT: 异常记录 - 观察异常数据结构
```

### 性能观察点

```python
# 内存分配
# BREAKPOINT: 每次内存分配 - 观察内存增长

# CPU使用
# BREAKPOINT: 每次计算 - 观察CPU负载

# 资源竞争
# BREAKPOINT: 资源获取 - 观察资源分配
```

## 📊 输出文件说明

### 调试报告文件

| 文件模式 | 文件名格式 | 内容描述 |
|----------|------------|----------|
| 基础追踪 | `agent_debug_report_[session_id].json` | 基础能力调用记录 |
| 性能监控 | `agent_runtime_report_[timestamp].json` | 性能监控数据 |
| 交互模拟 | `agent_simulation_result_[timestamp].json` | 工作流执行结果 |
| 综合调试 | `agent_debug_master_results_[timestamp].json` | 完整调试记录 |

### 日志文件

- `agent_debug.log`: 详细执行日志
- 包含时间戳、级别、消息内容

## 🔧 高级使用技巧

### 1. 自定义监控间隔

```python
# 修改监控频率
monitor = AgentRuntimeMonitor(monitor_interval=0.01)  # 10ms间隔
```

### 2. 添加自定义断点

```python
@monitor_method
def your_custom_function():
    # BREAKPOINT: 自定义功能 - 观察特定逻辑
    pass
```

### 3. 内存快照对比

```python
# 操作前快照
monitor.capture_memory_snapshot("before_operation")

# 执行操作
your_operation()

# 操作后快照
monitor.capture_memory_snapshot("after_operation")
```

### 4. 性能热点分析

```python
# 获取最耗时的方法
top_methods = monitor.get_top_methods(limit=10)
for method_info in top_methods:
    print(f"Method: {method_info['method']}")
    print(f"Total time: {method_info['stats']['total_time']:.3f}s")
```

## 🎨 IDE调试设置

### VS Code设置

1. 打开调试面板 (Ctrl+Shift+D)
2. 创建launch.json配置:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Agent Debug Master",
            "type": "python",
            "request": "launch",
            "program": "agent_debug_master.py",
            "args": ["comprehensive", "--save-results"],
            "console": "integratedTerminal"
        }
    ]
}
```

3. 在所有 `# BREAKPOINT:` 注释行设置断点

### PyCharm设置

1. 右键点击 `agent_debug_master.py`
2. 选择 "Debug 'agent_debug_master'"
3. 在断点位置点击行号设置断点
4. 使用调试工具栏控制执行流程

## 📈 观察要点

### Context组织方式
- **查询Context**: Agent如何构建和传递查询参数
- **文件Context**: 文件操作的元数据管理方式
- **任务Context**: 任务状态和依赖关系维护
- **错误Context**: 错误信息的结构化存储

### 决策过程
- **策略选择**: Agent在多个选项中的选择逻辑
- **优先级排序**: 任务和操作的优先级计算方法
- **资源分配**: 内存和时间资源的分配策略

### 执行流程
- **调用链**: 方法调用的顺序和层次结构
- **状态变更**: 对象状态的变化时机和原因
- **异常传播**: 异常在调用栈中的传播路径

## ⚠️ 注意事项

### 性能影响
- 监控会带来5-10%的性能开销
- 大数据操作可能消耗较多内存
- 建议在测试环境中使用

### 文件管理
- 调试过程会生成多个临时文件
- 定期清理调试日志和报告文件
- 注意磁盘空间使用

### 断点设置
- 避免在高频循环中设置过多断点
- 重点关注关键决策点和状态变更
- 使用条件断点减少中断次数

## 🎉 预期收获

通过使用这套调试工具，您将能够：

1. **深入理解Agent内部机制**
   - 观察context的组织和传递方式
   - 理解决策过程和优化策略
   - 发现性能瓶颈和改进机会

2. **掌握Agent能力边界**
   - 了解各种能力的使用场景
   - 观察能力间的协作方式
   - 识别能力的限制和扩展点

3. **优化Agent使用方式**
   - 学习最佳实践模式
   - 避免常见的性能陷阱
   - 提高Agent使用效率

4. **为Agent开发提供数据支持**
   - 收集真实的使用数据
   - 分析用户行为模式
   - 指导功能改进方向

## 🔗 相关资源

- [详细使用指南](agent_debug_guide.md)
- [性能优化建议](performance_tips.md)
- [常见问题解答](faq.md)
- [扩展开发指南](extension_guide.md)

---

**开始您的Agent调试之旅吧！** 🚀
