#!/usr/bin/env python3
"""
智能代码编辑功能数据处理管道实现
基于Zeta项目的数据格式和处理逻辑
"""

import json
import re
import difflib
import ast
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class GitDiffRecord:
    """原始Git Diff数据结构"""
    mrcr_url: str
    file_path: str
    code_type: str
    old_file: str
    new_file: str
    old_hunk: str
    new_hunk: str
    old_commit_id: str
    new_commit_id: str
    review_line: int
    review_message: str
    severity: str
    category: str
    author: str
    start_line: int
    end_line: int
    code_with_line: str

@dataclass
class ZetaTrainingRecord:
    """Zeta格式训练数据结构"""
    events: str
    input: str
    output: str
    labels: str
    assertions: str = ""

@dataclass
class ReviewAnalysis:
    """Review消息分析结果"""
    type: str
    description: str
    suggestions: List[str]

class CursorPositionInferrer:
    """光标位置推断器"""
    
    def __init__(self):
        self.language_configs = {
            'java': {'method_keywords': ['public', 'private', 'protected'], 'block_start': '{', 'block_end': '}'},
            'python': {'method_keywords': ['def', 'class'], 'block_start': ':', 'block_end': None},
            'javascript': {'method_keywords': ['function', 'class'], 'block_start': '{', 'block_end': '}'},
            'typescript': {'method_keywords': ['function', 'class'], 'block_start': '{', 'block_end': '}'},
        }
    
    def infer_cursor_position(self, git_record: GitDiffRecord) -> Tuple[int, int]:
        """
        推断光标位置（行号，列号）
        """
        # 1. 解析code_with_line获取行号映射
        line_mapping = self._parse_code_with_line(git_record.code_with_line)
        
        # 2. 定位review_line
        target_line_num = git_record.review_line
        target_line_content = line_mapping.get(target_line_num, "")
        
        # 3. 分析差异类型
        diff_type = self._analyze_diff_type(git_record.old_file, git_record.new_file)
        
        # 4. 根据差异类型确定光标位置
        if diff_type == "line_deletion":
            # 删除场景：光标在被删除行的末尾
            col_pos = len(target_line_content.rstrip())
        elif diff_type == "line_modification":
            # 修改场景：光标在修改点
            col_pos = self._find_modification_point(target_line_content, git_record.new_hunk)
        elif diff_type == "line_addition":
            # 添加场景：光标在插入点
            col_pos = self._find_insertion_point(target_line_content)
        else:
            # 默认：行末
            col_pos = len(target_line_content.rstrip())
        
        return target_line_num, col_pos
    
    def _parse_code_with_line(self, code_with_line: str) -> Dict[int, str]:
        """解析带行号的代码"""
        line_mapping = {}
        for line in code_with_line.split('\n'):
            if line.startswith('line '):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    line_num = int(parts[0].replace('line ', ''))
                    line_content = parts[1]
                    line_mapping[line_num] = line_content
        return line_mapping
    
    def _analyze_diff_type(self, old_file: str, new_file: str) -> str:
        """分析差异类型"""
        old_lines = old_file.split('\n')
        new_lines = new_file.split('\n')
        
        if len(old_lines) > len(new_lines):
            return "line_deletion"
        elif len(old_lines) < len(new_lines):
            return "line_addition"
        else:
            return "line_modification"
    
    def _find_modification_point(self, line_content: str, new_hunk: str) -> int:
        """找到修改点的列位置"""
        # 简化实现：返回行中间位置
        return len(line_content) // 2
    
    def _find_insertion_point(self, line_content: str) -> int:
        """找到插入点的列位置"""
        # 简化实现：返回行末位置
        return len(line_content.rstrip())

