# Inline Chat Token 管理演示

## Token 分配策略

### 1. 基础分配
```
总 Token 限制：32,000 tokens
├── 系统提示词：2,000 tokens (6.25%)
├── 用户输入：1,000 tokens (3.125%)
├── 选中代码：8,000 tokens (25%) - 最高优先级
├── 方法上下文：6,000 tokens (18.75%)
├── 类上下文：4,000 tokens (12.5%)
├── 文件上下文：3,000 tokens (9.375%)
├── 项目上下文：2,000 tokens (6.25%)
└── 响应缓冲：6,000 tokens (18.75%)
```

### 2. 动态调整策略
```
当选中代码超过 8K tokens 时：
├── 选中代码：实际大小 (不截断)
├── 方法上下文：减少到 4K tokens
├── 类上下文：减少到 2K tokens
├── 文件上下文：减少到 1K tokens
└── 项目上下文：减少到 500 tokens
```

### 3. 截断算法
```
截断优先级：
1. 保留选中代码完整内容
2. 保留方法签名和核心逻辑
3. 保留类字段和构造函数
4. 保留相关方法调用
5. 截断注释和文档
6. 截断导入语句
7. 截断项目级上下文
```

## 上下文组织示例

### 选中代码：processItems 方法
```java
public void processItems(List<String> inputItems) {
    // 验证输入
    if (inputItems == null || inputItems.isEmpty()) {
        return;
    }
    
    // 处理每个项目
    for (String item : inputItems) {
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

### 包含的上下文：
1. **方法上下文**：完整方法体
2. **类上下文**：相关字段 (items, counters)
3. **相关方法**：isValidItem, processItem, updateCounter, postProcess
4. **文件上下文**：导入语句和包声明
5. **项目上下文**：相关配置和依赖

### 截断后的上下文：
```
如果超过 Token 限制：
├── 保留：选中代码 + 方法签名
├── 保留：相关字段和构造函数
├── 保留：核心方法调用
├── 截断：详细注释
├── 截断：完整导入列表
└── 截断：项目级配置
```
