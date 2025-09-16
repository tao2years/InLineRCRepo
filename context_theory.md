# Inline Chat 上下文分析的理论依据

## 1. 软件工程理论基础

### 1.1 程序分析理论
```
程序分析理论：
├── 静态分析 (Static Analysis)
│   ├── 数据流分析 (Data Flow Analysis)
│   ├── 控制流分析 (Control Flow Analysis)
│   ├── 别名分析 (Alias Analysis)
│   └── 指针分析 (Pointer Analysis)
├── 动态分析 (Dynamic Analysis)
│   ├── 执行跟踪 (Execution Tracing)
│   ├── 性能分析 (Performance Analysis)
│   └── 内存分析 (Memory Analysis)
└── 混合分析 (Hybrid Analysis)
    ├── 符号执行 (Symbolic Execution)
    ├── 模型检查 (Model Checking)
    └── 抽象解释 (Abstract Interpretation)
```

### 1.2 代码理解理论
```
代码理解理论：
├── 语法理解 (Syntactic Understanding)
│   ├── AST 解析 (AST Parsing)
│   ├── 语法树遍历 (Syntax Tree Traversal)
│   └── 语法模式匹配 (Syntax Pattern Matching)
├── 语义理解 (Semantic Understanding)
│   ├── 类型推断 (Type Inference)
│   ├── 符号解析 (Symbol Resolution)
│   └── 语义角色标注 (Semantic Role Labeling)
└── 语用理解 (Pragmatic Understanding)
    ├── 意图识别 (Intent Recognition)
    ├── 上下文推理 (Contextual Reasoning)
    └── 领域知识应用 (Domain Knowledge Application)
```

## 2. 上下文选择的理论依据

### 2.1 信息论基础
```
信息论基础：
├── 信息熵 (Information Entropy)
│   ├── 选中代码的信息熵：H(S) = -Σ P(si) log P(si)
│   ├── 上下文的信息熵：H(C) = -Σ P(ci) log P(ci)
│   └── 互信息：I(S;C) = H(S) + H(C) - H(S,C)
├── 信息增益 (Information Gain)
│   ├── IG(S,C) = H(S) - H(S|C)
│   └── 选择信息增益最大的上下文
└── 相对熵 (Relative Entropy)
    ├── KL散度：DKL(P||Q) = Σ P(x) log(P(x)/Q(x))
    └── 选择KL散度最小的上下文
```

### 2.2 图论基础
```
图论基础：
├── 调用图 (Call Graph)
│   ├── 节点：方法/函数
│   ├── 边：调用关系
│   └── 路径：调用链
├── 依赖图 (Dependency Graph)
│   ├── 节点：类/模块
│   ├── 边：依赖关系
│   └── 连通分量：相关模块
└── 控制流图 (Control Flow Graph)
    ├── 节点：基本块
    ├── 边：控制流
    └── 路径：执行路径
```

## 3. 相关方法判断的算法

### 3.1 基于调用关系的判断
```
调用关系算法：
├── 直接调用 (Direct Call)
│   ├── 方法A直接调用方法B
│   ├── 相关度：1.0
│   └── 判断条件：A.body.contains(B.name)
├── 间接调用 (Indirect Call)
│   ├── 方法A通过方法C调用方法B
│   ├── 相关度：0.8
│   └── 判断条件：存在调用链 A→C→B
└── 递归调用 (Recursive Call)
    ├── 方法A递归调用自身
    ├── 相关度：0.9
    └── 判断条件：A.name == B.name
```

### 3.2 基于变量共享的判断
```
变量共享算法：
├── 类字段共享 (Field Sharing)
│   ├── 方法A和方法B访问同一个类字段
│   ├── 相关度：0.7
│   └── 判断条件：A.fields ∩ B.fields ≠ ∅
├── 参数传递 (Parameter Passing)
│   ├── 方法A的返回值作为方法B的参数
│   ├── 相关度：0.8
│   └── 判断条件：A.returnType == B.parameterType
└── 局部变量模式 (Local Variable Pattern)
    ├── 方法A和方法B使用相似的局部变量模式
    ├── 相关度：0.5
    └── 判断条件：similarity(A.variables, B.variables) > threshold
```

### 3.3 基于代码模式的判断
```
代码模式算法：
├── 结构模式 (Structural Pattern)
│   ├── 相似的控制流结构
│   ├── 相关度：0.6
│   └── 判断条件：structural_similarity(A, B) > threshold
├── 异常处理模式 (Exception Handling Pattern)
│   ├── 相似的异常处理逻辑
│   ├── 相关度：0.7
│   └── 判断条件：exception_similarity(A, B) > threshold
└── 算法模式 (Algorithm Pattern)
    ├── 相似的算法实现
    ├── 相关度：0.8
    └── 判断条件：algorithm_similarity(A, B) > threshold
```