class EditableRegionDeterminer:
    """可编辑区域确定器"""
    
    def determine_editable_region(self, git_record: GitDiffRecord, cursor_line: int) -> Tuple[int, int]:
        """
        确定可编辑区域的起始和结束行号
        """
        # 1. 分析代码结构
        code_structure = self._analyze_code_structure(git_record.old_file, git_record.code_type)
        
        # 2. 分析修改范围
        diff_scope = self._analyze_diff_scope(git_record.old_hunk, git_record.new_hunk)
        
        # 3. 确定区域边界
        if diff_scope == "method_level":
            start_line, end_line = self._find_method_boundaries(code_structure, cursor_line)
        elif diff_scope == "statement_level":
            start_line, end_line = self._find_statement_boundaries(code_structure, cursor_line)
        else:
            start_line, end_line = self._find_minimal_boundaries(code_structure, cursor_line)
        
        return start_line, end_line
    
    def _analyze_code_structure(self, code: str, code_type: str) -> Dict:
        """分析代码结构"""
        lines = code.split('\n')
        structure = {
            'methods': [],
            'classes': [],
            'blocks': []
        }
        
        # 简化的结构分析
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if code_type == 'java':
                if any(keyword in stripped for keyword in ['public ', 'private ', 'protected ']):
                    if '(' in stripped and ')' in stripped:
                        structure['methods'].append(i)
                elif stripped.startswith('class '):
                    structure['classes'].append(i)
            # 可以扩展其他语言的分析
        
        return structure
    
    def _analyze_diff_scope(self, old_hunk: str, new_hunk: str) -> str:
        """分析修改范围"""
        if not old_hunk or not new_hunk:
            return "minimal"
        
        old_lines = old_hunk.split('\n')
        new_lines = new_hunk.split('\n')
        
        if len(old_lines) > 10 or len(new_lines) > 10:
            return "method_level"
        elif len(old_lines) > 3 or len(new_lines) > 3:
            return "statement_level"
        else:
            return "minimal"
    
    def _find_method_boundaries(self, structure: Dict, cursor_line: int) -> Tuple[int, int]:
        """找到方法边界"""
        # 简化实现：返回较大的区域
        return max(1, cursor_line - 10), cursor_line + 10
    
    def _find_statement_boundaries(self, structure: Dict, cursor_line: int) -> Tuple[int, int]:
        """找到语句边界"""
        return max(1, cursor_line - 5), cursor_line + 5
    
    def _find_minimal_boundaries(self, structure: Dict, cursor_line: int) -> Tuple[int, int]:
        """找到最小边界"""
        return max(1, cursor_line - 2), cursor_line + 2

class EventsConstructor:
    """编辑历史构造器"""
    
    def construct_edit_events(self, git_record: GitDiffRecord) -> str:
        """构造编辑事件描述"""
        # 1. 分析hunk差异
        diff_operations = self._parse_hunk_diff(git_record.old_hunk, git_record.new_hunk)
        
        # 2. 构造事件描述
        events = []
        for operation in diff_operations:
            event = f'User edited "{git_record.file_path}":\n\n```diff\n'
            
            if operation['type'] == 'deletion':
                event += f"@@ -{operation['old_start']},{operation['old_count']} +{operation['new_start']},{operation['new_count']} @@\n"
                for line in operation['deleted_lines']:
                    event += f"-{line}\n"
            elif operation['type'] == 'addition':
                event += f"@@ -{operation['old_start']},{operation['old_count']} +{operation['new_start']},{operation['new_count']} @@\n"
                for line in operation['added_lines']:
                    event += f"+{line}\n"
            elif operation['type'] == 'modification':
                event += f"@@ -{operation['old_start']},{operation['old_count']} +{operation['new_start']},{operation['new_count']} @@\n"
                for old_line, new_line in zip(operation['old_lines'], operation['new_lines']):
                    event += f"-{old_line}\n+{new_line}\n"
            
            event += '```'
            events.append(event)
        
        return '\n\n'.join(events) if events else f'User edited "{git_record.file_path}"'
    
    def _parse_hunk_diff(self, old_hunk: str, new_hunk: str) -> List[Dict]:
        """解析hunk差异"""
        if not old_hunk or not new_hunk:
            return []
        
        old_lines = old_hunk.split('\n')
        new_lines = new_hunk.split('\n')
        
        # 使用difflib分析差异
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        operations = []
        current_op = None
        
        for line in diff:
            if line.startswith('@@'):
                continue
            elif line.startswith('-'):
                if current_op is None or current_op['type'] != 'deletion':
                    current_op = {
                        'type': 'deletion',
                        'deleted_lines': [],
                        'old_start': 1,
                        'old_count': 0,
                        'new_start': 1,
                        'new_count': 0
                    }
                    operations.append(current_op)
                current_op['deleted_lines'].append(line[1:])
                current_op['old_count'] += 1
            elif line.startswith('+'):
                if current_op is None or current_op['type'] != 'addition':
                    current_op = {
                        'type': 'addition',
                        'added_lines': [],
                        'old_start': 1,
                        'old_count': 0,
                        'new_start': 1,
                        'new_count': 0
                    }
                    operations.append(current_op)
                current_op['added_lines'].append(line[1:])
                current_op['new_count'] += 1
        
        return operations

