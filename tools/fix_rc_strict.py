#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from collections import OrderedDict

def parse_context(prompt_text):
    # 解析 context above/below 到 {line_num: content}，保留原始缩进
    ctx = {}

    # 解析 context above
    m = re.search(r'The context above is:\s*```java\s*(.*?)\s*```', prompt_text, re.DOTALL)
    if m:
        block = m.group(1)
        for line in block.split('\n'):
            line = line.rstrip()
            m2 = re.match(r"\s*(\d+):(.*)$", line)  # 不要吃掉冒号后的空格
            if m2:
                n = int(m2.group(1))
                code = m2.group(2)  # 保留原始缩进，包括前导空格
                ctx[n] = code

    # 解析 context below
    m = re.search(r'The context below is:\s*```java\s*(.*?)\s*```', prompt_text, re.DOTALL)
    if m:
        block = m.group(1)
        for line in block.split('\n'):
            line = line.rstrip()
            m2 = re.match(r"\s*(\d+):(.*)$", line)  # 不要吃掉冒号后的空格
            if m2:
                n = int(m2.group(1))
                code = m2.group(2)  # 保留原始缩进，包括前导空格
                ctx[n] = code

    return ctx

def norm_code(s: str) -> str:
    # 标准化代码用于匹配（保留字符串内容；去多余空白与注释）
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"//.*$", "", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s.lower().strip()

def fuzzy_match_score(s1: str, s2: str) -> float:
    # 计算两个代码片段的相似度（0-1）
    s1_norm = norm_code(s1)
    s2_norm = norm_code(s2)
    if not s1_norm or not s2_norm:
        return 0.0
    if s1_norm == s2_norm:
        return 1.0
    # 包含关系
    if s1_norm in s2_norm or s2_norm in s1_norm:
        return 0.8
    # 关键词重叠度
    words1 = set(re.findall(r'\w+', s1_norm))
    words2 = set(re.findall(r'\w+', s2_norm))
    if not words1 or not words2:
        return 0.0
    overlap = len(words1 & words2)
    total = len(words1 | words2)
    return overlap / total if total > 0 else 0.0

def strip_existing_lineno(code: str) -> str:
    # 去掉行首可能存在的（可带前导空格的）旧行号标注，如 "   4: ..."
    # 但保留行号后面的所有内容，包括缩进
    return re.sub(r"^\s*\d+:", "", code)

def extract_rc_blocks(prompt_text):
    # 返回列表 [(header_text, diff_text, start_idx, end_idx)]
    out = []
    recent_start = prompt_text.find('## Recent Changes Context')
    recent_end = prompt_text.find('These recent changes show the development progression')
    if recent_start == -1 or recent_end == -1:
        return out, None, None
    section = prompt_text[recent_start:recent_end]
    for m in re.finditer(r'(### Recent Change \d+ \([^)]+\))\s*```diff\s*(.*?)```', section, re.DOTALL):
        out.append((m.group(1), m.group(2)))
    return out, recent_start, recent_end

