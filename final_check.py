#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re

def check_all_entries():
    error_count = 0
    total_entries = 0
    
    with open('benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            total_entries += 1
            obj = json.loads(line)
            t = obj['prompt']
            sec = t[t.find('## Recent Changes Context'):t.find('These recent changes show the development progression')]
            
            entry_ok = True
            for rc in (3, 2, 1):
                m = re.search(fr'### Recent Change {rc}[\s\S]*?```diff\n([\s\S]*?)\n```', sec)
                if m:
                    lines = m.group(1).split('\n')
                    minus_nums = []
                    plus_nums = []
                    space_nums = []
                    has_indent = False
                    
                    for line_content in lines:
                        if line_content.strip().startswith('-') and ':' in line_content:
                            m2 = re.match(r'-\s*(\d+):(.*)$', line_content)
                            if m2: 
                                minus_nums.append(int(m2.group(1)))
                        elif line_content.strip().startswith('+') and ':' in line_content:
                            m2 = re.match(r'\+\s*(\d+):(.*)$', line_content)
                            if m2: 
                                plus_nums.append(int(m2.group(1)))
                                code = m2.group(2)
                                if len(code) - len(code.lstrip()) > 0:
                                    has_indent = True
                        elif line_content.strip() and ':' in line_content and not line_content.strip().startswith('@@'):
                            m2 = re.match(r'\s*(\d+):(.*)$', line_content)
                            if m2: 
                                space_nums.append(int(m2.group(1)))
                    
                    minus_ok = minus_nums == sorted(minus_nums) if minus_nums else True
                    plus_ok = plus_nums == sorted(plus_nums) if plus_nums else True
                    space_ok = space_nums == sorted(space_nums) if space_nums else True
                    
                    if not (minus_ok and plus_ok and space_ok and has_indent):
                        entry_ok = False
                        print(f"❌ Entry #{total_entries} RC{rc}: 减号{minus_ok} 加号{plus_ok} 空格{space_ok} 缩进{has_indent}")
                        error_count += 1
            
            if entry_ok:
                print(f"✅ Entry #{total_entries}: 所有RC格式正确")
    
    print(f"\n=== 最终结果 ===")
    print(f"总计{total_entries}条数据，错误数: {error_count}")
    print(f"成功率: {(total_entries-error_count)/total_entries*100:.1f}%")
    if error_count == 0:
        print("🎉 所有数据格式完全正确！")
    
    return error_count == 0

if __name__ == '__main__':
    check_all_entries()