class LabelClassifier:
    """标签分类器"""
    
    def __init__(self):
        self.location_labels = ['no-op', 'local-edit', 'non-local-edit']
        self.intent_labels = ['add-imports', 'complete-implementation', 'complete-pattern', 
                             'infer-intent', 'infer-refactor', 'unknown']
    
    def classify_edit_location(self, git_record: GitDiffRecord, cursor_line: int) -> str:
        """分类编辑位置"""
        # 1. 检查是否为no-op
        if git_record.old_file.strip() == git_record.new_file.strip():
            return "no-op"
        
        # 2. 分析修改位置
        modifications = self._find_all_modifications(git_record.old_file, git_record.new_file)
        
        # 3. 判断修改距离
        local_modifications = 0
        non_local_modifications = 0
        
        for mod_line in modifications:
            distance = abs(mod_line - cursor_line)
            if distance <= 3:  # 3行以内认为是local
                local_modifications += 1
            else:
                non_local_modifications += 1
        
        # 4. 根据修改分布决定分类
        if non_local_modifications > 0:
            return "non-local-edit"
        elif local_modifications > 0:
            return "local-edit"
        else:
            return "no-op"
    
    def classify_edit_intent(self, git_record: GitDiffRecord) -> str:
        """分类编辑意图"""
        old_code = git_record.old_file
        new_code = git_record.new_file
        
        # 1. 检查导入语句添加
        if self._has_import_additions(old_code, new_code):
            return "add-imports"
        
        # 2. 检查方法实现
        if self._has_method_implementation(old_code, new_code):
            return "complete-implementation"
        
        # 3. 检查重复模式
        if self._has_repetitive_pattern(old_code, new_code):
            return "complete-pattern"
        
        # 4. 检查变量重命名
        if self._has_variable_renaming(old_code, new_code):
            return "infer-intent"
        
        # 5. 检查代码重构
        if self._has_code_restructuring(old_code, new_code):
            return "infer-refactor"
        
        return "unknown"
    
    def _find_all_modifications(self, old_code: str, new_code: str) -> List[int]:
        """找到所有修改的行号"""
        old_lines = old_code.split('\n')
        new_lines = new_code.split('\n')
        
        modifications = []
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        line_num = 1
        for line in diff:
            if line.startswith('-') or line.startswith('+'):
                modifications.append(line_num)
            if not line.startswith('+'):
                line_num += 1
        
        return modifications
    
    def _has_import_additions(self, old_code: str, new_code: str) -> bool:
        """检查是否有导入语句添加"""
        old_imports = re.findall(r'^import\s+.*$', old_code, re.MULTILINE)
        new_imports = re.findall(r'^import\s+.*$', new_code, re.MULTILINE)
        return len(new_imports) > len(old_imports)
    
    def _has_method_implementation(self, old_code: str, new_code: str) -> bool:
        """检查是否有方法实现"""
        # 简化检查：查看是否有大量代码添加
        old_lines = len(old_code.split('\n'))
        new_lines = len(new_code.split('\n'))
        return new_lines - old_lines > 5
    
    def _has_repetitive_pattern(self, old_code: str, new_code: str) -> bool:
        """检查是否有重复模式"""
        # 简化检查：查看是否有相似的行添加
        old_lines = set(old_code.split('\n'))
        new_lines = set(new_code.split('\n'))
        added_lines = new_lines - old_lines
        
        # 检查添加的行是否有相似模式
        if len(added_lines) >= 2:
            added_list = list(added_lines)
            for i in range(len(added_list)):
                for j in range(i + 1, len(added_list)):
                    # 简单的相似性检查
                    similarity = self._calculate_similarity(added_list[i], added_list[j])
                    if similarity > 0.7:
                        return True
        
        return False
    
    def _has_variable_renaming(self, old_code: str, new_code: str) -> bool:
        """检查是否有变量重命名"""
        # 简化检查：查看是否有标识符的替换
        old_words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', old_code)
        new_words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', new_code)
        
        old_word_count = {}
        new_word_count = {}
        
        for word in old_words:
            old_word_count[word] = old_word_count.get(word, 0) + 1
        
        for word in new_words:
            new_word_count[word] = new_word_count.get(word, 0) + 1
        
        # 检查是否有词频显著变化
        for word in old_word_count:
            if old_word_count[word] > 1 and new_word_count.get(word, 0) == 0:
                return True
        
        return False
    
    def _has_code_restructuring(self, old_code: str, new_code: str) -> bool:
        """检查是否有代码重构"""
        # 简化检查：查看代码结构是否有显著变化
        old_lines = old_code.split('\n')
        new_lines = new_code.split('\n')
        
        # 检查缩进结构变化
        old_indents = [len(line) - len(line.lstrip()) for line in old_lines if line.strip()]
        new_indents = [len(line) - len(line.lstrip()) for line in new_lines if line.strip()]
        
        if len(old_indents) != len(new_indents):
            return True
        
        # 检查缩进模式是否有显著变化
        indent_changes = sum(1 for i, j in zip(old_indents, new_indents) if abs(i - j) > 2)
        return indent_changes > len(old_indents) * 0.3
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 使用简单的编辑距离计算相似度
        import difflib
        return difflib.SequenceMatcher(None, str1, str2).ratio()

