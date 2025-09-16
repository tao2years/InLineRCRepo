package com.cursor.context;

import java.util.*;

/**
 * Inline Chat 上下文分析的数据结构定义
 */
public class ContextDataStructures {
    
    /**
     * 代码选择信息
     */
    public static class CodeSelection {
        private String filePath;
        private int startLine;
        private int endLine;
        private List<String> selectedLines;
        private String selectedText;
        private MethodInfo containingMethod;
        private ClassInfo containingClass;
        private FileInfo file;
        private ProjectInfo project;
        
        // 构造函数和getter/setter
        public CodeSelection(String filePath, int startLine, int endLine) {
            this.filePath = filePath;
            this.startLine = startLine;
            this.endLine = endLine;
        }
        
        public String getFilePath() { return filePath; }
        public int getStartLine() { return startLine; }
        public int getEndLine() { return endLine; }
        public List<String> getSelectedLines() { return selectedLines; }
        public String getSelectedText() { return selectedText; }
        public MethodInfo getContainingMethod() { return containingMethod; }
        public ClassInfo getContainingClass() { return containingClass; }
        public FileInfo getFile() { return file; }
        public ProjectInfo getProject() { return project; }
    }
    
    /**
     * 方法信息
     */
    public static class MethodInfo {
        private String name;
        private String signature;
        private List<Parameter> parameters;
        private TypeInfo returnType;
        private List<String> body;
        private Set<String> localVariables;
        private Set<MethodCall> methodCalls;
        private Set<String> fieldAccess;
        private int complexity;
        private List<String> annotations;
        
        // 构造函数和getter/setter
        public MethodInfo(String name, String signature) {
            this.name = name;
            this.signature = signature;
            this.parameters = new ArrayList<>();
            this.body = new ArrayList<>();
            this.localVariables = new HashSet<>();
            this.methodCalls = new HashSet<>();
            this.fieldAccess = new HashSet<>();
            this.annotations = new ArrayList<>();
        }
        
        public String getName() { return name; }
        public String getSignature() { return signature; }
        public List<Parameter> getParameters() { return parameters; }
        public TypeInfo getReturnType() { return returnType; }
        public List<String> getBody() { return body; }
        public Set<String> getLocalVariables() { return localVariables; }
        public Set<MethodCall> getMethodCalls() { return methodCalls; }
        public Set<String> getFieldAccess() { return fieldAccess; }
        public int getComplexity() { return complexity; }
        public List<String> getAnnotations() { return annotations; }
    }
    
    /**
     * 类信息
     */
    public static class ClassInfo {
        private String name;
        private String packageName;
        private List<FieldInfo> fields;
        private List<MethodInfo> methods;
        private List<String> imports;
        private List<String> annotations;
        private String superClass;
        private List<String> interfaces;
        private AccessModifier accessModifier;
        
        // 构造函数和getter/setter
        public ClassInfo(String name, String packageName) {
            this.name = name;
            this.packageName = packageName;
            this.fields = new ArrayList<>();
            this.methods = new ArrayList<>();
            this.imports = new ArrayList<>();
            this.annotations = new ArrayList<>();
            this.interfaces = new ArrayList<>();
        }
        
        public String getName() { return name; }
        public String getPackageName() { return packageName; }
        public List<FieldInfo> getFields() { return fields; }
        public List<MethodInfo> getMethods() { return methods; }
        public List<String> getImports() { return imports; }
        public List<String> getAnnotations() { return annotations; }
        public String getSuperClass() { return superClass; }
        public List<String> getInterfaces() { return interfaces; }
        public AccessModifier getAccessModifier() { return accessModifier; }
    }
    
    /**
     * 文件信息
     */
    public static class FileInfo {
        private String path;
        private String name;
        private String packageName;
        private List<ImportInfo> imports;
        private List<ClassInfo> classes;
        private List<String> content;
        private long size;
        private long lastModified;
        
        // 构造函数和getter/setter
        public FileInfo(String path, String name) {
            this.path = path;
            this.name = name;
            this.imports = new ArrayList<>();
            this.classes = new ArrayList<>();
            this.content = new ArrayList<>();
        }
        
        public String getPath() { return path; }
        public String getName() { return name; }
        public String getPackageName() { return packageName; }
        public List<ImportInfo> getImports() { return imports; }
        public List<ClassInfo> getClasses() { return classes; }
        public List<String> getContent() { return content; }
        public long getSize() { return size; }
        public long getLastModified() { return lastModified; }
    }
    
