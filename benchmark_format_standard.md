# InLineRC Benchmark格式标准文档

## 📋 概述

本文档定义了InLineRC Benchmark的标准格式，确保所有benchmark数据的一致性和质量。

## 🎯 核心格式要求

### 1. JSONL文件结构

每个benchmark条目必须包含以下6个字段：

```json
{
  "prompt": "...",
  "domain": "nl2code_java",
  "id": "...", 
  "good_example_response": "...",
  "reward_command": "...",
  "extra_content": {
      "query": "...",
      "diff_path": "...",
      "test_result": "...",
      "file_path": "...",
      "start_line": "...",
      "end_line": "...",
      "work_dir": "..."
  }
}
```

### 2. 代码行号标注

**所有代码段必须包含行号标注**，格式为：`行号:`

```java
  1: @Service("tResMsService")
  2: public class TResMsServiceImpl implements TResMsService {
  3:     private static final Logger LOGGER = LogManager.getLogger(TResMsServiceImpl.class);
```

### 3. Context Above/Below间隔

- **Context Above**: 结束于某行（如第80行）
- **目标实现区域**: 预留行号间隔（如第81-84行）
- **Context Below**: 从下一行开始（如第85行）

```java
 80:     }
```

```java
 85:     @Override
 86:     public int update(ResMsRequestBody requestBody) throws VscServiceException {
```

## 🔧 Recent Changes格式标准

### 标准格式模板

```markdown
### Recent Change 3 (Earliest preparation work)
```diff
@@ -13,1 +13,0 @@
+ 13:     private String keyPrefix = "APITestExecuteDaemonService::dynamic-global-variable::";
```

### Recent Change 2 (Intermediate preparation)
```diff
@@ -19,8 +19,4 @@
  19:     public void put(String taskId, String key, String value) {
+ 20:         BoundHashOperations<String, String, String> boundHashOperations = redisTemplate.boundHashOps(prefix(taskId));
+ 21:         if (boundHashOperations.get(key) == null && boundHashOperations.size() >= amountLimitPerTask) {
+ 22:             throwLimitExceedException(amountLimitPerTask);
+ 23:         }
+ 24:         boundHashOperations.put(key, value);
+ 25:         boundHashOperations.expire(Duration.ofSeconds(ttlSeconds));
- 20:         redisTemplate.opsForHash().put(prefix(taskId), key, value);
- 21:         // TODO: consider TTL; will migrate to bound ops later
  26:     }
```

### Recent Change 1 (Most recent preparation)
```diff
@@ -45,2 +45,2 @@
- 45:         logger.debug("Processing task: {}", taskId);
+ 45:         LOGGER.info("[begin processTask][taskId={}]", taskId);
  46:     }
```
```

### 关键要求

1. **@@行格式**: `@@ -起始行,变更行数 +起始行,变更行数 @@`
2. **行号标注**: 所有+/-行必须包含行号，格式为`+ 行号: 代码内容`
3. **描述统一**: 使用英文描述（Earliest/Intermediate/Most recent preparation work）
4. **逻辑顺序**: RC3→RC2→RC1，从早到晚的开发演进

## ❌ 常见错误格式

### 错误示例1：缺少行号

```diff
@@ -2,5 +2,5 @@
  public class TResMsServiceImpl implements TResMsService {
-    // TODO add logger
+    private static final Logger LOGGER = LogManager.getLogger(TResMsServiceImpl.class);
```

### 错误示例2：缺少@@头

```diff
**文件**: TResMsServiceImpl.java
**修改位置**: 第2-6行
-    // TODO add logger
+    private static final Logger LOGGER = LogManager.getLogger(TResMsServiceImpl.class);
```

## ✅ 正确格式示例

```diff
@@ -2,5 +2,5 @@
  2: public class TResMsServiceImpl implements TResMsService {
-  3:     // TODO add logger
+  3:     private static final Logger LOGGER = LogManager.getLogger(TResMsServiceImpl.class);
  4: 
-  5:     // TODO table name
+  5:     private static final String TABLE_NAME = "t_res_micro_service";
  6: 
```

## 🔍 质量检查清单

### 代码格式检查
- [ ] 所有代码段都有行号标注
- [ ] Context above/below有正确的行号间隔
- [ ] 行号格式一致（`行号:`）

### Recent Changes检查
- [ ] 包含正确的@@头信息
- [ ] +/-行都有行号标注
- [ ] 描述使用英文标准格式
- [ ] 逻辑顺序正确（RC3→RC2→RC1）

### 内容质量检查
- [ ] Recent Changes形成完整的开发演进链
- [ ] 技术修改合理且准确
- [ ] Diff格式符合unified diff标准

## 🛠️ 修复工具

### 自动修复脚本
```bash
python fix_recent_changes_format.py
```

### 格式验证脚本
```bash
python scripts/validate_separated_benchmark.py
```

## 📊 标准统计

一个完整的benchmark文件应该包含：
- **条目数量**: 明确的数据条数
- **格式一致性**: 100%符合标准格式
- **行号完整性**: 所有代码段都有行号
- **Recent Changes质量**: 逻辑连贯的开发演进

## 🎯 最佳实践

1. **始终使用标准模板**：基于`nl2code_java_all_20_with_rc_separated_final.jsonl`
2. **严格行号管理**：确保所有代码都有正确的行号标注
3. **Recent Changes逻辑性**：确保RC3→RC2→RC1形成合理的开发演进
4. **格式验证**：使用自动化工具验证格式正确性
5. **质量审视**：人工检查每个Recent Change的技术合理性

---

**版本**: v1.0  
**更新时间**: 2025-01-19  
**维护者**: InLineRC Benchmark Team
