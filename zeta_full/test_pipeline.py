#!/usr/bin/env python3
"""
数据处理管道测试脚本
用于验证数据转换的正确性和完整性
"""

import json
import tempfile
import shutil
from pathlib import Path
from data_processor import DataProcessingPipeline

def test_single_record():
    """测试单条记录的处理"""
    print("=== 测试单条记录处理 ===")
    
    # 示例数据
    sample_data = {
        "mrcr_url": "https://example.com/repo",
        "file_path": "service/src/main/java/SimpleUser.java",
        "code_type": "java",
        "old_file": """
package com.example.model;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SimpleUser {
    private String name;
    private String email;
    
    public void updateName() {
        if (this.name == null) {
            return;
        }
        this.name = this.name.trim();
    }
}
""",
        "new_file": """
package com.example.model;

import lombok.Getter;
import lombok.Setter;
import org.apache.commons.lang3.StringUtils;

@Getter
@Setter
public class SimpleUser {
    private String name;
    private String email;
    
    public void updateName() {
        if (StringUtils.isBlank(this.name)) {
            return;
        }
        this.name = this.name.trim();
    }
}
""",
        "old_hunk": "if (this.name == null) {",
        "new_hunk": "if (StringUtils.isBlank(this.name)) {",
        "old_commit_id": "abc123",
        "new_commit_id": "def456",
        "review_line": 14,
        "review_message": "【功能性问题】建议使用StringUtils.isBlank进行空值检查",
        "severity": "一般",
        "category": "代码质量",
        "author": "reviewer",
        "start_line": 14,
        "end_line": 14,
        "code_with_line": "line 12:    public void updateName() {\nline 13:        if (this.name == null) {\nline 14:            return;\nline 15:        }"
    }
    
    # 创建处理管道
    pipeline = DataProcessingPipeline()
    
    # 处理数据
    result = pipeline.process_batch([sample_data])
    
    # 验证结果
    print(f"处理统计: {result['statistics']}")
    
    if result['train']:
        train_record = result['train'][0]
        print(f"\n训练数据示例:")
        print(f"Events: {train_record.events[:100]}...")
        print(f"Labels: {train_record.labels}")
        print(f"Input包含光标标记: {'<|user_cursor_is_here|>' in train_record.input}")
        print(f"Input包含可编辑区域: {'<|editable_region_start|>' in train_record.input}")
        print(f"Output包含可编辑区域: {'<|editable_region_start|>' in train_record.output}")
    
    if result['eval']:
        eval_record = result['eval'][0]
        print(f"\n评估数据示例:")
        print(f"Assertions: {eval_record.assertions}")
    
    return result

