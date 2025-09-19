# Agent调试追踪器使用指南

## 🎯 目标
通过多样化的Agent能力调用来观察Agent的内部执行流程、context组织方式和决策过程。

## 📋 功能覆盖

### 1. 代码库分析场景 (`simulate_codebase_analysis`)
**触发能力**: `codebase-retrieval`
- 模拟多种查询类型
- 观察查询参数构建
- 追踪检索结果处理

**关键断点位置**:
```python
# 查询构建过程
query_context = {
    "query": query,
    "timestamp": datetime.now().isoformat(),
    # ... 观察context结构
}
```

### 2. 文件操作场景 (`simulate_file_operations`)
**触发能力**: `view`, `str-replace-editor`, `save-file`
- 文件路径解析
- 权限检查机制
- 文件元数据获取

**关键断点位置**:
```python
file_context = {
    "file_path": file_path,
    "exists": os.path.exists(file_path),
    # ... 观察文件处理逻辑
}
```

### 3. 代码生成场景 (`simulate_code_generation`)
**触发能力**: 代码编写和模板处理
- 多语言代码生成
- 模板选择策略
- 分步骤生成过程

**关键断点位置**:
```python
generation_context = {
    "task_description": task["task"],
    "target_language": task["language"],
    # ... 观察生成策略
}
```

### 4. 任务管理场景 (`simulate_task_management`)
**触发能力**: `add_tasks`, `update_tasks`, `view_tasklist`
- 任务分解策略
- 依赖关系建立
- 状态更新机制

**关键断点位置**:
```python
task = {
    "id": f"task_{i+1}",
    "name": task_name,
    "dependencies": [],
    # ... 观察任务管理逻辑
}
```

### 5. 错误处理场景 (`simulate_error_handling`)
**触发能力**: 异常处理和恢复机制
- 错误检测和分类
- 恢复策略选择
- 失败后清理工作

**关键断点位置**:
```python
error_context = {
    "error_type": scenario["type"],
    "recovery_attempts": [],
    # ... 观察错误处理流程
}
```

### 6. 内存密集型操作 (`simulate_memory_intensive_operations`)
**触发能力**: 内存管理和优化
- 大数据处理
- 内存分配策略
- 垃圾回收触发

**关键断点位置**:
```python
large_data = {
    "size": data_size,
    "data": list(range(data_size)),
    # ... 观察内存使用模式
}
```

## 🔧 使用方法

### 1. 基础运行
```bash
python agent_debug_tracer.py
```

### 2. 调试模式运行
在IDE中设置断点后运行：
```bash
# VS Code
code agent_debug_tracer.py
# 设置断点到所有 # BREAKPOINT: 注释处

# PyCharm
# 打开文件，在断点位置点击行号设置断点
```

### 3. 高级调试
```python
# 在Python调试器中运行
import pdb
pdb.set_trace()  # 在关键位置插入
```

## 📊 观察要点

### Context组织方式
- **查询Context**: 观察Agent如何构建和传递查询参数
- **文件Context**: 观察文件操作的元数据管理
- **任务Context**: 观察任务状态和依赖关系维护
- **错误Context**: 观察错误信息的结构化存储

### 决策过程
- **策略选择**: 观察Agent在多个选项中的选择逻辑
- **优先级排序**: 观察任务和操作的优先级计算
- **资源分配**: 观察内存和时间资源的分配策略

### 执行流程
- **调用链**: 观察方法调用的顺序和层次
- **状态变更**: 观察对象状态的变化时机
- **异常传播**: 观察异常在调用栈中的传播路径

## 🎯 重点断点位置

### 高价值断点
1. **初始化完成**: `AgentDebugTracer.__init__()` 结束
2. **查询构建**: 每个`query_context`创建后
3. **文件操作**: 文件权限检查和元数据获取
4. **任务创建**: 每个任务对象创建完成
5. **错误恢复**: 每个恢复策略尝试前后
6. **内存分配**: 大数据对象创建前后
7. **报告生成**: 最终数据汇总完成

### 性能观察点
- **内存使用**: 在大数据操作前后观察内存变化
- **执行时间**: 在耗时操作前后记录时间戳
- **资源竞争**: 在并发操作中观察资源访问

## 📈 输出分析

### 日志文件
- `agent_debug.log`: 详细的执行日志
- 包含时间戳、级别、消息内容

### 调试报告
- `agent_debug_report_[session_id].json`: 结构化的调试数据
- 包含所有trace数据和context快照

### 报告结构
```json
{
  "session_id": "debug_session_20250919_105700",
  "generated_at": "2025-09-19T10:57:00",
  "total_traces": 20,
  "total_snapshots": 15,
  "summary": {
    "scenarios_executed": 6,
    "total_operations": 35
  },
  "trace_data": [...],
  "context_snapshots": [...]
}
```

## 🚀 扩展建议

### 添加新场景
1. **网络操作**: 模拟`web-search`, `web-fetch`
2. **进程管理**: 模拟`launch-process`, `read-process`
3. **Git操作**: 模拟`git-commit-retrieval`
4. **诊断功能**: 模拟`diagnostics`

### 增强观察能力
1. **性能监控**: 添加CPU、内存、IO监控
2. **调用图**: 生成方法调用关系图
3. **时序分析**: 分析操作的时间序列模式
4. **资源追踪**: 追踪文件句柄、网络连接等资源

## ⚠️ 注意事项

1. **断点设置**: 不要在循环内设置过多断点，避免调试过程过长
2. **内存监控**: 大数据操作可能消耗较多内存，注意监控
3. **日志大小**: 长时间运行可能产生大量日志，注意清理
4. **并发安全**: 如果扩展为多线程，注意线程安全问题

## 🎉 预期收获

通过使用这个调试追踪器，您将能够：
- 深入理解Agent的内部工作机制
- 观察不同场景下的context组织方式
- 分析Agent的决策过程和优化点
- 发现潜在的性能瓶颈和改进机会
- 为Agent能力的进一步开发提供数据支持