    /**
     * 项目信息
     */
    public static class ProjectInfo {
        private String name;
        private String rootPath;
        private List<FileInfo> files;
        private List<DependencyInfo> dependencies;
        private List<ConfigFile> configFiles;
        private BuildSystem buildSystem;
        private String language;
        private String version;
        
        // 构造函数和getter/setter
        public ProjectInfo(String name, String rootPath) {
            this.name = name;
            this.rootPath = rootPath;
            this.files = new ArrayList<>();
            this.dependencies = new ArrayList<>();
            this.configFiles = new ArrayList<>();
        }
        
        public String getName() { return name; }
        public String getRootPath() { return rootPath; }
        public List<FileInfo> getFiles() { return files; }
        public List<DependencyInfo> getDependencies() { return dependencies; }
        public List<ConfigFile> getConfigFiles() { return configFiles; }
        public BuildSystem getBuildSystem() { return buildSystem; }
        public String getLanguage() { return language; }
        public String getVersion() { return version; }
    }
    
    /**
     * 上下文分析结果
     */
    public static class ContextAnalysisResult {
        private SelectedCodeContext selectedContext;
        private MethodContext methodContext;
        private ClassContext classContext;
        private FileContext fileContext;
        private ProjectContext projectContext;
        private int totalTokens;
        private boolean exceedsLimit;
        private Map<String, Double> relevanceScores;
        
        // 构造函数和getter/setter
        public ContextAnalysisResult() {
            this.relevanceScores = new HashMap<>();
        }
        
        public SelectedCodeContext getSelectedContext() { return selectedContext; }
        public void setSelectedContext(SelectedCodeContext selectedContext) { this.selectedContext = selectedContext; }
        public MethodContext getMethodContext() { return methodContext; }
        public void setMethodContext(MethodContext methodContext) { this.methodContext = methodContext; }
        public ClassContext getClassContext() { return classContext; }
        public void setClassContext(ClassContext classContext) { this.classContext = classContext; }
        public FileContext getFileContext() { return fileContext; }
        public void setFileContext(FileContext fileContext) { this.fileContext = fileContext; }
        public ProjectContext getProjectContext() { return projectContext; }
        public void setProjectContext(ProjectContext projectContext) { this.projectContext = projectContext; }
        public int getTotalTokens() { return totalTokens; }
        public void setTotalTokens(int totalTokens) { this.totalTokens = totalTokens; }
        public boolean isExceedsLimit() { return exceedsLimit; }
        public void setExceedsLimit(boolean exceedsLimit) { this.exceedsLimit = exceedsLimit; }
        public Map<String, Double> getRelevanceScores() { return relevanceScores; }
    }
    
    /**
     * 选中代码上下文
     */
    public static class SelectedCodeContext {
        private List<String> codeLines;
        private CodeStructure structure;
        private Set<String> variables;
        private Set<String> methodCalls;
        private int complexity;
        private String pattern;
        
        // 构造函数和getter/setter
        public SelectedCodeContext() {
            this.codeLines = new ArrayList<>();
            this.variables = new HashSet<>();
            this.methodCalls = new HashSet<>();
        }
        
        public List<String> getCodeLines() { return codeLines; }
        public void setCodeLines(List<String> codeLines) { this.codeLines = codeLines; }
        public CodeStructure getStructure() { return structure; }
        public void setStructure(CodeStructure structure) { this.structure = structure; }
        public Set<String> getVariables() { return variables; }
        public void setVariables(Set<String> variables) { this.variables = variables; }
        public Set<String> getMethodCalls() { return methodCalls; }
        public void setMethodCalls(Set<String> methodCalls) { this.methodCalls = methodCalls; }
        public int getComplexity() { return complexity; }
        public void setComplexity(int complexity) { this.complexity = complexity; }
        public String getPattern() { return pattern; }
        public void setPattern(String pattern) { this.pattern = pattern; }
    }
    
    /**
     * 方法上下文
     */
    public static class MethodContext {
        private MethodInfo method;
        private MethodSignature signature;
        private List<Parameter> parameters;
        private TypeInfo returnType;
        private List<String> body;
        private Set<String> localVariables;
        private Set<MethodCall> methodCalls;
        private ControlFlow controlFlow;
        