def test_batch_processing():
    """测试批量处理"""
    print("\n=== 测试批量处理 ===")
    
    # 加载示例数据
    sample_file = Path("sample_input.jsonl")
    if not sample_file.exists():
        print("示例文件不存在，跳过批量测试")
        return
    
    raw_data = []
    with open(sample_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                raw_data.append(json.loads(line))
    
    print(f"加载了 {len(raw_data)} 条示例数据")
    
    # 创建处理管道
    config = {
        'quality_control': {
            'quality_threshold': 0.5  # 降低阈值以便测试
        }
    }
    pipeline = DataProcessingPipeline(config)
    
    # 处理数据
    result = pipeline.process_batch(raw_data)
    
    # 输出统计信息
    stats = result['statistics']
    print(f"\n批量处理统计:")
    print(f"  总处理: {stats['total_processed']}")
    print(f"  训练集: {stats['train_count']}")
    print(f"  评估集: {stats['eval_count']}")
    print(f"  DPO数据: {stats['dpo_count']}")
    print(f"  失败: {stats['failed_count']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    
    # 显示一些样本
    if result['train']:
        print(f"\n训练样本标签分布:")
        label_counts = {}
        for record in result['train']:
            labels = record.labels
            label_counts[labels] = label_counts.get(labels, 0) + 1
        
        for labels, count in label_counts.items():
            print(f"  {labels}: {count}")
    
    if result['failed']:
        print(f"\n失败样本原因:")
        failure_reasons = {}
        for failed in result['failed']:
            reason = failed.get('reason', failed.get('error', 'Unknown'))
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        for reason, count in failure_reasons.items():
            print(f"  {reason}: {count}")
    
    return result

def test_output_format():
    """测试输出格式"""
    print("\n=== 测试输出格式 ===")
    
    # 使用临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试数据
        test_data = {
            "mrcr_url": "test",
            "file_path": "test.java",
            "code_type": "java",
            "old_file": "public class Test { }",
            "new_file": "public class Test {\n    private String name;\n}",
            "old_hunk": "{ }",
            "new_hunk": "{\n    private String name;\n}",
            "old_commit_id": "test1",
            "new_commit_id": "test2",
            "review_line": 1,
            "review_message": "测试消息",
            "severity": "一般",
            "category": "测试",
            "author": "tester",
            "start_line": 1,
            "end_line": 1,
            "code_with_line": "line 1:public class Test { }"
        }
        
        # 处理数据
        pipeline = DataProcessingPipeline()
        result = pipeline.process_batch([test_data])
        
        # 保存到临时文件
        if result['train']:
            train_file = temp_path / "train.jsonl"
            with open(train_file, 'w', encoding='utf-8') as f:
                for record in result['train']:
                    record_dict = {
                        'events': record.events,
                        'input': record.input,
                        'output': record.output,
                        'labels': record.labels
                    }
                    f.write(json.dumps(record_dict, ensure_ascii=False) + '\n')
            
            # 验证文件格式
            with open(train_file, 'r', encoding='utf-8') as f:
                line = f.readline()
                parsed = json.loads(line)
                
                print("输出格式验证:")
                print(f"  包含events字段: {'events' in parsed}")
                print(f"  包含input字段: {'input' in parsed}")
                print(f"  包含output字段: {'output' in parsed}")
                print(f"  包含labels字段: {'labels' in parsed}")
                print(f"  input包含光标标记: {'<|user_cursor_is_here|>' in parsed['input']}")
                print(f"  标签格式正确: {len(parsed['labels'].split(',')) == 2}")

def test_label_classification():
    """测试标签分类功能"""
    print("\n=== 测试标签分类 ===")
    
    test_cases = [
        {
            "name": "导入语句添加",
            "old_file": "public class Test { }",
            "new_file": "import java.util.List;\n\npublic class Test { }",
            "expected_intent": "add-imports"
        },
        {
            "name": "方法实现",
            "old_file": "public void method() { }",
            "new_file": "public void method() {\n    System.out.println(\"Hello\");\n    return;\n}",
            "expected_intent": "complete-implementation"
        },
        {
            "name": "无修改",
            "old_file": "public class Test { }",
            "new_file": "public class Test { }",
            "expected_location": "no-op"
        }
    ]
    
    pipeline = DataProcessingPipeline()
    
    for case in test_cases:
        test_data = {
            "mrcr_url": "test",
            "file_path": "test.java",
            "code_type": "java",
            "old_file": case["old_file"],
            "new_file": case["new_file"],
            "old_hunk": "",
            "new_hunk": "",
            "old_commit_id": "test1",
            "new_commit_id": "test2",
            "review_line": 1,
            "review_message": "",
            "severity": "一般",
            "category": "测试",
            "author": "tester",
            "start_line": 1,
            "end_line": 1,
            "code_with_line": "line 1:test"
        }
        
        result = pipeline.process_batch([test_data])
        
        if result['train']:
            labels = result['train'][0].labels
            location_label, intent_label = labels.split(',')
            
            print(f"\n{case['name']}:")
            print(f"  实际标签: {labels}")
            
            if 'expected_location' in case:
                match = location_label == case['expected_location']
                print(f"  位置标签匹配: {match} (期望: {case['expected_location']}, 实际: {location_label})")
            
            if 'expected_intent' in case:
                match = intent_label == case['expected_intent']
                print(f"  意图标签匹配: {match} (期望: {case['expected_intent']}, 实际: {intent_label})")

def main():
    """主测试函数"""
    print("开始数据处理管道测试\n")
    
    try:
        # 运行各项测试
        test_single_record()
        test_batch_processing()
        test_output_format()
        test_label_classification()
        
        print("\n=== 测试完成 ===")
        print("所有测试已完成，请检查输出结果")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
