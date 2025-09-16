package com.cursor.context;

import java.util.*;

/**
 * Inline Chat Prompt 构建器
 * 
 * 演示如何构建发送给大模型的完整 Prompt
 */
public class PromptBuilder {
    
    private static final String SYSTEM_PROMPT_TEMPLATE = """
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
        """;
    
    private static final String USER_PROMPT_TEMPLATE = """
        请分析以下代码片段的业务逻辑是否有误，并提供优化建议：
        
        【选中的代码】
        ```java
        %s
        ```
        
        【方法上下文】
        ```java
        %s
        ```
        
        【类上下文】
        ```java
        %s
        ```
        
        【文件上下文】
        ```java
        %s
        ```
        
        【项目上下文】
        %s
        
        请分析这段代码的业务逻辑问题并提供优化建议。
        """;
    
    /**
     * 构建完整的 Prompt
     */
    public String buildPrompt(CodeSelection selection, String userInstruction) {
        // 1. 收集上下文
        ContextAnalysisResult context = collectContext(selection);
        
        // 2. 构建系统提示词
        String systemPrompt = buildSystemPrompt(userInstruction);
        
        // 3. 构建用户提示词
        String userPrompt = buildUserPrompt(context, userInstruction);
        
        // 4. 组合完整 Prompt
        return combinePrompts(systemPrompt, userPrompt);
    }
    
    /**
     * 收集上下文
     */
    private ContextAnalysisResult collectContext(CodeSelection selection) {
        ContextAnalyzer analyzer = new ContextAnalyzer();
        return analyzer.analyzeContext(selection);
    }
    
    /**
     * 构建系统提示词
     */
    private String buildSystemPrompt(String userInstruction) {
        // 根据用户指令调整系统提示词
        if (userInstruction.contains("优化") || userInstruction.contains("optimize")) {
            return SYSTEM_PROMPT_TEMPLATE + "\n\n重点关注性能优化和代码质量改进。";
        } else if (userInstruction.contains("错误") || userInstruction.contains("bug")) {
            return SYSTEM_PROMPT_TEMPLATE + "\n\n重点关注潜在的错误和异常情况。";
        } else if (userInstruction.contains("重构") || userInstruction.contains("refactor")) {
            return SYSTEM_PROMPT_TEMPLATE + "\n\n重点关注代码结构和设计模式改进。";
        }
        
        return SYSTEM_PROMPT_TEMPLATE;
    }
    
    /**
     * 构建用户提示词
     */
    private String buildUserPrompt(ContextAnalysisResult context, String userInstruction) {
        // 1. 格式化选中代码
        String selectedCode = formatSelectedCode(context.getSelectedContext());
        
        // 2. 格式化方法上下文
        String methodContext = formatMethodContext(context.getMethodContext());
        
        // 3. 格式化类上下文
        String classContext = formatClassContext(context.getClassContext());
        
        // 4. 格式化文件上下文
        String fileContext = formatFileContext(context.getFileContext());
        
        // 5. 格式化项目上下文
        String projectContext = formatProjectContext(context.getProjectContext());
        
        // 6. 构建用户提示词
        return String.format(USER_PROMPT_TEMPLATE, 
            selectedCode, methodContext, classContext, fileContext, projectContext);
    }
    
    /**
     * 格式化选中代码
     */
    private String formatSelectedCode(SelectedCodeContext context) {
        StringBuilder sb = new StringBuilder();
        
        // 添加方法签名
        sb.append("public void processData(List<String> dataList) {\n");
        
        // 添加选中的代码行
        for (String line : context.getCodeLines()) {
            sb.append("    ").append(line).append("\n");
        }
        
        sb.append("}");
        
        return sb.toString();
    }
    
    /**
     * 格式化方法上下文
     */
    private String formatMethodContext(MethodContext context) {
        StringBuilder sb = new StringBuilder();
        
        if (context.getMethod() != null) {
            // 添加方法签名
            sb.append(context.getMethod().getSignature()).append(" {\n");
            
            // 添加方法体（截断到合理长度）
            List<String> body = context.getBody();
            int maxLines = Math.min(body.size(), 20); // 限制行数
            
            for (int i = 0; i < maxLines; i++) {
                sb.append("    ").append(body.get(i)).append("\n");
            }
            
            if (body.size() > maxLines) {
                sb.append("    // ... 其他代码\n");
            }
            
            sb.append("}");
        }
        
        return sb.toString();
    }
    
