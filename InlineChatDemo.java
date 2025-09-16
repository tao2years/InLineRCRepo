package com.example.demo;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

/**
 * 演示 Inline Chat 上下文组织的示例类
 */
public class InlineChatDemo {
    
    // 类级别的字段
    private String name;
    private int version;
    private Map<String, Object> config;
    
    /**
     * 构造函数
     */
    public InlineChatDemo(String name) {
        this.name = name;
        this.version = 1;
        this.config = new HashMap<>();
    }
    
    /**
     * 主要业务方法 - 这里会被选中进行 Inline Chat
     */
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
    
    /**
     * 辅助方法
     */
    private void validateInput(String input) {
        if (input == null) {
            throw new IllegalArgumentException("Input cannot be null");
        }
    }
    
    /**
     * 获取配置信息
     */
    public Map<String, Object> getConfig() {
        return new HashMap<>(config);
    }
}
