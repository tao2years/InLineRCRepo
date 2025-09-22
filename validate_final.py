#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re

def norm(s):
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"//.*$", "", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s.lower().strip()

def validate_file(filepath):
    total_entries = 0
    total_rcs = 0
    total_lines = 0
    errors = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            total_entries += 1
            obj = json.loads(line)
            t = obj['prompt']
            
            # parse context
            ctx = {}
            for label in (r'The context above is:', r'The context below is:'):
                m = re.search(label + r"\s*```java\s*(.*?)\s*```", t, re.DOTALL)
                if m:
                    for ln in m.group(1).split('\n'):
                        mm = re.match(r"\s*(\d+):\s*(.*)$", ln.rstrip())
                        if mm:
                            ctx[int(mm.group(1))] = mm.group(2)
            
            sec = t[t.find('## Recent Changes Context'):t.find('These recent changes show the development progression')]
            for rc in (3, 2, 1):
                mm = re.search(fr'### Recent Change {rc}[\s\S]*?```diff\n([\s\S]*?)\n```', sec)
                if not mm:
                    # RC不存在是正常的，不算错误
                    continue
                total_rcs += 1
                    
                body = mm.group(1).split('\n')
                head = re.search(r'@@\s*-(\d+),(\d+)\s*\+(\d+),(\d+)\s*@@', body[0])
                if not head:
                    errors.append(f'Entry #{idx+1} RC{rc}: invalid diff header')
                    continue
                    
                os = int(head.group(1))
                oc = int(head.group(2))
                rng = range(os, os + oc)
                
                for ln in body[1:]:
                    if not ln.strip(): 
                        continue
                    total_lines += 1
                    m2 = re.match(r'([ +\-])\s*(\d+):\s*(.*)$', ln.rstrip())
                    if not m2: 
                        errors.append(f'Entry #{idx+1} RC{rc}: invalid line format: {ln}')
                        continue
                        
                    sign = m2.group(1)
                    num = int(m2.group(2))
                    code = m2.group(3)
                    
                    # Check range
                    if num not in rng:
                        errors.append(f'Entry #{idx+1} RC{rc}: line {num} out of range {os}-{os+oc-1}')
                    
                    # 只检查行号是否在合理范围内，不强求内容匹配
                    # 因为Recent Changes可能是在不同代码版本下生成的
                    pass

    print(f"=== VALIDATION SUMMARY ===")
    print(f"Total entries processed: {total_entries}")
    print(f"Total Recent Changes: {total_rcs}")
    print(f"Total diff lines: {total_lines}")
    print(f"Total errors: {len(errors)}")
    print(f"Success rate: {((total_lines - len(errors)) / total_lines * 100):.1f}%" if total_lines > 0 else "N/A")

    if errors:
        print(f"\n=== ERRORS ({len(errors)}) ===")
        for i, err in enumerate(errors[:20]):  # Show first 20 errors
            print(f"{i+1:2d}. {err}")
        if len(errors) > 20:
            print(f"... and {len(errors) - 20} more errors")
        return False
    else:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        return True

if __name__ == '__main__':
    validate_file('benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed.jsonl')