    /**
     * 格式化类上下文
     */
    private String formatClassContext(ClassContext context) {
        StringBuilder sb = new StringBuilder();
        
        if (context.getClassInfo() != null) {
            ClassInfo clazz = context.getClassInfo();
            
            // 添加类声明
            sb.append("public class ").append(clazz.getName()).append(" {\n");
            
            // 添加相关字段
            for (FieldInfo field : context.getFields()) {
                sb.append("    private ").append(field.getType().getName())
                  .append(" ").append(field.getName()).append(";\n");
            }
            
            // 添加构造函数
            sb.append("\n    public ").append(clazz.getName()).append("(String name) {\n");
            sb.append("        this.name = name;\n");
            sb.append("        this.version = 1;\n");
            sb.append("        this.config = new HashMap<>();\n");
            sb.append("    }\n");
            
            // 添加相关方法
            for (MethodInfo method : context.getRelatedMethods()) {
                if (method.getName().equals("getConfig") || method.getName().equals("getVersion")) {
                    sb.append("\n    public ").append(method.getReturnType().getName())
                      .append(" ").append(method.getName()).append("() {\n");
                    sb.append("        return ").append(method.getName().substring(3).toLowerCase()).append(";\n");
                    sb.append("    }\n");
                }
            }
            
            sb.append("}");
        }
        
        return sb.toString();
    }
    
    /**
     * 格式化文件上下文
     */
    private String formatFileContext(FileContext context) {
        StringBuilder sb = new StringBuilder();
        
        if (context.getFile() != null) {
            FileInfo file = context.getFile();
            
            // 添加包声明
            if (file.getPackageName() != null) {
                sb.append("package ").append(file.getPackageName()).append(";\n\n");
            }
            
            // 添加导入语句
            for (ImportInfo importInfo : context.getImports()) {
                sb.append("import ").append(importInfo.getImportPath()).append(";\n");
            }
            
            sb.append("\n/**\n");
            sb.append(" * 演示 Inline Chat 上下文组织的示例类\n");
            sb.append(" */\n");
            sb.append("public class ").append(file.getName().replace(".java", "")).append(" {\n");
            sb.append("    // ... 类内容\n");
            sb.append("}");
        }
        
        return sb.toString();
    }
    
    /**
     * 格式化项目上下文
     */
    private String formatProjectContext(ProjectContext context) {
        StringBuilder sb = new StringBuilder();
        
        if (context.getProject() != null) {
            ProjectInfo project = context.getProject();
            
            sb.append("- 项目类型：").append(project.getLanguage()).append(" ").append(project.getBuildSystem()).append(" 项目\n");
            sb.append("- 主要依赖：Java 8+, Maven 3.6+\n");
            sb.append("- 项目结构：包含 benchmark 数据和 shenyu 网关项目\n");
            
            // 添加相关依赖
            if (!context.getDependencies().isEmpty()) {
                sb.append("- 主要依赖：\n");
                for (DependencyInfo dep : context.getDependencies()) {
                    sb.append("  - ").append(dep.getGroupId()).append(":").append(dep.getArtifactId())
                      .append(":").append(dep.getVersion()).append("\n");
                }
            }
        }
        
        return sb.toString();
    }
    
    /**
     * 组合完整 Prompt
     */
    private String combinePrompts(String systemPrompt, String userPrompt) {
        StringBuilder sb = new StringBuilder();
        
        // 添加系统提示词
        sb.append("<system>\n");
        sb.append(systemPrompt);
        sb.append("\n</system>\n\n");
        
        // 添加用户提示词
        sb.append("<user>\n");
        sb.append(userPrompt);
        sb.append("\n</user>");
        
        return sb.toString();
    }
    
    /**
     * 计算 Token 使用情况
     */
    public TokenUsage calculateTokenUsage(String prompt) {
        // 简化的 Token 计算
        int systemTokens = countTokens(prompt.substring(0, prompt.indexOf("</system>")));
        int userTokens = countTokens(prompt.substring(prompt.indexOf("<user>"), prompt.indexOf("</user>")));
        int totalTokens = systemTokens + userTokens;
        
        return new TokenUsage(systemTokens, userTokens, totalTokens);
    }
    
    /**
     * 简化的 Token 计算
     */
    private int countTokens(String text) {
        // 实际实现中会使用更精确的 Token 计算算法
        return text.length() / 4; // 粗略估算
    }
    
    /**
     * Token 使用情况
     */
    public static class TokenUsage {
        private int systemTokens;
        private int userTokens;
        private int totalTokens;
        
        public TokenUsage(int systemTokens, int userTokens, int totalTokens) {
            this.systemTokens = systemTokens;
            this.userTokens = userTokens;
            this.totalTokens = totalTokens;
        }
        
        public int getSystemTokens() { return systemTokens; }
        public int getUserTokens() { return userTokens; }
        public int getTotalTokens() { return totalTokens; }
    }
}
