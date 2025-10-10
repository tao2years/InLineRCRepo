# 智能代码补全/编辑SFT数据构造技术方案

## 1. 方案概述

### 1.1 目标
基于代码审查数据构造高质量的SFT（Supervised Fine-Tuning）训练数据，用于训练智能代码补全/编辑模型，使模型能够：
- 根据代码上下文和编辑历史预测下一步编辑
- 理解代码审查意见并生成相应的代码修改
- 支持多种编程语言的智能补全和重构

### 1.2 数据来源
- **原始数据**：Git diff格式的代码审查数据
- **核心字段**：old_file, new_file, review_message, review_line等
- **数据特点**：包含真实的代码修改历史和专家审查意见

### 1.3 目标格式
遵循Zeta项目的数据格式标准：
```json
{
    "events": "编辑历史描述",
    "input": "带光标和可编辑区域标记的输入代码",
    "output": "期望的输出代码",
    "labels": "编辑位置,编辑意图"
}
```

## 2. 核心技术架构

### 2.1 数据处理流水线

```
原始审查数据 → 预处理 → 光标推断 → 区域确定 → 历史构造 → 标签分类 → SFT数据
```

### 2.2 关键组件

#### 2.2.1 光标位置推断器（CursorInferrer）
**功能**：基于review_line和代码差异推断用户光标位置
**输入**：review_line, code_with_line, diff信息
**输出**：精确的光标行号和列号

#### 2.2.2 可编辑区域确定器（EditableRegionDeterminer）
**功能**：确定合理的可编辑区域边界
**策略**：基于代码结构、修改范围和语言特性
**输出**：区域起始和结束位置

#### 2.2.3 编辑历史构造器（EventsConstructor）
**功能**：将git diff转换为标准化的编辑历史描述
**格式**：统一的diff格式，包含文件路径和具体修改

#### 2.2.4 标签分类器（LabelClassifier）
**功能**：自动分类编辑类型和意图
**输出**：两级标签系统（位置+意图）

## 3. 详细实施方案

### 3.1 数据预处理

#### 3.1.1 数据清洗
```python
def preprocess_raw_data(raw_record):
    """
    数据预处理步骤：
    1. 验证必需字段完整性
    2. 标准化文件路径格式
    3. 清理代码中的特殊字符
    4. 验证代码语法有效性
    """
    # 字段完整性检查
    required_fields = ['old_file', 'new_file', 'review_line', 'code_type']
    for field in required_fields:
        if not raw_record.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # 代码格式标准化
    old_file = normalize_code_format(raw_record['old_file'])
    new_file = normalize_code_format(raw_record['new_file'])
    
    return cleaned_record
```

#### 3.1.2 语言特定处理
```python
LANGUAGE_CONFIGS = {
    'java': {
        'method_keywords': ['public', 'private', 'protected', 'static'],
        'class_keywords': ['class', 'interface', 'enum'],
        'import_pattern': r'^import\s+[\w.]+;',
        'annotation_pattern': r'^@\w+',
        'block_delimiters': ('{', '}')
    },
    'python': {
        'method_keywords': ['def', 'async def'],
        'class_keywords': ['class'],
        'import_pattern': r'^(import|from)\s+',
        'decorator_pattern': r'^@\w+',
        'block_delimiters': (':', None)
    }
}
```

### 3.2 光标位置推断算法

#### 3.2.1 基础推断策略
```python
def infer_cursor_position(record):
    """
    光标位置推断的核心算法：
    
    1. 基于review_line定位关注行
    2. 分析代码差异类型
    3. 根据修改模式确定精确位置
    """
    
    # 步骤1：解析带行号的代码上下文
    line_mapping = parse_code_with_line(record.code_with_line)
    target_line = record.review_line
    
    # 步骤2：分析修改类型
    diff_analysis = analyze_code_diff(record.old_file, record.new_file)
    
    # 步骤3：确定光标位置
    if diff_analysis.type == 'deletion':
        # 删除场景：光标在被删除内容的起始位置
        cursor_pos = find_deletion_start_position(target_line, diff_analysis)
    elif diff_analysis.type == 'insertion':
        # 插入场景：光标在插入点
        cursor_pos = find_insertion_position(target_line, diff_analysis)
    elif diff_analysis.type == 'modification':
        # 修改场景：光标在修改点
        cursor_pos = find_modification_position(target_line, diff_analysis)
    else:
        # 复合场景：基于主要修改类型
        cursor_pos = find_primary_change_position(target_line, diff_analysis)
    
    return cursor_pos
```

