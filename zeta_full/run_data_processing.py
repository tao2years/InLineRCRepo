#!/usr/bin/env python3
"""
数据处理管道运行脚本
用于将git diff格式的原始数据转换为Zeta训练格式
"""

import json
import yaml
import argparse
import logging
from pathlib import Path
from typing import List, Dict
from data_processor import DataProcessingPipeline, GitDiffRecord, ZetaTrainingRecord

def setup_logging(config: Dict):
    """设置日志配置"""
    log_config = config.get('logging', {})
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_config.get('log_file', 'data_processing.log')),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            return json.load(f)

def load_raw_data(data_path: str) -> List[Dict]:
    """加载原始数据"""
    raw_data = []
    
    if data_path.endswith('.jsonl'):
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    raw_data.append(json.loads(line))
    elif data_path.endswith('.json'):
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                raw_data = data
            else:
                raw_data = [data]
    else:
        raise ValueError(f"Unsupported file format: {data_path}")
    
    return raw_data

def save_processed_data(data: List[ZetaTrainingRecord], output_path: str, format_type: str = 'jsonl'):
    """保存处理后的数据"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format_type == 'jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in data:
                record_dict = {
                    'events': record.events,
                    'input': record.input,
                    'output': record.output,
                    'labels': record.labels
                }
                if record.assertions:
                    record_dict['assertions'] = record.assertions
                
                f.write(json.dumps(record_dict, ensure_ascii=False) + '\n')
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            records_list = []
            for record in data:
                record_dict = {
                    'events': record.events,
                    'input': record.input,
                    'output': record.output,
                    'labels': record.labels
                }
                if record.assertions:
                    record_dict['assertions'] = record.assertions
                records_list.append(record_dict)
            
            json.dump(records_list, f, ensure_ascii=False, indent=2)

def save_dpo_data(data: List[Dict], output_path: str, format_type: str = 'jsonl'):
    """保存DPO数据"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format_type == 'jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in data:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def save_statistics(stats: Dict, output_path: str):
    """保存统计信息"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def save_failed_records(failed_records: List[Dict], output_path: str):
    """保存失败记录"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(failed_records, f, ensure_ascii=False, indent=2)

def generate_markdown_report(result: Dict, output_path: str):
    """生成Markdown格式的处理报告"""
    stats = result['statistics']
    
    report = f"""# 数据处理报告

## 处理统计

- **总处理数量**: {stats['total_processed']}
- **训练集数量**: {stats['train_count']}
- **评估集数量**: {stats['eval_count']}
- **DPO数据数量**: {stats['dpo_count']}
- **失败数量**: {stats['failed_count']}
- **成功率**: {stats['success_rate']:.2%}

## 数据分布

### 训练集 (train.jsonl)
- 用于模型的监督微调(SFT)
- 包含完整的编辑历史和标签信息
- 数量: {stats['train_count']} 条

### 评估集 (eval.jsonl)
- 用于模型性能评估
- 包含assertions用于自动化评估
- 数量: {stats['eval_count']} 条

### DPO数据集 (dpo.jsonl)
- 用于直接偏好优化训练
- 包含chosen/rejected对比数据
- 数量: {stats['dpo_count']} 条

## 质量控制

- 所有数据都经过格式验证和质量评估
- 低质量数据已被过滤
- 失败记录已保存到 `processing_errors.json`

## 使用建议

1. **训练流程**: 先使用train.jsonl进行SFT训练，再使用dpo.jsonl进行DPO优化
2. **评估方法**: 使用eval.jsonl中的assertions进行自动化评估
3. **质量监控**: 定期检查失败记录，优化数据处理流程

## 文件说明

- `train.jsonl`: SFT训练数据
- `eval.jsonl`: 评估数据（包含assertions）
- `dpo.jsonl`: DPO训练数据（包含chosen/rejected对）
- `processing_stats.json`: 详细统计信息
- `processing_errors.json`: 失败记录和错误信息
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据处理管道')
    parser.add_argument('--input', '-i', required=True, help='输入数据文件路径')
    parser.add_argument('--output-dir', '-o', required=True, help='输出目录')
    parser.add_argument('--config', '-c', default='process_config.yaml', help='配置文件路径')
    parser.add_argument('--format', choices=['json', 'jsonl'], default='jsonl', help='输出格式')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式，不保存文件')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 设置日志
    logger = setup_logging(config)
    logger.info(f"开始数据处理，输入文件: {args.input}")
    
    try:
        # 加载原始数据
        logger.info("加载原始数据...")
        raw_data = load_raw_data(args.input)
        logger.info(f"加载了 {len(raw_data)} 条原始记录")
        
        # 创建处理管道
        logger.info("初始化数据处理管道...")
        pipeline = DataProcessingPipeline(config)
        
        # 处理数据
        logger.info("开始处理数据...")
        result = pipeline.process_batch(raw_data)
        
        # 输出统计信息
        stats = result['statistics']
        logger.info(f"处理完成！统计信息:")
        logger.info(f"  - 总处理: {stats['total_processed']}")
        logger.info(f"  - 训练集: {stats['train_count']}")
        logger.info(f"  - 评估集: {stats['eval_count']}")
        logger.info(f"  - DPO数据: {stats['dpo_count']}")
        logger.info(f"  - 失败: {stats['failed_count']}")
        logger.info(f"  - 成功率: {stats['success_rate']:.2%}")
        
        if not args.dry_run:
            # 创建输出目录
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存处理后的数据
            logger.info("保存处理后的数据...")
            
            # 保存训练数据
            if result['train']:
                train_path = output_dir / config['output_format']['train_file']
                save_processed_data(result['train'], train_path, args.format)
                logger.info(f"训练数据已保存到: {train_path}")
            
            # 保存评估数据
            if result['eval']:
                eval_path = output_dir / config['output_format']['eval_file']
                save_processed_data(result['eval'], eval_path, args.format)
                logger.info(f"评估数据已保存到: {eval_path}")
            
            # 保存DPO数据
            if result['dpo']:
                dpo_path = output_dir / config['output_format']['dpo_file']
                save_dpo_data(result['dpo'], dpo_path, args.format)
                logger.info(f"DPO数据已保存到: {dpo_path}")
            
            # 保存统计信息
            stats_path = output_dir / config['logging']['stats_file']
            save_statistics(stats, stats_path)
            logger.info(f"统计信息已保存到: {stats_path}")
            
            # 保存失败记录
            if result['failed']:
                error_path = output_dir / config['error_handling']['error_report_file']
                save_failed_records(result['failed'], error_path)
                logger.info(f"失败记录已保存到: {error_path}")
            
            # 生成处理报告
            report_path = output_dir / "processing_report.md"
            generate_markdown_report(result, report_path)
            logger.info(f"处理报告已保存到: {report_path}")
            
            logger.info(f"所有文件已保存到: {output_dir}")
        else:
            logger.info("试运行模式，未保存文件")
        
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()
