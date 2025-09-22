#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re

def norm(s):
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"//.*$", "", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s.lower().strip()

def debug_entry(filepath, entry_num):
    with open(filepath, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx + 1 != entry_num:
                continue
                
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
            
            print(f"=== Entry #{entry_num} Context Lines ===")
            for num in sorted(ctx.keys())[:10]:  # Show first 10 lines
                print(f"{num:3d}: {ctx[num]}")
            print("...")
            
            sec = t[t.find('## Recent Changes Context'):t.find('These recent changes show the development progression')]
            for rc in (3, 2, 1):
                print(f"\n=== Entry #{entry_num} RC{rc} ===")
                mm = re.search(fr'### Recent Change {rc}[\s\S]*?```diff\n([\s\S]*?)\n```', sec)
                if not mm: 
                    print("NOT FOUND")
                    continue
                    
                body = mm.group(1).split('\n')
                head = re.search(r'@@\s*-(\d+),(\d+)\s*\+(\d+),(\d+)\s*@@', body[0])
                if not head:
                    print("INVALID HEADER")
                    continue
                    
                os = int(head.group(1))
                oc = int(head.group(2))
                print(f"Range: {os}-{os+oc-1}")
                
                for ln in body[1:]:
                    if not ln.strip(): 
                        continue
                    m2 = re.match(r'([ +\-])\s*(\d+):\s*(.*)$', ln.rstrip())
                    if not m2: 
                        print(f"INVALID FORMAT: {ln}")
                        continue
                        
                    sign = m2.group(1)
                    num = int(m2.group(2))
                    code = m2.group(3)
                    
                    if sign == '+':
                        if num not in ctx:
                            print(f"ERROR: + line {num} not in context: {code}")
                        else:
                            ctx_norm = norm(ctx[num])
                            code_norm = norm(code)
                            if ctx_norm != code_norm:
                                print(f"ERROR: + line {num} content mismatch:")
                                print(f"  CTX: '{ctx[num]}'")
                                print(f"  RC:  '{code}'")
                                print(f"  CTX_NORM: '{ctx_norm}'")
                                print(f"  RC_NORM:  '{code_norm}'")
            break

if __name__ == '__main__':
    # Debug first few problematic entries
    for entry_num in [2, 3, 4, 5]:
        debug_entry('benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed.jsonl', entry_num)
        print("\n" + "="*80 + "\n")
