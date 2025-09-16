package com.cursor.context;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 相关方法查找器
 * 
 * 演示如何自动判断和查找相关方法
 */
public class RelatedMethodFinder {
    
    // 相关度阈值
    private static final double CALL_RELATION_THRESHOLD = 0.8;
    private static final double VARIABLE_SHARING_THRESHOLD = 0.6;
    private static final double PATTERN_SIMILARITY_THRESHOLD = 0.7;
    private static final double SEMANTIC_SIMILARITY_THRESHOLD = 0.5;
    
    /**
     * 查找相关方法
     */
    public List<MethodInfo> findRelatedMethods(CodeSelection selection, ClassInfo clazz) {
        List<MethodInfo> relatedMethods = new ArrayList<>();
        
        // 1. 基于调用关系的相关方法
        List<MethodInfo> callRelated = findCallRelatedMethods(selection, clazz);
        relatedMethods.addAll(callRelated);
        
        // 2. 基于变量共享的相关方法
        List<MethodInfo> variableRelated = findVariableRelatedMethods(selection, clazz);
        relatedMethods.addAll(variableRelated);
        
        // 3. 基于代码模式的相关方法
        List<MethodInfo> patternRelated = findPatternRelatedMethods(selection, clazz);
        relatedMethods.addAll(patternRelated);
        
        // 4. 基于语义相似度的相关方法
        List<MethodInfo> semanticRelated = findSemanticRelatedMethods(selection, clazz);
        relatedMethods.addAll(semanticRelated);
        
        // 5. 去重并排序
        return deduplicateAndSort(relatedMethods, selection);
    }
    
    /**
     * 基于调用关系查找相关方法
     */
    private List<MethodInfo> findCallRelatedMethods(CodeSelection selection, ClassInfo clazz) {
        List<MethodInfo> relatedMethods = new ArrayList<>();
        
        // 获取选中代码中调用的方法
        Set<String> calledMethods = extractMethodCalls(selection.getSelectedLines());
        
        for (MethodInfo method : clazz.getMethods()) {
            // 1. 直接调用关系
            if (calledMethods.contains(method.getName())) {
                relatedMethods.add(method);
                continue;
            }
            
            // 2. 间接调用关系（通过其他方法调用）
            if (hasIndirectCallRelation(method, calledMethods)) {
                relatedMethods.add(method);
                continue;
            }
            
            // 3. 调用选中代码中的方法
            if (callsSelectedMethods(method, selection)) {
                relatedMethods.add(method);
            }
        }
        
        return relatedMethods;
    }
    
    /**
     * 基于变量共享查找相关方法
     */
    private List<MethodInfo> findVariableRelatedMethods(CodeSelection selection, ClassInfo clazz) {
        List<MethodInfo> relatedMethods = new ArrayList<>();
        
        // 获取选中代码中使用的变量
        Set<String> usedVariables = extractVariables(selection.getSelectedLines());
        
        for (MethodInfo method : clazz.getMethods()) {
            // 1. 共享类字段
            Set<String> methodFields = extractFieldAccess(method.getBody());
            if (hasIntersection(usedVariables, methodFields)) {
                relatedMethods.add(method);
                continue;
            }
            
            // 2. 共享局部变量模式
            Set<String> methodVariables = extractLocalVariables(method.getBody());
            if (hasIntersection(usedVariables, methodVariables)) {
                relatedMethods.add(method);
                continue;
            }
            
            // 3. 参数传递关系
            if (hasParameterRelation(method, usedVariables)) {
                relatedMethods.add(method);
            }
        }
        
        return relatedMethods;
    }
    