def assign_numbers_for_block(diff_text: str, ctx_map: dict):
    # 从 diff_text 构造严格编号后的 diff 内容（优先匹配 '+' 到 context；'-' 尽量与相邻 '+' 复用行号；其余按范围顺序分配）
    lines = [l.rstrip() for l in diff_text.split('\n') if True]
    if not lines:
        return diff_text
    # 找 header
    m = re.search(r'@@\s*-(\d+),(\d+)\s*\+(\d+),(\d+)\s*@@', diff_text)
    if not m:
        return diff_text
    old_start = int(m.group(1)); old_count = int(m.group(2))
    rng_start, rng_end = old_start, old_start + old_count - 1
    allowed = list(range(rng_start, rng_end + 1))

    # 构造 context 的标准化反查映射（限制在范围内）
    ctx_norm_to_num = {}
    for n, code in ctx_map.items():
        if n < rng_start or n > rng_end:
            continue
        ctx_norm_to_num.setdefault(norm_code(code), []).append(n)

    # 解析成条目
    items = []
    header_kept = False
    for l in lines:
        if l.strip().startswith('@@') and not header_kept:
            items.append({'type':'header','text':l.strip()})
            header_kept = True
            continue
        if not l.strip():
            continue
        sign = ' '
        raw = l
        if l.startswith('-') and not l.startswith('---'):
            sign = '-'; raw = l[1:]
        elif l.startswith('+') and not l.startswith('+++'):
            sign = '+'; raw = l[1:]
        elif l.startswith(' '):
            sign = ' '; raw = l[1:]
        code = strip_existing_lineno(raw)
        if not code:
            continue
        items.append({'type':'line','sign':sign,'code':code,'num':None})

    used = set()
    def try_match(item):
        best_num = None
        best_score = 0.0
        target_code = item['code']

        # 1. 精确匹配
        key = norm_code(target_code)
        for cand in ctx_norm_to_num.get(key, []):
            if cand not in used:
                item['num'] = cand
                # 更新代码内容为context中的原始内容（保留缩进）
                if cand in ctx_map:
                    item['code'] = ctx_map[cand]
                used.add(cand)
                return

        # 2. 在整个context中寻找最佳匹配（不限制范围）
        for num, code in ctx_map.items():
            if num in used:
                continue
            score = fuzzy_match_score(target_code, code)
            if score > best_score and score >= 0.4:  # 降低阈值到40%
                best_score = score
                best_num = num

        # 3. 如果找到了匹配，但不在范围内，寻找范围内最近的空行或相似行
        if best_num is not None:
            if rng_start <= best_num <= rng_end:
                item['num'] = best_num
                # 更新代码内容为context中的原始内容（保留缩进）
                if best_num in ctx_map:
                    item['code'] = ctx_map[best_num]
                used.add(best_num)
            else:
                # 在范围内寻找空行或最相似的行
                fallback_num = None
                for cand in range(rng_start, rng_end + 1):
                    if cand not in used:
                        if cand not in ctx_map or not ctx_map[cand].strip():
                            # 优先选择空行
                            fallback_num = cand
                            break
                        elif fallback_num is None:
                            fallback_num = cand
                if fallback_num is not None:
                    item['num'] = fallback_num
                    # 更新代码内容为context中的原始内容（保留缩进）
                    if fallback_num in ctx_map:
                        item['code'] = ctx_map[fallback_num]
                    used.add(fallback_num)

    # 1) 先为 '+' 匹配 context 行号
    for it in items:
        if it.get('type')=='line' and it['sign']=='+':
            try_match(it)
    # 2) 再为 ' ' 匹配
    for it in items:
        if it.get('type')=='line' and it['sign']==' ' and it['num'] is None:
            try_match(it)
    # 3) '-' 不做基于内容的匹配，避免注释/空行误匹配，改由第4步与相邻'+'成对复用行号
    # for it in items:
    #     if it.get('type')=='line' and it['sign']=='-' and it['num'] is None:
    #         try_match(it)
    # 4) 邻近配对：对每个已编号的 '+'，优先向前、再向后寻找最近的未编号 '-' 并复用其行号
    for i,it in enumerate(items):
        if it.get('type')=='line' and it['sign']=='+' and it['num'] is not None:
            paired = False
            for j in range(i-1, -1, -1):
                jt = items[j]
                if jt.get('type')=='line' and jt['sign']=='-' and jt['num'] is None:
                    jt['num'] = it['num']
                    paired = True
                    break
            if not paired:
                for j in range(i+1, len(items)):
                    jt = items[j]
                    if jt.get('type')=='line' and jt['sign']=='-' and jt['num'] is None:
                        jt['num'] = it['num']
                        break
    # 5) 其余未编号的，按 allowed 顺序分配
    for it in items:
        if it.get('type')!='line' or it['num'] is not None:
            continue
        for cand in allowed:
            if cand not in used:
                it['num'] = cand; used.add(cand); break

        # 6) 如果还是没有分配到，强制分配一个范围内的行号
        if it['num'] is None:
            for cand in allowed:
                if cand not in used:
                    it['num'] = cand; used.add(cand); break
            # 如果范围内都用完了，使用范围的第一个行号
            if it['num'] is None:
                it['num'] = allowed[0] if allowed else 1

    # 确保所有行都有正确的缩进，但保持原始diff顺序
    line_items = [it for it in items if it.get('type')=='line']
    header_items = [it for it in items if it.get('type')=='header']

    # 对所有有行号的行，尝试从context中获取正确的代码内容（包括缩进）
    for it in line_items:
        if it['num'] is not None and it['num'] in ctx_map:
            # 对于"+"行和" "行，使用context中的原始内容
            if it['sign'] in ['+', ' ']:
                it['code'] = ctx_map[it['num']]

    # 标准diff格式：先显示所有删除行，再显示所有添加行，最后显示上下文行
    # 每组内部按行号递增排序
    minus_items = [it for it in line_items if it['sign'] == '-']
    plus_items = [it for it in line_items if it['sign'] == '+']
    space_items = [it for it in line_items if it['sign'] == ' ']

    # 各组内部按行号排序
    minus_items.sort(key=lambda x: x['num'] if x['num'] is not None else 999999)
    plus_items.sort(key=lambda x: x['num'] if x['num'] is not None else 999999)
    space_items.sort(key=lambda x: x['num'] if x['num'] is not None else 999999)

    # 重新组合：header + 删除行 + 添加行 + 上下文行
    sorted_items = header_items + minus_items + plus_items + space_items

    # 输出
    out = []
    for it in sorted_items:
        if it['type']=='header':
            out.append(it['text'])
        else:
            if it['num'] is None:
                # 如果没有分配到行号，使用占位符
                out.append(f"{it['sign']}  ??: {it['code']}")
            else:
                out.append(f"{it['sign']}{it['num']:4d}: {it['code']}")
    return '\n'.join(out)

def rebuild_recent_section(prompt_text):
    ctx_map = parse_context(prompt_text)
    blocks, s, e = extract_rc_blocks(prompt_text)
    if not blocks:
        return prompt_text
    section = []
    section.append('## Recent Changes Context')
    section.append('Here are some recent changes that were made to this file to help you understand the development context:')
    section.append('')
    for header, diff_text in blocks:
        fixed = assign_numbers_for_block(diff_text, ctx_map)
        # 清理多余空行，保持 code fence 内紧凑
        fixed = re.sub(r"\n{2,}", "\n", fixed)
        section.append(header)
        section.append('```diff')
        section.append(fixed)
        section.append('```')
        section.append('')
    new_section = '\n'.join(section) + '\n'
    # 组装
    pre = prompt_text[:s]
    post = prompt_text[e:]
    return pre + new_section + post

def process_file(path_in: str, path_out: str):
    with open(path_in, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    out = []
    for idx, line in enumerate(lines):
        try:
            obj = json.loads(line)
        except Exception:
            out.append(line.rstrip('\n'))
            continue
        p = obj.get('prompt', '')
        fixed = rebuild_recent_section(p)
        obj['prompt'] = fixed
        out.append(json.dumps(obj, ensure_ascii=False))
    with open(path_out, 'w', encoding='utf-8') as f:
        for x in out:
            f.write(x + '\n')

if __name__ == '__main__':
    process_file('benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl',
                 'benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed.jsonl')

