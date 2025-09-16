package com.example.inlinechat;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Inline Chat 使用示例
 * 
 * 演示如何在实际开发中使用 Inline Chat 功能
 */
public class InlineChatExample {
    
    private Map<String, List<String>> dataMap;
    private Set<String> processedKeys;
    
    public InlineChatExample() {
        this.dataMap = new HashMap<>();
        this.processedKeys = new HashSet<>();
    }
    
    /**
     * 主要处理方法 - 这里会使用 Inline Chat
     * 
     * 用户选中这个方法，然后使用 Inline Chat 询问：
     * "如何优化这个方法的性能？"
     */
    public void processData(Map<String, List<String>> inputData) {
        // 验证输入数据
        if (inputData == null || inputData.isEmpty()) {
            return;
        }
        
        // 处理每个键值对
        for (Map.Entry<String, List<String>> entry : inputData.entrySet()) {
            String key = entry.getKey();
            List<String> values = entry.getValue();
            
            // 检查是否已处理
            if (processedKeys.contains(key)) {
                continue;
            }
            
            // 处理值列表
            List<String> processedValues = new ArrayList<>();
            for (String value : values) {
                if (value != null && !value.trim().isEmpty()) {
                    String processed = value.trim().toLowerCase();
                    processedValues.add(processed);
                }
            }
            
            // 存储处理结果
            if (!processedValues.isEmpty()) {
                dataMap.put(key, processedValues);
                processedKeys.add(key);
            }
        }
        
        // 后处理
        cleanup();
    }
    
    /**
     * 清理方法
     */
    private void cleanup() {
        // 移除空值
        dataMap.entrySet().removeIf(entry -> entry.getValue().isEmpty());
        
        // 排序键
        Map<String, List<String>> sortedMap = new TreeMap<>(dataMap);
        dataMap.clear();
        dataMap.putAll(sortedMap);
    }
    
    /**
     * 获取处理结果
     */
    public Map<String, List<String>> getProcessedData() {
        return new HashMap<>(dataMap);
    }
    
    /**
     * 获取已处理的键
     */
    public Set<String> getProcessedKeys() {
        return new HashSet<>(processedKeys);
    }
}