    /**
     * 基于代码模式查找相关方法
     */
    private List<MethodInfo> findPatternRelatedMethods(CodeSelection selection, ClassInfo clazz) {
        List<MethodInfo> relatedMethods = new ArrayList<>();
        
        // 提取选中代码的模式
        CodePattern selectedPattern = extractCodePattern(selection.getSelectedLines());
        
        for (MethodInfo method : clazz.getMethods()) {
            // 1. 结构模式相似性
            CodePattern methodPattern = extractCodePattern(method.getBody());
            double structuralSimilarity = calculateStructuralSimilarity(selectedPattern, methodPattern);
            if (structuralSimilarity > PATTERN_SIMILARITY_THRESHOLD) {
                relatedMethods.add(method);
                continue;
            }
            
            // 2. 控制流模式相似性
            double controlFlowSimilarity = calculateControlFlowSimilarity(selectedPattern, methodPattern);
            if (controlFlowSimilarity > PATTERN_SIMILARITY_THRESHOLD) {
                relatedMethods.add(method);
                continue;
            }
            
            // 3. 异常处理模式相似性
            double exceptionSimilarity = calculateExceptionSimilarity(selectedPattern, methodPattern);
            if (exceptionSimilarity > PATTERN_SIMILARITY_THRESHOLD) {
                relatedMethods.add(method);
            }
        }
        
        return relatedMethods;
    }
    
    /**
     * 基于语义相似度查找相关方法
     */
    private List<MethodInfo> findSemanticRelatedMethods(CodeSelection selection, ClassInfo clazz) {
        List<MethodInfo> relatedMethods = new ArrayList<>();
        
        // 提取选中代码的语义特征
        SemanticFeatures selectedFeatures = extractSemanticFeatures(selection.getSelectedLines());
        
        for (MethodInfo method : clazz.getMethods()) {
            // 1. 功能相似性
            SemanticFeatures methodFeatures = extractSemanticFeatures(method.getBody());
            double functionalSimilarity = calculateFunctionalSimilarity(selectedFeatures, methodFeatures);
            if (functionalSimilarity > SEMANTIC_SIMILARITY_THRESHOLD) {
                relatedMethods.add(method);
                continue;
            }
            
            // 2. 领域概念相似性
            double domainSimilarity = calculateDomainSimilarity(selectedFeatures, methodFeatures);
            if (domainSimilarity > SEMANTIC_SIMILARITY_THRESHOLD) {
                relatedMethods.add(method);
                continue;
            }
            
            // 3. 算法模式相似性
            double algorithmSimilarity = calculateAlgorithmSimilarity(selectedFeatures, methodFeatures);
            if (algorithmSimilarity > SEMANTIC_SIMILARITY_THRESHOLD) {
                relatedMethods.add(method);
            }
        }
        
        return relatedMethods;
    }
    
    /**
     * 计算结构相似性
     */
    private double calculateStructuralSimilarity(CodePattern pattern1, CodePattern pattern2) {
        // 1. 语句类型分布相似性
        double statementSimilarity = calculateStatementTypeSimilarity(pattern1, pattern2);
        
        // 2. 嵌套层次相似性
        double nestingSimilarity = calculateNestingSimilarity(pattern1, pattern2);
        
        // 3. 代码块结构相似性
        double blockSimilarity = calculateBlockSimilarity(pattern1, pattern2);
        
        // 加权平均
        return (statementSimilarity * 0.4 + nestingSimilarity * 0.3 + blockSimilarity * 0.3);
    }
    
    /**
     * 计算控制流相似性
     */
    private double calculateControlFlowSimilarity(CodePattern pattern1, CodePattern pattern2) {
        // 1. 条件语句相似性
        double conditionSimilarity = calculateConditionSimilarity(pattern1, pattern2);
        
        // 2. 循环结构相似性
        double loopSimilarity = calculateLoopSimilarity(pattern1, pattern2);
        
        // 3. 分支结构相似性
        double branchSimilarity = calculateBranchSimilarity(pattern1, pattern2);
        
        // 加权平均
        return (conditionSimilarity * 0.4 + loopSimilarity * 0.3 + branchSimilarity * 0.3);
    }
    
