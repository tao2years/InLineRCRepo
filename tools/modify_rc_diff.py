#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recent Changes Diff修改工具

用于动态修改benchmark文件中指定行的Recent Changes diff符号
"""

import json
import re
import argparse
import os
from typing import List, Tuple


class RCDiffModifier:
    """Recent Changes Diff修改器"""
    
    def __init__(self, file_path: str = "benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl"):
        """
        初始化修改器
        
        Args:
            file_path: benchmark文件路径
        """
        self.file_path = file_path
        self.data = []
        self.load_data()
    
    def load_data(self):
        """加载benchmark数据"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.data = [json.loads(line.strip()) for line in f if line.strip()]
        
        print(f"✅ 已加载 {len(self.data)} 条benchmark数据")
    
    def reverse_diff_signs(self, diff_content: str) -> str:
        """
        反转diff中的+/-符号
        
        Args:
            diff_content: 原始diff内容
            
        Returns:
            反转后的diff内容
        """
        lines = diff_content.split('\n')
        reversed_lines = []
        
        for line in lines:
            if line.startswith('+'):
                # + 改为 -
                reversed_lines.append('-' + line[1:])
            elif line.startswith('-'):
                # - 改为 +
                reversed_lines.append('+' + line[1:])
            else:
                # 其他行保持不变（如@@行、空行等）
                reversed_lines.append(line)
        
        return '\n'.join(reversed_lines)
    
    def extract_rc_diffs(self, prompt: str) -> Tuple[str, str, str]:
        """
        从prompt中提取三个Recent Changes的diff内容
        
        Args:
            prompt: 完整的prompt内容
            
        Returns:
            (rc3_diff, rc2_diff, rc1_diff) 三个diff内容的元组
        """
        # 使用正则表达式提取Recent Changes的diff部分
        rc3_pattern = r'### Recent Change 3.*?```diff\n(.*?)\n```'
        rc2_pattern = r'### Recent Change 2.*?```diff\n(.*?)\n```'
        rc1_pattern = r'### Recent Change 1.*?```diff\n(.*?)\n```'
        
        rc3_match = re.search(rc3_pattern, prompt, re.DOTALL)
        rc2_match = re.search(rc2_pattern, prompt, re.DOTALL)
        rc1_match = re.search(rc1_pattern, prompt, re.DOTALL)
        
        rc3_diff = rc3_match.group(1) if rc3_match else ""
        rc2_diff = rc2_match.group(1) if rc2_match else ""
        rc1_diff = rc1_match.group(1) if rc1_match else ""
        
        return rc3_diff, rc2_diff, rc1_diff
    
    def replace_rc_diffs(self, prompt: str, new_rc3: str, new_rc2: str, new_rc1: str) -> str:
        """
        替换prompt中的Recent Changes diff内容
        
        Args:
            prompt: 原始prompt
            new_rc3, new_rc2, new_rc1: 新的diff内容
            
        Returns:
            更新后的prompt
        """
        # 替换RC3
        rc3_pattern = r'(### Recent Change 3.*?```diff\n)(.*?)(\n```)'
        prompt = re.sub(rc3_pattern, r'\1' + new_rc3 + r'\3', prompt, flags=re.DOTALL)
        
        # 替换RC2
        rc2_pattern = r'(### Recent Change 2.*?```diff\n)(.*?)(\n```)'
        prompt = re.sub(rc2_pattern, r'\1' + new_rc2 + r'\3', prompt, flags=re.DOTALL)
        
        # 替换RC1
        rc1_pattern = r'(### Recent Change 1.*?```diff\n)(.*?)(\n```)'
        prompt = re.sub(rc1_pattern, r'\1' + new_rc1 + r'\3', prompt, flags=re.DOTALL)
        
        return prompt
    
    def modify_line(self, line_num: int, rc3_flag: int, rc2_flag: int, rc1_flag: int) -> bool:
        """
        修改指定行的Recent Changes diff符号
        
        Args:
            line_num: 目标行号（1-based）
            rc3_flag: RC3标志，0=反转符号，1=保持不变
            rc2_flag: RC2标志，0=反转符号，1=保持不变
            rc1_flag: RC1标志，0=反转符号，1=保持不变
            
        Returns:
            是否修改成功
        """
        # 验证行号
        if line_num < 1 or line_num > len(self.data):
            print(f"❌ 行号超出范围: {line_num} (有效范围: 1-{len(self.data)})")
            return False
        
        # 获取目标数据（转换为0-based索引）
        target_data = self.data[line_num - 1]
        benchmark_id = target_data.get('id', 'unknown')
        
        print(f"\n🎯 修改第{line_num}行: {benchmark_id}")
        print(f"📝 参数: RC3={rc3_flag}, RC2={rc2_flag}, RC1={rc1_flag}")
        
        # 提取当前的RC diffs
        prompt = target_data.get('prompt', '')
        if not prompt:
            print("❌ 该行没有prompt内容")
            return False
        
        rc3_diff, rc2_diff, rc1_diff = self.extract_rc_diffs(prompt)
        
        if not any([rc3_diff, rc2_diff, rc1_diff]):
            print("❌ 未找到Recent Changes内容")
            return False
        
        # 根据标志位处理每个RC
        new_rc3 = rc3_diff if rc3_flag == 1 else self.reverse_diff_signs(rc3_diff)
        new_rc2 = rc2_diff if rc2_flag == 1 else self.reverse_diff_signs(rc2_diff)
        new_rc1 = rc1_diff if rc1_flag == 1 else self.reverse_diff_signs(rc1_diff)
        
        # 显示修改信息
        print(f"  🔄 RC3: {'保持不变' if rc3_flag == 1 else '反转符号'}")
        print(f"  🔄 RC2: {'保持不变' if rc2_flag == 1 else '反转符号'}")
        print(f"  🔄 RC1: {'保持不变' if rc1_flag == 1 else '反转符号'}")
        
        # 替换prompt中的RC内容
        new_prompt = self.replace_rc_diffs(prompt, new_rc3, new_rc2, new_rc1)
        
        # 更新数据
        self.data[line_num - 1]['prompt'] = new_prompt
        
        print("✅ 修改完成")
        return True
    
    def save_data(self, output_path: str = None):
        """
        保存修改后的数据
        
        Args:
            output_path: 输出文件路径，默认覆盖原文件
        """
        if output_path is None:
            output_path = self.file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in self.data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"💾 数据已保存到: {output_path}")
    
    def preview_line(self, line_num: int):
        """
        预览指定行的Recent Changes内容
        
        Args:
            line_num: 行号（1-based）
        """
        if line_num < 1 or line_num > len(self.data):
            print(f"❌ 行号超出范围: {line_num}")
            return
        
        target_data = self.data[line_num - 1]
        benchmark_id = target_data.get('id', 'unknown')
        prompt = target_data.get('prompt', '')
        
        print(f"\n📋 第{line_num}行预览: {benchmark_id}")
        
        if not prompt:
            print("❌ 该行没有prompt内容")
            return
        
        rc3_diff, rc2_diff, rc1_diff = self.extract_rc_diffs(prompt)
        
        print(f"\n🔍 Recent Change 3:")
        print(rc3_diff[:200] + "..." if len(rc3_diff) > 200 else rc3_diff)
        
        print(f"\n🔍 Recent Change 2:")
        print(rc2_diff[:200] + "..." if len(rc2_diff) > 200 else rc2_diff)
        
        print(f"\n🔍 Recent Change 1:")
        print(rc1_diff[:200] + "..." if len(rc1_diff) > 200 else rc1_diff)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='修改benchmark文件中的Recent Changes diff符号')
    parser.add_argument('line_num', type=int, help='目标行号（1-based）')
    parser.add_argument('rc3_flag', type=int, choices=[0, 1], help='RC3标志：0=反转符号，1=保持不变')
    parser.add_argument('rc2_flag', type=int, choices=[0, 1], help='RC2标志：0=反转符号，1=保持不变')
    parser.add_argument('rc1_flag', type=int, choices=[0, 1], help='RC1标志：0=反转符号，1=保持不变')
    parser.add_argument('--file', '-f', default='benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl',
                       help='benchmark文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径（默认覆盖原文件）')
    parser.add_argument('--preview', '-p', action='store_true', help='仅预览，不修改')
    
    args = parser.parse_args()
    
    try:
        # 创建修改器
        modifier = RCDiffModifier(args.file)
        
        if args.preview:
            # 仅预览
            modifier.preview_line(args.line_num)
        else:
            # 执行修改
            success = modifier.modify_line(args.line_num, args.rc3_flag, args.rc2_flag, args.rc1_flag)
            
            if success:
                modifier.save_data(args.output)
                print(f"\n🎉 修改完成！")
            else:
                print(f"\n❌ 修改失败！")
    
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
