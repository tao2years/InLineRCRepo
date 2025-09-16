# 实际的 Prompt 输出示例

## 完整的 Prompt 内容

```
<system>
你是一个专业的代码审查和优化助手。请分析用户选中的代码片段，判断业务逻辑是否有误，并提供优化建议。

分析要求：
1. 识别潜在的业务逻辑错误
2. 分析性能问题
3. 检查代码健壮性
4. 提供具体的优化建议
5. 考虑线程安全和并发问题

请按照以下格式回答：
- 问题识别
- 原因分析
- 优化建议
- 代码示例

重点关注性能优化和代码质量改进。
</system>

<user>
请分析以下代码片段的业务逻辑是否有误，并提供优化建议：

【选中的代码】
```java
public void processData(List<String> dataList) {
    // 这里是选中的代码区域
    for (String data : dataList) {
        if (data != null && !data.isEmpty()) {
            // 处理逻辑
            String processed = data.trim().toLowerCase();
            config.put(processed, System.currentTimeMillis());
        }
    }
    
    // 更新版本
    version++;
}
```

【方法上下文】
```java
public void processData(List<String> dataList) {
    // 验证输入
    if (inputData == null || inputData.isEmpty()) {
        return;
    }
    
    // 处理每个项目
    for (String item : inputData) {
        if (isValidItem(item)) {
            String processed = processItem(item);
            items.add(processed);
            updateCounter(processed);
        }
    }
    
    // 后处理
    postProcess();
}
```

【类上下文】
```java
public class InlineChatDemo {
    private String name;
    private int version;
    private Map<String, Object> config;
    
    public InlineChatDemo(String name) {
        this.name = name;
        this.version = 1;
        this.config = new HashMap<>();
    }
    
    public Map<String, Object> getConfig() {
        return new HashMap<>(config);
    }
    
    public int getVersion() {
        return version;
    }
}
```

【文件上下文】
```java
package com.example.demo;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

/**
 * 演示 Inline Chat 上下文组织的示例类
 */
public class InlineChatDemo {
    // ... 类内容
}
```

【项目上下文】
- 项目类型：Java Maven 项目
- 主要依赖：Java 8+, Maven 3.6+
- 项目结构：包含 benchmark 数据和 shenyu 网关项目

请分析这段代码的业务逻辑问题并提供优化建议。
</user>
```

## 大模型的预期响应

```
## 问题识别

1. **输入验证不完整**：方法参数 `dataList` 没有进行 null 检查
2. **性能问题**：每次循环都调用 `System.currentTimeMillis()`，效率低下
3. **数据覆盖问题**：相同 key 的值会被覆盖，可能丢失历史数据
4. **线程安全问题**：`version++` 不是原子操作，存在并发问题
5. **业务逻辑不一致**：选中代码与完整方法逻辑不匹配

## 原因分析

1. **缺少防御性编程**：没有对输入参数进行充分验证
2. **时间戳重复计算**：在循环中重复调用系统时间函数
3. **Map 使用不当**：使用 `put()` 会覆盖已有值
4. **非原子操作**：`version++` 在多线程环境下不安全
5. **代码不一致**：选中代码与完整方法实现存在差异

## 优化建议

### 1. 输入验证优化
```java
public void processData(List<String> dataList) {
    // 添加输入验证
    if (dataList == null || dataList.isEmpty()) {
        return;
    }
    
    // 预先获取时间戳，避免重复计算
    long currentTime = System.currentTimeMillis();
    
    for (String data : dataList) {
        if (data != null && !data.isEmpty()) {
            String processed = data.trim().toLowerCase();
            // 使用 putIfAbsent 避免覆盖
            config.putIfAbsent(processed, currentTime);
        }
    }
    
    // 使用原子操作
    version.incrementAndGet();
}
```

### 2. 线程安全优化
```java
public class InlineChatDemo {
    private final AtomicInteger version = new AtomicInteger(1);
    private final ConcurrentHashMap<String, Object> config = new ConcurrentHashMap<>();
    
    public void processData(List<String> dataList) {
        if (dataList == null || dataList.isEmpty()) {
            return;
        }
        
        long currentTime = System.currentTimeMillis();
        
        for (String data : dataList) {
            if (data != null && !data.isEmpty()) {
                String processed = data.trim().toLowerCase();
                config.putIfAbsent(processed, currentTime);
            }
        }
        
        version.incrementAndGet();
    }
}
```

### 3. 业务逻辑优化
```java
public void processData(List<String> dataList) {
    if (dataList == null || dataList.isEmpty()) {
        return;
    }
    
    // 使用 Stream API 提高可读性
    long currentTime = System.currentTimeMillis();
    
    dataList.stream()
        .filter(Objects::nonNull)
        .filter(data -> !data.isEmpty())
        .map(String::trim)
        .map(String::toLowerCase)
        .forEach(processed -> config.putIfAbsent(processed, currentTime));
    
    version.incrementAndGet();
}
```

## 总结

主要问题集中在输入验证、性能优化、线程安全和业务逻辑一致性方面。建议使用原子操作、并发集合和 Stream API 来改进代码质量和性能。
```

## Token 使用统计

```
系统提示词：约 200 tokens
用户提示词：约 1,500 tokens
├── 选中代码：300 tokens
├── 方法上下文：400 tokens
├── 类上下文：300 tokens
├── 文件上下文：200 tokens
├── 项目上下文：100 tokens
└── 用户指令：200 tokens

总计：约 1,700 tokens
剩余：约 30,300 tokens (用于 AI 响应)
```

## 上下文组织验证

### 1. 选中代码完整性 ✅
- 完整保留了用户选中的代码片段
- 包含了所有相关的业务逻辑

### 2. 方法上下文相关性 ✅
- 提供了完整的方法实现
- 包含了相关的辅助方法调用

### 3. 类上下文完整性 ✅
- 包含了相关的字段定义
- 提供了构造函数和相关方法

### 4. 文件上下文完整性 ✅
- 包含了包声明和导入语句
- 提供了类的基本结构

### 5. 项目上下文相关性 ✅
- 包含了项目类型和依赖信息
- 提供了项目结构概览