class AssertionsGenerator:
    """评估断言生成器"""

    def generate_assertions(self, git_record: GitDiffRecord) -> str:
        """基于review_message生成assertions"""
        if not git_record.review_message:
            return ""

        review_analysis = self._parse_review_message(git_record.review_message)
        code_change = self._analyze_code_change(git_record.old_file, git_record.new_file)

        assertions = []

        if review_analysis.type == "functionality":
            assertion = self._generate_functionality_assertion(code_change, review_analysis)
            assertions.append(assertion)
        elif review_analysis.type == "style":
            assertion = self._generate_style_assertion(code_change, review_analysis)
            assertions.append(assertion)
        elif review_analysis.type == "performance":
            assertion = self._generate_performance_assertion(code_change, review_analysis)
            assertions.append(assertion)
        else:
            assertion = f"Ensure that the test output addresses the review concern: {review_analysis.description}"
            assertions.append(assertion)

        # 添加通用检查
        assertions.extend(self._generate_general_assertions(code_change))

        return '\n'.join(assertions)

    def _parse_review_message(self, message: str) -> ReviewAnalysis:
        """解析review消息"""
        patterns = {
            'functionality': r'【功能性问题】(.+)',
            'style': r'【代码风格】(.+)',
            'performance': r'【性能问题】(.+)',
            'security': r'【安全问题】(.+)'
        }

        for issue_type, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                return ReviewAnalysis(
                    type=issue_type,
                    description=match.group(1),
                    suggestions=self._extract_suggestions(match.group(1))
                )

        return ReviewAnalysis(type="general", description=message, suggestions=[])

    def _extract_suggestions(self, description: str) -> List[str]:
        """从描述中提取建议"""
        suggestions = []
        if "建议" in description:
            suggestion_part = description.split("建议")[1]
            suggestions.append(suggestion_part.strip())
        return suggestions

    def _analyze_code_change(self, old_code: str, new_code: str) -> Dict:
        """分析代码变化"""
        return {
            'lines_added': len(new_code.split('\n')) - len(old_code.split('\n')),
            'lines_modified': self._count_modified_lines(old_code, new_code),
            'complexity_change': self._estimate_complexity_change(old_code, new_code)
        }

    def _count_modified_lines(self, old_code: str, new_code: str) -> int:
        """计算修改的行数"""
        old_lines = old_code.split('\n')
        new_lines = new_code.split('\n')

        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        modified_count = 0

        for line in diff:
            if line.startswith('-') or line.startswith('+'):
                modified_count += 1

        return modified_count // 2  # 每个修改包含一个删除和一个添加

    def _estimate_complexity_change(self, old_code: str, new_code: str) -> str:
        """估算复杂度变化"""
        old_complexity = self._calculate_cyclomatic_complexity(old_code)
        new_complexity = self._calculate_cyclomatic_complexity(new_code)

        if new_complexity > old_complexity:
            return "increased"
        elif new_complexity < old_complexity:
            return "decreased"
        else:
            return "unchanged"

    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """简化的圈复杂度计算"""
        complexity_keywords = ['if', 'else', 'elif', 'while', 'for', 'try', 'except', 'case', 'switch']
        complexity = 1  # 基础复杂度

        for keyword in complexity_keywords:
            complexity += code.count(keyword)

        return complexity

    def _generate_functionality_assertion(self, code_change: Dict, review_analysis: ReviewAnalysis) -> str:
        """生成功能性检查的assertion"""
        description = review_analysis.description.lower()

        if "null" in description and "check" in description:
            return "Ensure that the test output properly handles null values and includes appropriate null checks"
        elif "stringutils" in description:
            return "Ensure that the test output uses StringUtils.isBlank() instead of simple null checks for string validation"
        elif "exception" in description:
            return "Ensure that the test output includes proper exception handling mechanisms"
        else:
            return f"Ensure that the test output addresses the functionality concern: {review_analysis.description}"

    def _generate_style_assertion(self, code_change: Dict, review_analysis: ReviewAnalysis) -> str:
        """生成代码风格检查的assertion"""
        return f"Ensure that the test output follows proper code style guidelines: {review_analysis.description}"

    def _generate_performance_assertion(self, code_change: Dict, review_analysis: ReviewAnalysis) -> str:
        """生成性能检查的assertion"""
        return f"Ensure that the test output implements performance optimizations: {review_analysis.description}"

    def _generate_general_assertions(self, code_change: Dict) -> List[str]:
        """生成通用检查assertions"""
        assertions = []

        if code_change['lines_added'] > 0:
            assertions.append("Ensure that the test output contains the expected code additions")

        if code_change['lines_modified'] > 0:
            assertions.append("Ensure that the test output properly modifies the existing code")

        if code_change['complexity_change'] == "increased":
            assertions.append("Ensure that the increased code complexity is justified and well-structured")

        return assertions

