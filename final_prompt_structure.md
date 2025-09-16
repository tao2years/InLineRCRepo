# 最终发送给大模型的 Prompt 结构

## 系统提示词 (System Prompt)
```
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
```

## 用户提示词 (User Prompt)
```
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
```

## 完整的 Prompt 拼接

### 1. 系统提示词部分
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
</system>
```

### 2. 用户提示词部分
```
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

## Token 使用统计

### 各部分 Token 使用
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

## 上下文组织策略

### 1. 优先级排序
```
1. 选中代码 (100% 保留)
2. 方法上下文 (80% 保留)
3. 类上下文 (60% 保留)
4. 文件上下文 (40% 保留)
5. 项目上下文 (20% 保留)
```

### 2. 智能截断
```
如果超过 Token 限制：
├── 保留：选中代码 + 方法签名
├── 保留：相关字段和构造函数
├── 保留：核心方法调用
├── 截断：详细注释
├── 截断：完整导入列表
└── 截断：项目级配置
```

### 3. 语义完整性
```
确保保留：
├── 方法逻辑完整
├── 变量作用域
├── 调用关系
├── 类结构
└── 核心业务逻辑
```