    /**
     * 计算功能相似性
     */
    private double calculateFunctionalSimilarity(SemanticFeatures features1, SemanticFeatures features2) {
        // 1. 操作类型相似性
        double operationSimilarity = calculateOperationSimilarity(features1, features2);
        
        // 2. 数据操作相似性
        double dataOperationSimilarity = calculateDataOperationSimilarity(features1, features2);
        
        // 3. 业务逻辑相似性
        double businessLogicSimilarity = calculateBusinessLogicSimilarity(features1, features2);
        
        // 加权平均
        return (operationSimilarity * 0.4 + dataOperationSimilarity * 0.3 + businessLogicSimilarity * 0.3);
    }
    
    /**
     * 去重并排序
     */
    private List<MethodInfo> deduplicateAndSort(List<MethodInfo> methods, CodeSelection selection) {
        // 去重
        Set<MethodInfo> uniqueMethods = new LinkedHashSet<>(methods);
        
        // 按相关度排序
        return uniqueMethods.stream()
                .sorted((m1, m2) -> Double.compare(
                    calculateOverallRelevance(m2, selection),
                    calculateOverallRelevance(m1, selection)
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 计算整体相关度
     */
    private double calculateOverallRelevance(MethodInfo method, CodeSelection selection) {
        double relevance = 0.0;
        
        // 1. 调用关系相关度
        if (hasDirectCallRelation(method, selection)) {
            relevance += 0.4;
        }
        
        // 2. 变量共享相关度
        if (hasVariableSharing(method, selection)) {
            relevance += 0.3;
        }
        
        // 3. 模式相似性相关度
        double patternSimilarity = calculatePatternSimilarity(method, selection);
        relevance += patternSimilarity * 0.2;
        
        // 4. 语义相似性相关度
        double semanticSimilarity = calculateSemanticSimilarity(method, selection);
        relevance += semanticSimilarity * 0.1;
        
        return relevance;
    }
    
    // 辅助方法的简化实现
    private Set<String> extractMethodCalls(List<String> lines) { return new HashSet<>(); }
    private Set<String> extractVariables(List<String> lines) { return new HashSet<>(); }
    private Set<String> extractFieldAccess(List<String> body) { return new HashSet<>(); }
    private Set<String> extractLocalVariables(List<String> body) { return new HashSet<>(); }
    private boolean hasIntersection(Set<String> set1, Set<String> set2) { return false; }
    private boolean hasIndirectCallRelation(MethodInfo method, Set<String> calledMethods) { return false; }
    private boolean callsSelectedMethods(MethodInfo method, CodeSelection selection) { return false; }
    private boolean hasParameterRelation(MethodInfo method, Set<String> variables) { return false; }
    private CodePattern extractCodePattern(List<String> lines) { return new CodePattern(); }
    private double calculateControlFlowSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateExceptionSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private SemanticFeatures extractSemanticFeatures(List<String> lines) { return new SemanticFeatures(); }
    private double calculateDomainSimilarity(SemanticFeatures features1, SemanticFeatures features2) { return 0.0; }
    private double calculateAlgorithmSimilarity(SemanticFeatures features1, SemanticFeatures features2) { return 0.0; }
    private double calculateStatementTypeSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateNestingSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateBlockSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateConditionSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateLoopSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateBranchSimilarity(CodePattern pattern1, CodePattern pattern2) { return 0.0; }
    private double calculateOperationSimilarity(SemanticFeatures features1, SemanticFeatures features2) { return 0.0; }
    private double calculateDataOperationSimilarity(SemanticFeatures features1, SemanticFeatures features2) { return 0.0; }
    private double calculateBusinessLogicSimilarity(SemanticFeatures features1, SemanticFeatures features2) { return 0.0; }
    private boolean hasDirectCallRelation(MethodInfo method, CodeSelection selection) { return false; }
    private boolean hasVariableSharing(MethodInfo method, CodeSelection selection) { return false; }
    private double calculatePatternSimilarity(MethodInfo method, CodeSelection selection) { return 0.0; }
    private double calculateSemanticSimilarity(MethodInfo method, CodeSelection selection) { return 0.0; }
}