#### 3.2.2 具体案例分析

**案例：方法逻辑简化**
```java
// 原始代码（review_line = 37）
@Override
public void updateUserNickName() {
    if (this.nickName == null) {  // ← review_line指向这里
        return;
    }
    String nickNameByRegion = parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion());
    this.setNickName(nickNameByRegion);
}

// 目标代码
@Override
public void updateUserNickName() {
    this.setNickName(parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion()));
}
```

**推断逻辑**：
1. review_line=37指向`if (this.nickName == null) {`
2. 这是删除操作的起始行
3. 光标应该放在第37行的行首（缩进后）
4. **结果**：`<|user_cursor_is_here|>`标记放在if语句开头

### 3.3 可编辑区域确定策略

#### 3.3.1 区域大小策略
```python
def determine_editable_region(record, cursor_line):
    """
    可编辑区域确定的分层策略：
    
    1. 分析代码结构层次
    2. 评估修改影响范围
    3. 确定合适的区域边界
    """
    
    # 代码结构分析
    structure = analyze_code_structure(record.old_file, record.code_type)
    
    # 修改范围评估
    change_scope = evaluate_change_scope(record.old_file, record.new_file)
    
    # 区域大小决策
    if change_scope.level == 'expression':
        # 表达式级：最小区域（±2行）
        region_size = 'minimal'
        padding = 2
    elif change_scope.level == 'statement':
        # 语句级：中等区域（±5行）
        region_size = 'statement'
        padding = 5
    elif change_scope.level == 'method':
        # 方法级：较大区域（整个方法）
        region_size = 'method'
        padding = find_method_boundaries(structure, cursor_line)
    else:
        # 类级：最大区域
        region_size = 'class'
        padding = find_class_boundaries(structure, cursor_line)
    
    start_line = max(1, cursor_line - padding)
    end_line = cursor_line + padding
    
    return start_line, end_line
```

#### 3.3.2 边界优化规则
```python
def optimize_region_boundaries(start_line, end_line, code_structure):
    """
    边界优化规则：
    1. 尊重代码块边界
    2. 包含完整的语句
    3. 避免截断注释
    4. 保持语法完整性
    """
    
    # 规则1：对齐到代码块边界
    if code_structure.has_block_at(start_line):
        start_line = code_structure.get_block_start(start_line)
    
    if code_structure.has_block_at(end_line):
        end_line = code_structure.get_block_end(end_line)
    
    # 规则2：包含完整语句
    start_line = align_to_statement_start(start_line, code_structure)
    end_line = align_to_statement_end(end_line, code_structure)
    
    # 规则3：处理注释
    if code_structure.has_comment_block(start_line, end_line):
        start_line, end_line = include_complete_comments(start_line, end_line, code_structure)
    
    return start_line, end_line
```

### 3.4 编辑历史构造

#### 3.4.1 Events字段生成
```python
def construct_edit_events(record):
    """
    编辑历史构造的标准化流程：
    
    1. 解析git diff信息
    2. 生成统一格式的编辑描述
    3. 包含必要的上下文信息
    """
    
    # 解析diff操作
    diff_operations = parse_unified_diff(record.old_hunk, record.new_hunk)
    
    events = []
    for operation in diff_operations:
        # 构造标准事件描述
        event = f'User edited "{record.file_path}":\n\n```diff\n'
        
        # 添加diff头部信息
        event += f'@@ -{operation.old_start},{operation.old_count} '
        event += f'+{operation.new_start},{operation.new_count} @@\n'
        
        # 添加具体修改内容
        for line in operation.context_lines:
            event += f' {line}\n'
        
        for line in operation.deleted_lines:
            event += f'-{line}\n'
        
        for line in operation.added_lines:
            event += f'+{line}\n'
        
        event += '```'
        events.append(event)
    
    return '\n\n'.join(events)
```

#### 3.4.2 复杂修改处理
```python
def handle_complex_modifications(old_file, new_file):
    """
    处理复杂修改场景：
    1. 多处修改的合并
    2. 跨文件的关联修改
    3. 重构操作的描述
    """
    
    # 识别修改类型
    modifications = identify_modifications(old_file, new_file)
    
    complex_events = []
    for mod in modifications:
        if mod.type == 'method_refactor':
            event = describe_method_refactor(mod)
        elif mod.type == 'import_reorganization':
            event = describe_import_changes(mod)
        elif mod.type == 'annotation_modification':
            event = describe_annotation_changes(mod)
        else:
            event = describe_generic_modification(mod)
        
        complex_events.append(event)
    
    return complex_events
