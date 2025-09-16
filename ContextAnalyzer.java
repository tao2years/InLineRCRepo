package com.cursor.context;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Inline Chat 上下文分析器
 * 
 * 演示如何自动分析和提取代码上下文
 */
public class ContextAnalyzer {
    
    // 上下文类型枚举
    public enum ContextType {
        SELECTED_CODE,      // 选中代码
        METHOD_CONTEXT,     // 方法上下文
        CLASS_CONTEXT,      // 类上下文
        FILE_CONTEXT,       // 文件上下文
        PROJECT_CONTEXT     // 项目上下文
    }
    
    // 上下文权重配置
    private static final Map<ContextType, Double> CONTEXT_WEIGHTS = Map.of(
        ContextType.SELECTED_CODE, 1.0,    // 最高优先级
        ContextType.METHOD_CONTEXT, 0.8,   // 高优先级
        ContextType.CLASS_CONTEXT, 0.6,    // 中等优先级
        ContextType.FILE_CONTEXT, 0.4,     // 低优先级
        ContextType.PROJECT_CONTEXT, 0.2   // 最低优先级
    );
    
    // Token 限制配置
    private static final int MAX_TOKENS = 32000;
    private static final Map<ContextType, Integer> TOKEN_LIMITS = Map.of(
        ContextType.SELECTED_CODE, 8000,   // 25%
        ContextType.METHOD_CONTEXT, 6000,  // 18.75%
        ContextType.CLASS_CONTEXT, 4000,   // 12.5%
        ContextType.FILE_CONTEXT, 3000,    // 9.375%
        ContextType.PROJECT_CONTEXT, 2000  // 6.25%
    );
    
    /**
     * 分析代码上下文
     */
    public ContextAnalysisResult analyzeContext(CodeSelection selection) {
        ContextAnalysisResult result = new ContextAnalysisResult();
        
        // 1. 分析选中代码
        SelectedCodeContext selectedContext = analyzeSelectedCode(selection);
        result.setSelectedContext(selectedContext);
        
        // 2. 分析方法上下文
        MethodContext methodContext = analyzeMethodContext(selection);
        result.setMethodContext(methodContext);
        
        // 3. 分析类上下文
        ClassContext classContext = analyzeClassContext(selection);
        result.setClassContext(classContext);
        
        // 4. 分析文件上下文
        FileContext fileContext = analyzeFileContext(selection);
        result.setFileContext(fileContext);
        
        // 5. 分析项目上下文
        ProjectContext projectContext = analyzeProjectContext(selection);
        result.setProjectContext(projectContext);
        
        // 6. 计算 Token 使用情况
        calculateTokenUsage(result);
        
        // 7. 应用截断策略
        applyTruncationStrategy(result);
        
        return result;
    }
    
    /**
     * 分析选中代码上下文
     */
    private SelectedCodeContext analyzeSelectedCode(CodeSelection selection) {
        SelectedCodeContext context = new SelectedCodeContext();
        
        // 获取选中的代码行
        List<String> selectedLines = selection.getSelectedLines();
        context.setCodeLines(selectedLines);
        
        // 分析代码结构
        CodeStructure structure = analyzeCodeStructure(selectedLines);
        context.setStructure(structure);
        
        // 识别变量和函数调用
        Set<String> variables = extractVariables(selectedLines);
        context.setVariables(variables);
        
        Set<String> methodCalls = extractMethodCalls(selectedLines);
        context.setMethodCalls(methodCalls);
        
        // 计算复杂度
        int complexity = calculateComplexity(selectedLines);
        context.setComplexity(complexity);
        
        return context;
    }
    
    /**
     * 分析方法上下文
     */
    private MethodContext analyzeMethodContext(CodeSelection selection) {
        MethodContext context = new MethodContext();
        
        // 获取包含选中代码的方法
        MethodInfo method = selection.getContainingMethod();
        context.setMethod(method);
        
        // 分析方法签名
        MethodSignature signature = analyzeMethodSignature(method);
        context.setSignature(signature);
        
        // 分析参数和返回值
        List<Parameter> parameters = method.getParameters();
        context.setParameters(parameters);
        
        TypeInfo returnType = method.getReturnType();
        context.setReturnType(returnType);
        
        // 分析方法体
        List<String> methodBody = method.getBody();
        context.setBody(methodBody);
        
        // 识别局部变量
        Set<String> localVariables = extractLocalVariables(methodBody);
        context.setLocalVariables(localVariables);
        
        // 识别方法调用
        Set<MethodCall> methodCalls = extractMethodCalls(methodBody);
        context.setMethodCalls(methodCalls);
        
        // 分析控制流
        ControlFlow controlFlow = analyzeControlFlow(methodBody);
        context.setControlFlow(controlFlow);
        
        return context;
    }
    
