package com.example.context;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 演示 Inline Chat 上下文组织的复杂示例
 * 
 * 这个类展示了如何组织代码上下文
 */
public class ContextDemo {
    
    // 静态常量
    private static final int MAX_SIZE = 100;
    private static final String DEFAULT_NAME = "default";
    
    // 实例字段
    private String name;
    private List<String> items;
    private Map<String, Integer> counters;
    
    /**
     * 构造函数
     */
    public ContextDemo(String name) {
        this.name = name;
        this.items = new ArrayList<>();
        this.counters = new HashMap<>();
    }
    
    /**
     * 主要处理方法 - 这里会被选中
     */
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
    
    /**
     * 验证项目
     */
    private boolean isValidItem(String item) {
        return item != null && !item.trim().isEmpty() && item.length() <= MAX_SIZE;
    }
    
    /**
     * 处理单个项目
     */
    private String processItem(String item) {
        return item.trim().toLowerCase();
    }
    
    /**
     * 更新计数器
     */
    private void updateCounter(String item) {
        counters.merge(item, 1, Integer::sum);
    }
    
    /**
     * 后处理方法
     */
    private void postProcess() {
        // 排序项目
        items.sort(String::compareTo);
        
        // 清理计数器
        counters.entrySet().removeIf(entry -> entry.getValue() == 0);
    }
    
    // Getter 方法
    public String getName() { return name; }
    public List<String> getItems() { return new ArrayList<>(items); }
    public Map<String, Integer> getCounters() { return new HashMap<>(counters); }
}