```

### 3.5 标签分类系统

#### 3.5.1 编辑位置分类
```python
def classify_edit_location(record, cursor_line):
    """
    编辑位置分类算法：
    
    no-op: 无实际修改
    local-edit: 光标附近的修改（±3行）
    non-local-edit: 远离光标的修改
    """
    
    # 检查是否有实际修改
    if record.old_file.strip() == record.new_file.strip():
        return 'no-op'
    
    # 找出所有修改位置
    modifications = find_all_modifications(record.old_file, record.new_file)
    
    # 计算修改与光标的距离
    local_modifications = []
    non_local_modifications = []
    
    for mod in modifications:
        distance = abs(mod.line_number - cursor_line)
        if distance <= 3:
            local_modifications.append(mod)
        else:
            non_local_modifications.append(mod)
    
    # 分类决策
    if len(non_local_modifications) > 0:
        return 'non-local-edit'
    elif len(local_modifications) > 0:
        return 'local-edit'
    else:
        return 'no-op'
```

#### 3.5.2 编辑意图分类
```python
def classify_edit_intent(record):
    """
    编辑意图分类算法：
    
    基于代码变化模式识别编辑意图
    """
    
    change_patterns = analyze_change_patterns(record.old_file, record.new_file)
    
    # 导入语句修改
    if change_patterns.has_import_changes():
        return 'add-imports'
    
    # 方法实现补全
    if change_patterns.has_method_implementation():
        return 'complete-implementation'
    
    # 重复模式补全
    if change_patterns.has_repetitive_pattern():
        return 'complete-pattern'
    
    # 基于命名的意图推断
    if change_patterns.has_naming_based_changes():
        return 'infer-intent'
    
    # 代码重构
    if change_patterns.has_refactoring_signs():
        return 'infer-refactor'
    
    return 'unknown'
```

### 3.6 质量控制机制

#### 3.6.1 数据验证
```python
def validate_sft_data(sft_record):
    """
    SFT数据质量验证：
    
    1. 格式完整性检查
    2. 标记正确性验证
    3. 语义一致性检查
    4. 标签合理性验证
    """
    
    errors = []
    
    # 格式检查
    required_fields = ['events', 'input', 'output', 'labels']
    for field in required_fields:
        if not getattr(sft_record, field, None):
            errors.append(f'Missing field: {field}')
    
    # 标记检查
    input_content = sft_record.input
    cursor_count = input_content.count('<|user_cursor_is_here|>')
    if cursor_count != 1:
        errors.append(f'Invalid cursor marker count: {cursor_count}')
    
    region_start_count = input_content.count('<|editable_region_start|>')
    region_end_count = input_content.count('<|editable_region_end|>')
    if region_start_count != 1 or region_end_count != 1:
        errors.append('Invalid editable region markers')
    
    # 语义检查
    if not validate_semantic_consistency(sft_record):
        errors.append('Semantic inconsistency detected')
    
    # 标签检查
    if not validate_label_format(sft_record.labels):
        errors.append('Invalid label format')
    
    return errors
```

#### 3.6.2 质量评分
```python
def assess_data_quality(sft_record):
    """
    数据质量评分算法：
    
    总分100分，包含4个维度：
    - 代码完整性（25分）
    - 编辑合理性（30分）
    - 上下文相关性（25分）
    - 标签准确性（20分）
    """
    
    score = 0
    
    # 代码完整性（25分）
    if is_syntactically_valid(sft_record.input) and is_syntactically_valid(sft_record.output):
        score += 25
    
    # 编辑合理性（30分）
    edit_reasonableness = evaluate_edit_reasonableness(sft_record.input, sft_record.output)
    score += int(edit_reasonableness * 30)
    
    # 上下文相关性（25分）
    context_relevance = evaluate_context_relevance(sft_record.events, sft_record.input)
    score += int(context_relevance * 25)
    
    # 标签准确性（20分）
    label_accuracy = evaluate_label_accuracy(sft_record)
    score += int(label_accuracy * 20)
    
    return score