    /**
     * 分析类上下文
     */
    private ClassContext analyzeClassContext(CodeSelection selection) {
        ClassContext context = new ClassContext();
        
        // 获取包含选中代码的类
        ClassInfo clazz = selection.getContainingClass();
        context.setClassInfo(clazz);
        
        // 分析类字段
        List<FieldInfo> fields = clazz.getFields();
        context.setFields(fields);
        
        // 分析方法
        List<MethodInfo> methods = clazz.getMethods();
        context.setMethods(methods);
        
        // 识别相关方法（基于调用关系）
        Set<MethodInfo> relatedMethods = findRelatedMethods(clazz, selection);
        context.setRelatedMethods(relatedMethods);
        
        // 分析继承关系
        InheritanceInfo inheritance = analyzeInheritance(clazz);
        context.setInheritance(inheritance);
        
        // 分析接口实现
        List<InterfaceInfo> interfaces = clazz.getInterfaces();
        context.setInterfaces(interfaces);
        
        return context;
    }
    
    /**
     * 分析文件上下文
     */
    private FileContext analyzeFileContext(CodeSelection selection) {
        FileContext context = new FileContext();
        
        // 获取文件信息
        FileInfo file = selection.getFile();
        context.setFile(file);
        
        // 分析导入语句
        List<ImportInfo> imports = file.getImports();
        context.setImports(imports);
        
        // 分析包声明
        String packageName = file.getPackage();
        context.setPackage(packageName);
        
        // 分析文件结构
        FileStructure structure = analyzeFileStructure(file);
        context.setStructure(structure);
        
        // 识别相关类
        Set<ClassInfo> relatedClasses = findRelatedClasses(file, selection);
        context.setRelatedClasses(relatedClasses);
        
        return context;
    }
    
    /**
     * 分析项目上下文
     */
    private ProjectContext analyzeProjectContext(CodeSelection selection) {
        ProjectContext context = new ProjectContext();
        
        // 获取项目信息
        ProjectInfo project = selection.getProject();
        context.setProject(project);
        
        // 分析依赖关系
        List<DependencyInfo> dependencies = project.getDependencies();
        context.setDependencies(dependencies);
        
        // 识别相关文件
        Set<FileInfo> relatedFiles = findRelatedFiles(project, selection);
        context.setRelatedFiles(relatedFiles);
        
        // 分析配置文件
        List<ConfigFile> configFiles = project.getConfigFiles();
        context.setConfigFiles(configFiles);
        
        return context;
    }
    
    /**
     * 查找相关方法
     * 
     * 相关方法的判断标准：
     * 1. 直接调用关系
     * 2. 共享变量访问
     * 3. 相似功能模式
     * 4. 继承关系
     */
    private Set<MethodInfo> findRelatedMethods(ClassInfo clazz, CodeSelection selection) {
        Set<MethodInfo> relatedMethods = new HashSet<>();
        
        // 1. 基于调用关系的相关方法
        Set<String> calledMethods = extractMethodCalls(selection.getSelectedLines());
        for (MethodInfo method : clazz.getMethods()) {
            if (calledMethods.contains(method.getName())) {
                relatedMethods.add(method);
            }
        }
        
        // 2. 基于共享变量的相关方法
        Set<String> usedVariables = extractVariables(selection.getSelectedLines());
        for (MethodInfo method : clazz.getMethods()) {
            Set<String> methodVariables = extractLocalVariables(method.getBody());
            if (hasIntersection(usedVariables, methodVariables)) {
                relatedMethods.add(method);
            }
        }
        
        // 3. 基于相似功能模式的相关方法
        String selectedCodePattern = extractCodePattern(selection.getSelectedLines());
        for (MethodInfo method : clazz.getMethods()) {
            String methodPattern = extractCodePattern(method.getBody());
            if (calculateSimilarity(selectedCodePattern, methodPattern) > 0.7) {
                relatedMethods.add(method);
            }
        }
        
        return relatedMethods;
    }
    
    /**
     * 计算 Token 使用情况
     */
    private void calculateTokenUsage(ContextAnalysisResult result) {
        int totalTokens = 0;
        
        // 计算各部分的 Token 使用
        totalTokens += estimateTokens(result.getSelectedContext());
        totalTokens += estimateTokens(result.getMethodContext());
        totalTokens += estimateTokens(result.getClassContext());
        totalTokens += estimateTokens(result.getFileContext());
        totalTokens += estimateTokens(result.getProjectContext());
        
        result.setTotalTokens(totalTokens);
        result.setExceedsLimit(totalTokens > MAX_TOKENS);
    }
    