        // 构造函数和getter/setter
        public MethodContext() {
            this.parameters = new ArrayList<>();
            this.body = new ArrayList<>();
            this.localVariables = new HashSet<>();
            this.methodCalls = new HashSet<>();
        }
        
        public MethodInfo getMethod() { return method; }
        public void setMethod(MethodInfo method) { this.method = method; }
        public MethodSignature getSignature() { return signature; }
        public void setSignature(MethodSignature signature) { this.signature = signature; }
        public List<Parameter> getParameters() { return parameters; }
        public void setParameters(List<Parameter> parameters) { this.parameters = parameters; }
        public TypeInfo getReturnType() { return returnType; }
        public void setReturnType(TypeInfo returnType) { this.returnType = returnType; }
        public List<String> getBody() { return body; }
        public void setBody(List<String> body) { this.body = body; }
        public Set<String> getLocalVariables() { return localVariables; }
        public void setLocalVariables(Set<String> localVariables) { this.localVariables = localVariables; }
        public Set<MethodCall> getMethodCalls() { return methodCalls; }
        public void setMethodCalls(Set<MethodCall> methodCalls) { this.methodCalls = methodCalls; }
        public ControlFlow getControlFlow() { return controlFlow; }
        public void setControlFlow(ControlFlow controlFlow) { this.controlFlow = controlFlow; }
    }
    
    /**
     * 类上下文
     */
    public static class ClassContext {
        private ClassInfo classInfo;
        private List<FieldInfo> fields;
        private List<MethodInfo> methods;
        private Set<MethodInfo> relatedMethods;
        private InheritanceInfo inheritance;
        private List<InterfaceInfo> interfaces;
        
        // 构造函数和getter/setter
        public ClassContext() {
            this.fields = new ArrayList<>();
            this.methods = new ArrayList<>();
            this.relatedMethods = new HashSet<>();
            this.interfaces = new ArrayList<>();
        }
        
        public ClassInfo getClassInfo() { return classInfo; }
        public void setClassInfo(ClassInfo classInfo) { this.classInfo = classInfo; }
        public List<FieldInfo> getFields() { return fields; }
        public void setFields(List<FieldInfo> fields) { this.fields = fields; }
        public List<MethodInfo> getMethods() { return methods; }
        public void setMethods(List<MethodInfo> methods) { this.methods = methods; }
        public Set<MethodInfo> getRelatedMethods() { return relatedMethods; }
        public void setRelatedMethods(Set<MethodInfo> relatedMethods) { this.relatedMethods = relatedMethods; }
        public InheritanceInfo getInheritance() { return inheritance; }
        public void setInheritance(InheritanceInfo inheritance) { this.inheritance = inheritance; }
        public List<InterfaceInfo> getInterfaces() { return interfaces; }
        public void setInterfaces(List<InterfaceInfo> interfaces) { this.interfaces = interfaces; }
    }
    
    /**
     * 文件上下文
     */
    public static class FileContext {
        private FileInfo file;
        private List<ImportInfo> imports;
        private String packageName;
        private FileStructure structure;
        private Set<ClassInfo> relatedClasses;
        
        // 构造函数和getter/setter
        public FileContext() {
            this.imports = new ArrayList<>();
            this.relatedClasses = new HashSet<>();
        }
        
        public FileInfo getFile() { return file; }
        public void setFile(FileInfo file) { this.file = file; }
        public List<ImportInfo> getImports() { return imports; }
        public void setImports(List<ImportInfo> imports) { this.imports = imports; }
        public String getPackageName() { return packageName; }
        public void setPackageName(String packageName) { this.packageName = packageName; }
        public FileStructure getStructure() { return structure; }
        public void setStructure(FileStructure structure) { this.structure = structure; }
        public Set<ClassInfo> getRelatedClasses() { return relatedClasses; }
        public void setRelatedClasses(Set<ClassInfo> relatedClasses) { this.relatedClasses = relatedClasses; }
    }
    
    /**
     * 项目上下文
     */
    public static class ProjectContext {
        private ProjectInfo project;
        private List<DependencyInfo> dependencies;
        private Set<FileInfo> relatedFiles;
        private List<ConfigFile> configFiles;
        
        // 构造函数和getter/setter
        public ProjectContext() {
            this.dependencies = new ArrayList<>();
            this.relatedFiles = new HashSet<>();
            this.configFiles = new ArrayList<>();
        }
        