```

## 4. 实际案例演示

### 4.1 案例输入
```json
{
    "file_path": "service/src/main/.../SimpleUser.java",
    "old_file": "...(包含if null检查的完整代码)...",
    "new_file": "...(简化后的代码)...",
    "review_line": 37,
    "review_message": "【功能性问题】为空是否也需要更新？不需要建议使用StringUtils.isBlank"
}
```

### 4.2 处理过程

#### 4.2.1 光标位置推断
- **输入**：review_line=37，指向`if (this.nickName == null) {`
- **分析**：这是删除操作的起始行
- **结果**：光标位置在第37行行首

#### 4.2.2 可编辑区域确定
- **分析**：方法内部逻辑修改，涉及6行代码
- **策略**：statement级别区域
- **结果**：第37-43行作为可编辑区域

#### 4.2.3 编辑历史构造
```
User edited "service/src/main/.../SimpleUser.java":

```diff
@@ -34,12 +34,6 @@ public class SimpleUser extends AbstractUserExtrasProcessor {
 
     @Override
     public void updateUserNickName() {
-        if (this.nickName == null) {
-            return;
-        }
-        String nickNameByRegion = parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion());
-
-        // 昵称为null或者空字符串也设置, 因为用户可能在当前region没设置过昵称
-        this.setNickName(nickNameByRegion);
+        this.setNickName(parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion()));
     }
 }
```

#### 4.2.4 标签分类
- **位置标签**：local-edit（修改在光标附近）
- **意图标签**：infer-refactor（代码重构简化）
- **最终标签**：`local-edit,infer-refactor`

### 4.3 最终输出
```json
{
    "events": "User edited \"service/src/main/.../SimpleUser.java\":\n\n```diff\n@@ -34,12 +34,6 @@ public class SimpleUser extends AbstractUserExtrasProcessor {\n \n     @Override\n     public void updateUserNickName() {\n-        if (this.nickName == null) {\n-            return;\n-        }\n-        String nickNameByRegion = parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion());\n-\n-        // 昵称为null或者空字符串也设置, 因为用户可能在当前region没设置过昵称\n-        this.setNickName(nickNameByRegion);\n+        this.setNickName(parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion()));\n     }\n }\n```",
    "input": "    @Override\n    public void updateUserNickName() {\n<|editable_region_start|>\n        if (this.nickName == null) {<|user_cursor_is_here|>\n            return;\n        }\n        String nickNameByRegion = parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion());\n\n        // 昵称为null或者空字符串也设置, 因为用户可能在当前region没设置过昵称\n        this.setNickName(nickNameByRegion);\n<|editable_region_end|>\n    }",
    "output": "    @Override\n    public void updateUserNickName() {\n<|editable_region_start|>\n        this.setNickName(parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion()));\n<|editable_region_end|>\n    }",
    "labels": "local-edit,infer-refactor"
}
```

## 5. 批量处理流程

### 5.1 数据处理管道
```python
class SFTDataConstructor:
    def __init__(self, config):
        self.cursor_inferrer = CursorInferrer(config)
        self.region_determiner = EditableRegionDeterminer(config)
        self.events_constructor = EventsConstructor(config)
        self.label_classifier = LabelClassifier(config)
        self.quality_controller = QualityController(config)
    
    def process_batch(self, raw_records):
        """批量处理原始数据"""
        sft_records = []
        failed_records = []
        
        for raw_record in raw_records:
            try:
                # 数据预处理
                cleaned_record = self.preprocess(raw_record)
                
                # 核心处理步骤
                sft_record = self.convert_to_sft_format(cleaned_record)
                
                # 质量验证
                validation_errors = self.quality_controller.validate(sft_record)
                if validation_errors:
                    failed_records.append({
                        'record': raw_record,
                        'errors': validation_errors
                    })
                    continue
                
                # 质量评分
                quality_score = self.quality_controller.assess_quality(sft_record)
                if quality_score >= self.config.quality_threshold:
                    sft_records.append(sft_record)
                else:
                    failed_records.append({
                        'record': raw_record,
                        'reason': f'Low quality score: {quality_score}'
                    })
                    
            except Exception as e:
                failed_records.append({
                    'record': raw_record,
                    'error': str(e)
                })
        
        return sft_records, failed_records
```

### 5.2 配置管理
```yaml
# SFT数据构造配置
sft_construction:
  # 质量控制
  quality_threshold: 75  # 最低质量分数
  
  # 光标推断
  cursor_inference:
    strategy: "heuristic"  # 推断策略
    max_search_range: 10   # 最大搜索范围
  
  # 区域确定
  editable_region:
    sizing_strategy: "adaptive"  # 自适应大小
    min_size: 3                  # 最小区域大小
    max_size: 50                 # 最大区域大小
  
  # 标签分类
  label_classification:
    local_edit_threshold: 3      # local-edit距离阈值
    implementation_min_lines: 5  # 实现补全最小行数
  
  # 输出格式
  output_format:
    preserve_indentation: true   # 保持缩进
    normalize_whitespace: true   # 标准化空白字符
```

### 5.3 使用示例
```bash
# 基本使用
python construct_sft_data.py \
    --input raw_review_data.jsonl \
    --output sft_train_data.jsonl \
    --config sft_config.yaml

# 批量处理
python construct_sft_data.py \
    --input_dir ./raw_data/ \
    --output_dir ./sft_data/ \
    --batch_size 1000 \
    --parallel_workers 4

# 质量分析
python analyze_sft_quality.py \
    --data sft_train_data.jsonl \
    --report quality_report.html
```

## 6. 质量保证与优化

### 6.1 数据质量监控
- **实时监控**：处理过程中的质量指标跟踪
- **质量报告**：详细的数据质量分析报告
- **异常检测**：自动识别异常数据模式
- **人工审核**：关键样本的人工质量检查

### 6.2 持续优化策略
- **反馈循环**：基于模型训练效果优化数据构造
- **规则更新**：根据新的代码模式更新处理规则
- **质量提升**：持续改进数据质量评估标准
- **扩展支持**：逐步支持更多编程语言和场景

### 6.3 性能优化
- **并行处理**：多进程并行处理大规模数据
- **内存优化**：流式处理避免内存溢出
- **缓存机制**：缓存中间结果提高处理效率
- **增量处理**：支持增量数据更新

## 7. 总结

本技术方案提供了从代码审查数据到SFT训练数据的完整转换解决方案，具有以下特点：

1. **准确性**：基于多维度分析的精确光标位置推断和区域确定
2. **完整性**：涵盖从数据预处理到质量控制的全流程
3. **可扩展性**：支持多种编程语言和自定义处理规则
4. **高质量**：多层次的质量控制确保训练数据质量
5. **实用性**：提供完整的工具链和配置系统

该方案为智能代码补全/编辑模型的训练提供了坚实的数据基础，支持高质量的SFT训练和持续优化。

## 8. 实施工具链

### 8.1 核心实现文件

#### 8.1.1 主处理器（sft_data_constructor.py）
```python
#!/usr/bin/env python3
"""
SFT数据构造主处理器
实现从原始审查数据到SFT训练数据的完整转换
"""

class SFTDataConstructor:
    """SFT数据构造器主类"""

    def __init__(self, config_path="sft_config.yaml"):
        self.config = self.load_config(config_path)
        self.initialize_components()

    def process_single_record(self, raw_record):
        """处理单条记录"""
        # 1. 数据预处理
        cleaned_record = self.preprocess_record(raw_record)

        # 2. 光标位置推断
        cursor_line, cursor_col = self.cursor_inferrer.infer_position(cleaned_record)

        # 3. 可编辑区域确定
        start_line, end_line = self.region_determiner.determine_region(
            cleaned_record, cursor_line
        )

        # 4. 编辑历史构造
        events = self.events_constructor.construct_events(cleaned_record)

        # 5. 输入输出构造
        input_code = self.construct_input_with_markers(
            cleaned_record.old_file, cursor_line, cursor_col, start_line, end_line
        )
        output_code = self.construct_output_with_markers(
            cleaned_record.new_file, start_line, end_line
        )

        # 6. 标签分类
        location_label = self.label_classifier.classify_location(
            cleaned_record, cursor_line
        )
        intent_label = self.label_classifier.classify_intent(cleaned_record)
        labels = f"{location_label},{intent_label}"

        # 7. 构造SFT记录
        sft_record = SFTRecord(
            events=events,
            input=input_code,
            output=output_code,
            labels=labels
        )

        return sft_record

    def batch_process(self, input_file, output_file):
        """批量处理数据"""
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:

            for line_num, line in enumerate(f_in, 1):
                try:
                    raw_record = json.loads(line.strip())
                    sft_record = self.process_single_record(raw_record)

                    # 质量验证
                    if self.quality_controller.validate_and_score(sft_record):
                        f_out.write(json.dumps(sft_record.to_dict(), ensure_ascii=False) + '\n')

                except Exception as e:
                    print(f"Error processing line {line_num}: {e}")
                    continue
```

#### 8.1.2 配置文件（sft_config.yaml）
```yaml
# SFT数据构造配置文件

# 基础设置
basic:
  quality_threshold: 75
  batch_size: 1000
  max_workers: 4

# 光标位置推断配置
cursor_inference:
  strategy: "heuristic"  # heuristic, ml_based, hybrid
  max_search_range: 10
  confidence_threshold: 0.8

  # 语言特定配置
  language_configs:
    java:
      method_patterns: ["public", "private", "protected"]
      class_patterns: ["class", "interface", "enum"]
      import_pattern: "^import\\s+[\\w.]+;"
    python:
      method_patterns: ["def", "async def"]
      class_patterns: ["class"]
      import_pattern: "^(import|from)\\s+"

# 可编辑区域配置
editable_region:
  sizing_strategy: "adaptive"  # minimal, adaptive, generous
  min_region_size: 3
  max_region_size: 50

  # 区域大小映射
  size_mapping:
    expression: 3
    statement: 7
    method: 15
    class: 30

# 标签分类配置
label_classification:
  # 位置分类阈值
  local_edit_max_distance: 3

  # 意图分类规则
  intent_rules:
    import_keywords: ["import", "from", "include"]
    implementation_min_lines: 5
    pattern_similarity_threshold: 0.7
    refactor_indicators: ["simplify", "optimize", "refactor"]

# 质量控制配置
quality_control:
  # 验证规则
  validation_rules:
    check_syntax: true
    check_markers: true
    check_consistency: true
    check_labels: true

  # 评分权重
  scoring_weights:
    code_completeness: 0.25
    edit_reasonableness: 0.30
    context_relevance: 0.25
    label_accuracy: 0.20

# 输出格式配置
output_format:
  preserve_indentation: true
  normalize_whitespace: true
  include_file_markers: false
  max_line_length: 120
```

#### 8.1.3 命令行工具（construct_sft_data.py）
```python
#!/usr/bin/env python3
"""
SFT数据构造命令行工具
"""

import argparse
import logging
from pathlib import Path
from sft_data_constructor import SFTDataConstructor

def setup_logging(level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description='构造SFT训练数据')
    parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    parser.add_argument('--config', '-c', default='sft_config.yaml', help='配置文件路径')
    parser.add_argument('--log-level', default='INFO', help='日志级别')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式')

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # 初始化构造器
        constructor = SFTDataConstructor(args.config)

        # 处理数据
        if args.dry_run:
            logger.info("试运行模式，不会生成输出文件")
            constructor.dry_run(args.input)
        else:
            logger.info(f"开始处理数据：{args.input} -> {args.output}")
            constructor.batch_process(args.input, args.output)
            logger.info("数据处理完成")

    except Exception as e:
        logger.error(f"处理失败: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
```

### 8.2 使用示例

#### 8.2.1 基本使用
```bash
# 处理单个文件
python construct_sft_data.py \
    --input raw_review_data.jsonl \
    --output sft_training_data.jsonl \
    --config sft_config.yaml

# 试运行检查
python construct_sft_data.py \
    --input raw_review_data.jsonl \
    --output /dev/null \
    --dry-run
```

#### 8.2.2 批量处理
```bash
# 处理目录中的所有文件
for file in raw_data/*.jsonl; do
    output_file="sft_data/$(basename "$file" .jsonl)_sft.jsonl"
    python construct_sft_data.py --input "$file" --output "$output_file"
done

# 并行处理
find raw_data/ -name "*.jsonl" | \
xargs -I {} -P 4 python construct_sft_data.py \
    --input {} --output sft_data/{}_sft.jsonl
```

#### 8.2.3 质量分析
```bash
# 生成质量报告
python analyze_sft_quality.py \
    --data sft_training_data.jsonl \
    --output quality_report.html \
    --include-samples 100

# 统计信息
python sft_statistics.py \
    --data sft_training_data.jsonl \
    --output stats.json
```

### 8.3 输出文件格式

#### 8.3.1 SFT训练数据格式
```jsonl
{"events": "User edited \"SimpleUser.java\":\n\n```diff\n@@ -34,12 +34,6 @@\n-        if (this.nickName == null) {\n-            return;\n-        }\n+        this.setNickName(parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion()));\n```", "input": "    @Override\n    public void updateUserNickName() {\n<|editable_region_start|>\n        if (this.nickName == null) {<|user_cursor_is_here|>\n            return;\n        }\n        String nickNameByRegion = parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion());\n        this.setNickName(nickNameByRegion);\n<|editable_region_end|>\n    }", "output": "    @Override\n    public void updateUserNickName() {\n<|editable_region_start|>\n        this.setNickName(parseNickNameByRegion(this.nickName, RequestContext.getCurrentRegion()));\n<|editable_region_end|>\n    }", "labels": "local-edit,infer-refactor"}
```

#### 8.3.2 质量报告格式
```json
{
    "summary": {
        "total_records": 1000,
        "valid_records": 850,
        "invalid_records": 150,
        "average_quality_score": 82.5
    },
    "quality_distribution": {
        "excellent": 320,
        "good": 380,
        "fair": 150,
        "poor": 150
    },
    "label_distribution": {
        "local-edit": 600,
        "non-local-edit": 200,
        "no-op": 50,
        "add-imports": 100,
        "complete-implementation": 200,
        "infer-refactor": 300,
        "unknown": 250
    },
    "common_issues": [
        "Invalid cursor marker placement",
        "Inconsistent editable region boundaries",
        "Incorrect label classification"
    ]
}
```

### 8.4 扩展和定制

#### 8.4.1 自定义处理器
```python
class CustomJavaProcessor(BaseProcessor):
    """Java语言特定的处理器"""

    def process_annotation_changes(self, old_code, new_code):
        """处理注解变化"""
        old_annotations = self.extract_annotations(old_code)
        new_annotations = self.extract_annotations(new_code)

        changes = self.compare_annotations(old_annotations, new_annotations)
        return self.generate_annotation_events(changes)

    def infer_cursor_for_annotation_change(self, record):
        """针对注解变化的光标推断"""
        annotation_changes = self.find_annotation_changes(record)
        if annotation_changes:
            return annotation_changes[0].line_number
        return super().infer_cursor_position(record)
```

#### 8.4.2 插件系统
```python
class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins = {}

    def register_plugin(self, name, plugin_class):
        """注册插件"""
        self.plugins[name] = plugin_class

    def apply_plugins(self, record, stage):
        """应用插件"""
        for plugin_name, plugin_class in self.plugins.items():
            if plugin_class.supports_stage(stage):
                record = plugin_class.process(record)
        return record
```

## 9. 部署和运维

### 9.1 生产环境部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  sft-constructor:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - CONFIG_PATH=/app/config/sft_config.yaml
      - LOG_LEVEL=INFO
    command: python construct_sft_data.py --input /app/data/input --output /app/data/output
```

### 9.2 监控和告警
```python
class ProcessingMonitor:
    """处理过程监控"""

    def __init__(self):
        self.metrics = {
            'processed_count': 0,
            'success_count': 0,
            'error_count': 0,
            'average_quality_score': 0.0
        }

    def update_metrics(self, result):
        """更新监控指标"""
        self.metrics['processed_count'] += 1
        if result.success:
            self.metrics['success_count'] += 1
            self.update_quality_score(result.quality_score)
        else:
            self.metrics['error_count'] += 1

    def check_alerts(self):
        """检查告警条件"""
        error_rate = self.metrics['error_count'] / self.metrics['processed_count']
        if error_rate > 0.1:  # 错误率超过10%
            self.send_alert(f"High error rate: {error_rate:.2%}")

        if self.metrics['average_quality_score'] < 70:  # 平均质量分数低于70
            self.send_alert(f"Low quality score: {self.metrics['average_quality_score']}")
```

### 9.3 性能优化
```python
class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.cache = {}
        self.batch_size = 1000

    def optimize_processing(self, records):
        """优化处理性能"""
        # 1. 批量处理
        batches = self.create_batches(records, self.batch_size)

        # 2. 并行处理
        with ProcessPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self.process_batch, batches))

        # 3. 结果合并
        return self.merge_results(results)

    def cache_intermediate_results(self, key, value):
        """缓存中间结果"""
        self.cache[key] = value

    def get_cached_result(self, key):
        """获取缓存结果"""
        return self.cache.get(key)
```

这套完整的技术方案提供了从原始代码审查数据到高质量SFT训练数据的端到端解决方案，包含了详细的实施指南、工具链和最佳实践，可以直接用于生产环境的智能代码补全/编辑模型训练数据构造。