## 4. 具体实现算法

### 4.1 上下文提取算法
```python
def extract_context(selected_code, file_content, project_info):
    context = {
        'selected': selected_code,
        'method': extract_method_context(selected_code, file_content),
        'class': extract_class_context(selected_code, file_content),
        'file': extract_file_context(file_content),
        'project': extract_project_context(project_info)
    }
    
    # 计算相关度
    for key in context:
        context[key]['relevance'] = calculate_relevance(context[key], selected_code)
    
    # 按相关度排序
    context = sort_by_relevance(context)
    
    # 应用Token限制
    context = apply_token_limits(context)
    
    return context
```

### 4.2 相关方法查找算法
```python
def find_related_methods(selected_code, class_methods):
    related_methods = []
    
    for method in class_methods:
        relevance = 0.0
        
        # 调用关系相关度
        if has_call_relation(selected_code, method):
            relevance += 0.4
        
        # 变量共享相关度
        if has_variable_sharing(selected_code, method):
            relevance += 0.3
        
        # 模式相似性相关度
        pattern_similarity = calculate_pattern_similarity(selected_code, method)
        relevance += pattern_similarity * 0.2
        
        # 语义相似性相关度
        semantic_similarity = calculate_semantic_similarity(selected_code, method)
        relevance += semantic_similarity * 0.1
        
        if relevance > 0.5:  # 阈值
            related_methods.append((method, relevance))
    
    # 按相关度排序
    related_methods.sort(key=lambda x: x[1], reverse=True)
    
    return [method for method, _ in related_methods]
```

### 4.3 Token管理算法
```python
def manage_tokens(context, max_tokens=32000):
    # 计算各部分Token使用
    token_usage = {
        'selected': estimate_tokens(context['selected']),
        'method': estimate_tokens(context['method']),
        'class': estimate_tokens(context['class']),
        'file': estimate_tokens(context['file']),
        'project': estimate_tokens(context['project'])
    }
    
    total_tokens = sum(token_usage.values())
    
    if total_tokens <= max_tokens:
        return context
    
    # 按优先级截断
    remaining_tokens = max_tokens
    
    # 1. 保留选中代码
    remaining_tokens -= token_usage['selected']
    
    # 2. 截断方法上下文
    method_limit = min(token_usage['method'], remaining_tokens * 0.3)
    context['method'] = truncate_context(context['method'], method_limit)
    remaining_tokens -= method_limit
    
    # 3. 截断类上下文
    class_limit = min(token_usage['class'], remaining_tokens * 0.2)
    context['class'] = truncate_context(context['class'], class_limit)
    remaining_tokens -= class_limit
    
    # 4. 截断文件上下文
    file_limit = min(token_usage['file'], remaining_tokens * 0.1)
    context['file'] = truncate_context(context['file'], file_limit)
    remaining_tokens -= file_limit
    
    # 5. 截断项目上下文
    project_limit = min(token_usage['project'], remaining_tokens)
    context['project'] = truncate_context(context['project'], project_limit)
    
    return context
```

## 5. 实际应用示例

### 5.1 选中代码分析
```java
// 选中的代码
public void processData(List<String> dataList) {
    for (String data : dataList) {
        if (data != null && !data.isEmpty()) {
            String processed = data.trim().toLowerCase();
            config.put(processed, System.currentTimeMillis());
        }
    }
    version++;
}
```

### 5.2 上下文提取结果
```
提取的上下文：
├── 选中代码：processData方法 (100% 保留)
├── 方法上下文：
│   ├── 方法签名：public void processData(List<String> dataList)
│   ├── 参数类型：List<String>
│   ├── 返回值类型：void
│   └── 方法体：完整方法体
├── 类上下文：
│   ├── 相关字段：config, version
│   ├── 相关方法：getConfig(), getVersion()
│   └── 构造函数：InlineChatDemo(String name)
├── 文件上下文：
│   ├── 导入语句：java.util.*
│   ├── 包声明：com.example.demo
│   └── 类声明：public class InlineChatDemo
└── 项目上下文：
    ├── 相关类：ConfigManager, DataProcessor
    ├── 配置文件：application.properties
    └── 依赖：Spring Framework
```

### 5.3 相关方法判断结果
```
相关方法：
├── 高相关度 (0.8-1.0)：
│   ├── getConfig() - 直接访问config字段
│   └── getVersion() - 直接访问version字段
├── 中等相关度 (0.5-0.8)：
│   ├── validateInput() - 相似的输入验证逻辑
│   └── cleanup() - 相似的数据处理逻辑
└── 低相关度 (0.3-0.5)：
    ├── constructor - 初始化相关字段
    └── toString() - 可能使用相关字段
```