class DataProcessingPipeline:
    """完整的数据处理管道"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.quality_threshold = self.config.get('quality_threshold', 0.6)

        # 初始化各个组件
        self.cursor_inferrer = CursorPositionInferrer()
        self.region_determiner = EditableRegionDeterminer()
        self.events_constructor = EventsConstructor()
        self.label_classifier = LabelClassifier()
        self.assertions_generator = AssertionsGenerator()

    def process_batch(self, raw_data_list: List[Dict]) -> Dict:
        """批量处理原始数据"""
        processed_records = []
        failed_records = []

        for raw_data in raw_data_list:
            try:
                # 转换为GitDiffRecord
                git_record = GitDiffRecord(**raw_data)

                # 转换为Zeta格式
                zeta_record = self._convert_to_zeta_format(git_record)

                # 质量验证
                validation_errors = self._validate_zeta_format(zeta_record)
                if validation_errors:
                    failed_records.append({
                        'record': raw_data,
                        'errors': validation_errors
                    })
                    continue

                # 质量评估
                quality_score = self._assess_data_quality(zeta_record)
                if quality_score < self.quality_threshold:
                    failed_records.append({
                        'record': raw_data,
                        'reason': f'Low quality score: {quality_score:.2f}'
                    })
                    continue

                processed_records.append(zeta_record)

            except Exception as e:
                failed_records.append({
                    'record': raw_data,
                    'error': str(e)
                })

        # 数据集划分
        train_data, eval_data, dpo_data = self._split_dataset(processed_records)

        return {
            'train': train_data,
            'eval': eval_data,
            'dpo': dpo_data,
            'failed': failed_records,
            'statistics': self._generate_statistics(train_data, eval_data, dpo_data, failed_records)
        }

    def _convert_to_zeta_format(self, git_record: GitDiffRecord) -> ZetaTrainingRecord:
        """将GitDiffRecord转换为ZetaTrainingRecord"""
        # 1. 推断光标位置
        cursor_line, cursor_col = self.cursor_inferrer.infer_cursor_position(git_record)

        # 2. 确定可编辑区域
        start_line, end_line = self.region_determiner.determine_editable_region(git_record, cursor_line)

        # 3. 构造input字段
        input_code = self._construct_input_with_markers(
            git_record.old_file, cursor_line, cursor_col, start_line, end_line
        )

        # 4. 构造output字段
        output_code = self._construct_output_with_markers(
            git_record.new_file, start_line, end_line
        )

        # 5. 构造events字段
        events = self.events_constructor.construct_edit_events(git_record)

        # 6. 分类标签
        location_label = self.label_classifier.classify_edit_location(git_record, cursor_line)
        intent_label = self.label_classifier.classify_edit_intent(git_record)
        labels = f"{location_label},{intent_label}"

        # 7. 生成assertions
        assertions = self.assertions_generator.generate_assertions(git_record)

        return ZetaTrainingRecord(
            events=events,
            input=input_code,
            output=output_code,
            labels=labels,
            assertions=assertions
        )

    def _construct_input_with_markers(self, code: str, cursor_line: int, cursor_col: int,
                                    start_line: int, end_line: int) -> str:
        """构造带标记的输入代码"""
        lines = code.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            if i == start_line:
                result_lines.append('<|editable_region_start|>')

            if i == cursor_line:
                # 在光标位置插入标记
                line_with_cursor = line[:cursor_col] + '<|user_cursor_is_here|>' + line[cursor_col:]
                result_lines.append(line_with_cursor)
            else:
                result_lines.append(line)

            if i == end_line:
                result_lines.append('<|editable_region_end|>')

        return '\n'.join(result_lines)

    def _construct_output_with_markers(self, code: str, start_line: int, end_line: int) -> str:
        """构造带标记的输出代码"""
        lines = code.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            if i == start_line:
                result_lines.append('<|editable_region_start|>')

            result_lines.append(line)

            if i == end_line:
                result_lines.append('<|editable_region_end|>')

        return '\n'.join(result_lines)

    def _validate_zeta_format(self, record: ZetaTrainingRecord) -> List[str]:
        """验证Zeta格式"""
        errors = []

        # 检查必需字段
        if not record.events:
            errors.append("Missing events field")
        if not record.input:
            errors.append("Missing input field")
        if not record.output:
            errors.append("Missing output field")
        if not record.labels:
            errors.append("Missing labels field")

        # 检查特殊标记
        if record.input:
            cursor_count = record.input.count('<|user_cursor_is_here|>')
            if cursor_count != 1:
                errors.append(f"Input must contain exactly one cursor marker, found {cursor_count}")

            start_count = record.input.count('<|editable_region_start|>')
            end_count = record.input.count('<|editable_region_end|>')
            if start_count != 1 or end_count != 1:
                errors.append(f"Input must contain exactly one editable region")

        # 检查标签格式
        if record.labels:
            if not self._validate_label_format(record.labels):
                errors.append("Invalid label format")

        return errors

    def _validate_label_format(self, labels: str) -> bool:
        """验证标签格式"""
        valid_location_labels = ['no-op', 'local-edit', 'non-local-edit']
        valid_intent_labels = ['add-imports', 'complete-implementation', 'complete-pattern',
                              'infer-intent', 'infer-refactor', 'unknown']

        label_parts = labels.split(',')
        if len(label_parts) != 2:
            return False

        location_label, intent_label = [label.strip() for label in label_parts]

        return (location_label in valid_location_labels and
                intent_label in valid_intent_labels)

    def _assess_data_quality(self, record: ZetaTrainingRecord) -> float:
        """评估数据质量"""
        score = 0.0
        max_score = 1.0

        # 基础格式检查 (0.3)
        if self._is_code_valid(record.input) and self._is_code_valid(record.output):
            score += 0.3

        # 编辑合理性检查 (0.3)
        edit_reasonableness = self._evaluate_edit_reasonableness(record.input, record.output)
        score += edit_reasonableness * 0.3

        # 上下文相关性检查 (0.2)
        context_relevance = self._evaluate_context_relevance(record.events, record.input)
        score += context_relevance * 0.2

        # 标签准确性检查 (0.2)
        label_accuracy = self._evaluate_label_accuracy(record)
        score += label_accuracy * 0.2

        return min(score, max_score)

    def _is_code_valid(self, code: str) -> bool:
        """检查代码是否语法有效"""
        # 简化检查：确保代码不为空且包含基本结构
        if not code or not code.strip():
            return False

        # 检查是否包含基本的代码结构
        code_indicators = ['{', '}', '(', ')', ';', '=', 'class', 'function', 'def', 'public', 'private']
        return any(indicator in code for indicator in code_indicators)

    def _evaluate_edit_reasonableness(self, input_code: str, output_code: str) -> float:
        """评估编辑的合理性"""
        # 简化评估：检查编辑是否在合理范围内
        input_lines = len(input_code.split('\n'))
        output_lines = len(output_code.split('\n'))

        line_diff = abs(output_lines - input_lines)

        # 编辑幅度合理性
        if line_diff == 0:
            return 0.5  # 可能是no-op或小修改
        elif line_diff <= 10:
            return 1.0  # 合理的编辑幅度
        elif line_diff <= 50:
            return 0.7  # 较大但可接受的编辑
        else:
            return 0.3  # 编辑幅度过大

    def _evaluate_context_relevance(self, events: str, input_code: str) -> float:
        """评估上下文相关性"""
        # 简化评估：检查events是否与input相关
        if not events:
            return 0.5

        # 检查events中是否包含与input相关的信息
        input_words = set(re.findall(r'\b\w+\b', input_code.lower()))
        events_words = set(re.findall(r'\b\w+\b', events.lower()))

        common_words = input_words.intersection(events_words)
        if len(input_words) == 0:
            return 0.5

        relevance = len(common_words) / len(input_words)
        return min(relevance * 2, 1.0)  # 放大相关性分数

    def _evaluate_label_accuracy(self, record: ZetaTrainingRecord) -> float:
        """评估标签准确性"""
        # 简化评估：基于启发式规则检查标签是否合理
        if not record.labels:
            return 0.0

        location_label, intent_label = record.labels.split(',')
        location_label = location_label.strip()
        intent_label = intent_label.strip()

        # 检查location标签的合理性
        location_score = self._check_location_label_accuracy(record, location_label)

        # 检查intent标签的合理性
        intent_score = self._check_intent_label_accuracy(record, intent_label)

        return (location_score + intent_score) / 2

    def _check_location_label_accuracy(self, record: ZetaTrainingRecord, location_label: str) -> float:
        """检查位置标签的准确性"""
        input_clean = record.input.replace('<|user_cursor_is_here|>', '').replace('<|editable_region_start|>', '').replace('<|editable_region_end|>', '')
        output_clean = record.output.replace('<|editable_region_start|>', '').replace('<|editable_region_end|>', '')

        if location_label == 'no-op':
            return 1.0 if input_clean.strip() == output_clean.strip() else 0.0
        elif location_label in ['local-edit', 'non-local-edit']:
            return 1.0 if input_clean.strip() != output_clean.strip() else 0.0
        else:
            return 0.5

    def _check_intent_label_accuracy(self, record: ZetaTrainingRecord, intent_label: str) -> float:
        """检查意图标签的准确性"""
        # 简化检查：基于代码变化特征
        if intent_label == 'add-imports':
            return 1.0 if 'import' in record.output and 'import' not in record.input else 0.5
        elif intent_label == 'complete-implementation':
            input_lines = len(record.input.split('\n'))
            output_lines = len(record.output.split('\n'))
            return 1.0 if output_lines > input_lines + 3 else 0.5
        else:
            return 0.7  # 其他标签给予中等分数

    def _split_dataset(self, records: List[ZetaTrainingRecord]) -> Tuple[List[ZetaTrainingRecord], List[ZetaTrainingRecord], List[ZetaTrainingRecord]]:
        """划分数据集"""
        # 简化划分：按比例随机划分
        import random
        random.shuffle(records)

        total = len(records)
        train_size = int(total * 0.7)
        eval_size = int(total * 0.15)

        train_data = records[:train_size]
        eval_data = records[train_size:train_size + eval_size]
        dpo_data = records[train_size + eval_size:]

        return train_data, eval_data, dpo_data

    def _generate_statistics(self, train_data: List, eval_data: List, dpo_data: List, failed_records: List) -> Dict:
        """生成统计信息"""
        return {
            'total_processed': len(train_data) + len(eval_data) + len(dpo_data),
            'train_count': len(train_data),
            'eval_count': len(eval_data),
            'dpo_count': len(dpo_data),
            'failed_count': len(failed_records),
            'success_rate': (len(train_data) + len(eval_data) + len(dpo_data)) / (len(train_data) + len(eval_data) + len(dpo_data) + len(failed_records)) if (len(train_data) + len(eval_data) + len(dpo_data) + len(failed_records)) > 0 else 0
        }

def main():
    """主函数示例"""
    # 示例用法
    sample_data = {
        "mrcr_url": "example_url",
        "file_path": "service/src/main/java/SimpleUser.java",
        "code_type": "java",
        "old_file": "public class SimpleUser {\n    private String name;\n}",
        "new_file": "public class SimpleUser {\n    private String name;\n    private String email;\n}",
        "old_hunk": "private String name;",
        "new_hunk": "private String name;\nprivate String email;",
        "old_commit_id": "abc123",
        "new_commit_id": "def456",
        "review_line": 3,
        "review_message": "【功能性问题】建议添加email字段的getter和setter方法",
        "severity": "一般",
        "category": "",
        "author": "reviewer",
        "start_line": 2,
        "end_line": 3,
        "code_with_line": "line 1:public class SimpleUser {\nline 2:    private String name;\nline 3:}"
    }

    # 创建处理管道
    pipeline = DataProcessingPipeline()

    # 处理数据
    result = pipeline.process_batch([sample_data])

    # 输出结果
    print("Processing Results:")
    print(f"Statistics: {result['statistics']}")
    print(f"Train samples: {len(result['train'])}")
    print(f"Eval samples: {len(result['eval'])}")
    print(f"DPO samples: {len(result['dpo'])}")
    print(f"Failed samples: {len(result['failed'])}")

if __name__ == "__main__":
    main()