    /**
     * 应用截断策略
     */
    private void applyTruncationStrategy(ContextAnalysisResult result) {
        if (!result.isExceedsLimit()) {
            return;
        }
        
        // 按优先级截断
        int remainingTokens = MAX_TOKENS;
        
        // 1. 保留选中代码（最高优先级）
        SelectedCodeContext selectedContext = result.getSelectedContext();
        int selectedTokens = estimateTokens(selectedContext);
        remainingTokens -= selectedTokens;
        
        // 2. 截断方法上下文
        MethodContext methodContext = result.getMethodContext();
        int methodTokens = Math.min(estimateTokens(methodContext), 
                                   Math.min(TOKEN_LIMITS.get(ContextType.METHOD_CONTEXT), remainingTokens));
        truncateMethodContext(methodContext, methodTokens);
        remainingTokens -= methodTokens;
        
        // 3. 截断类上下文
        ClassContext classContext = result.getClassContext();
        int classTokens = Math.min(estimateTokens(classContext), 
                                  Math.min(TOKEN_LIMITS.get(ContextType.CLASS_CONTEXT), remainingTokens));
        truncateClassContext(classContext, classTokens);
        remainingTokens -= classTokens;
        
        // 4. 截断文件上下文
        FileContext fileContext = result.getFileContext();
        int fileTokens = Math.min(estimateTokens(fileContext), 
                                 Math.min(TOKEN_LIMITS.get(ContextType.FILE_CONTEXT), remainingTokens));
        truncateFileContext(fileContext, fileTokens);
        remainingTokens -= fileTokens;
        
        // 5. 截断项目上下文
        ProjectContext projectContext = result.getProjectContext();
        int projectTokens = Math.min(estimateTokens(projectContext), 
                                    Math.min(TOKEN_LIMITS.get(ContextType.PROJECT_CONTEXT), remainingTokens));
        truncateProjectContext(projectContext, projectTokens);
    }
    
    // 辅助方法
    private int estimateTokens(Object context) {
        // 简化的 Token 估算算法
        if (context instanceof SelectedCodeContext) {
            return ((SelectedCodeContext) context).getCodeLines().size() * 10;
        } else if (context instanceof MethodContext) {
            return ((MethodContext) context).getBody().size() * 8;
        } else if (context instanceof ClassContext) {
            return ((ClassContext) context).getMethods().size() * 5;
        } else if (context instanceof FileContext) {
            return ((FileContext) context).getImports().size() * 3;
        } else if (context instanceof ProjectContext) {
            return ((ProjectContext) context).getDependencies().size() * 2;
        }
        return 0;
    }
    
    private boolean hasIntersection(Set<String> set1, Set<String> set2) {
        return set1.stream().anyMatch(set2::contains);
    }
    
    private double calculateSimilarity(String pattern1, String pattern2) {
        // 简化的相似度计算算法
        if (pattern1.equals(pattern2)) return 1.0;
        if (pattern1.contains(pattern2) || pattern2.contains(pattern1)) return 0.8;
        return 0.0;
    }
    
    // 其他辅助方法的简化实现
    private CodeStructure analyzeCodeStructure(List<String> lines) { return new CodeStructure(); }
    private Set<String> extractVariables(List<String> lines) { return new HashSet<>(); }
    private Set<String> extractMethodCalls(List<String> lines) { return new HashSet<>(); }
    private int calculateComplexity(List<String> lines) { return 1; }
    private MethodSignature analyzeMethodSignature(MethodInfo method) { return new MethodSignature(); }
    private Set<String> extractLocalVariables(List<String> body) { return new HashSet<>(); }
    private Set<MethodCall> extractMethodCalls(List<String> body) { return new HashSet<>(); }
    private ControlFlow analyzeControlFlow(List<String> body) { return new ControlFlow(); }
    private InheritanceInfo analyzeInheritance(ClassInfo clazz) { return new InheritanceInfo(); }
    private FileStructure analyzeFileStructure(FileInfo file) { return new FileStructure(); }
    private Set<ClassInfo> findRelatedClasses(FileInfo file, CodeSelection selection) { return new HashSet<>(); }
    private Set<FileInfo> findRelatedFiles(ProjectInfo project, CodeSelection selection) { return new HashSet<>(); }
    private String extractCodePattern(List<String> lines) { return ""; }
    private void truncateMethodContext(MethodContext context, int tokens) {}
    private void truncateClassContext(ClassContext context, int tokens) {}
    private void truncateFileContext(FileContext context, int tokens) {}
    private void truncateProjectContext(ProjectContext context, int tokens) {}
}