        public ProjectInfo getProject() { return project; }
        public void setProject(ProjectInfo project) { this.project = project; }
        public List<DependencyInfo> getDependencies() { return dependencies; }
        public void setDependencies(List<DependencyInfo> dependencies) { this.dependencies = dependencies; }
        public Set<FileInfo> getRelatedFiles() { return relatedFiles; }
        public void setRelatedFiles(Set<FileInfo> relatedFiles) { this.relatedFiles = relatedFiles; }
        public List<ConfigFile> getConfigFiles() { return configFiles; }
        public void setConfigFiles(List<ConfigFile> configFiles) { this.configFiles = configFiles; }
    }
    
    // 辅助类定义
    public static class Parameter {
        private String name;
        private TypeInfo type;
        private String defaultValue;
        
        public Parameter(String name, TypeInfo type) {
            this.name = name;
            this.type = type;
        }
        
        public String getName() { return name; }
        public TypeInfo getType() { return type; }
        public String getDefaultValue() { return defaultValue; }
    }
    
    public static class TypeInfo {
        private String name;
        private boolean isPrimitive;
        private boolean isArray;
        private List<TypeInfo> genericTypes;
        
        public TypeInfo(String name) {
            this.name = name;
            this.genericTypes = new ArrayList<>();
        }
        
        public String getName() { return name; }
        public boolean isPrimitive() { return isPrimitive; }
        public boolean isArray() { return isArray; }
        public List<TypeInfo> getGenericTypes() { return genericTypes; }
    }
    
    public static class MethodCall {
        private String methodName;
        private String className;
        private List<TypeInfo> parameterTypes;
        private boolean isStatic;
        
        public MethodCall(String methodName) {
            this.methodName = methodName;
            this.parameterTypes = new ArrayList<>();
        }
        
        public String getMethodName() { return methodName; }
        public String getClassName() { return className; }
        public List<TypeInfo> getParameterTypes() { return parameterTypes; }
        public boolean isStatic() { return isStatic; }
    }
    
    public static class FieldInfo {
        private String name;
        private TypeInfo type;
        private AccessModifier accessModifier;
        private boolean isStatic;
        private boolean isFinal;
        
        public FieldInfo(String name, TypeInfo type) {
            this.name = name;
            this.type = type;
        }
        
        public String getName() { return name; }
        public TypeInfo getType() { return type; }
        public AccessModifier getAccessModifier() { return accessModifier; }
        public boolean isStatic() { return isStatic; }
        public boolean isFinal() { return isFinal; }
    }
    
    public static class ImportInfo {
        private String importPath;
        private boolean isStatic;
        private String alias;
        
        public ImportInfo(String importPath) {
            this.importPath = importPath;
        }
        
        public String getImportPath() { return importPath; }
        public boolean isStatic() { return isStatic; }
        public String getAlias() { return alias; }
    }
    
    public static class DependencyInfo {
        private String groupId;
        private String artifactId;
        private String version;
        private String scope;
        
        public DependencyInfo(String groupId, String artifactId, String version) {
            this.groupId = groupId;
            this.artifactId = artifactId;
            this.version = version;
        }
        
        public String getGroupId() { return groupId; }
        public String getArtifactId() { return artifactId; }
        public String getVersion() { return version; }
        public String getScope() { return scope; }
    }
    
    public static class ConfigFile {
        private String path;
        private String type;
        private Map<String, Object> properties;
        
        public ConfigFile(String path, String type) {
            this.path = path;
            this.type = type;
            this.properties = new HashMap<>();
        }
        
        public String getPath() { return path; }
        public String getType() { return type; }
        public Map<String, Object> getProperties() { return properties; }
    }
    
    // 枚举定义
    public enum AccessModifier {
        PUBLIC, PROTECTED, PACKAGE_PRIVATE, PRIVATE
    }
    
    public enum BuildSystem {
        MAVEN, GRADLE, SBT, NPM, YARN, PIP
    }
    
    // 其他辅助类
    public static class CodeStructure { }
    public static class MethodSignature { }
    public static class ControlFlow { }
    public static class InheritanceInfo { }
    public static class InterfaceInfo { }
    public static class FileStructure { }
    public static class CodePattern { }
    public static class SemanticFeatures { }
}
