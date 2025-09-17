#!/usr/bin/env python3
"""
生成改进版RC预览文件
"""

import json
from datetime import datetime

def generate_preview():
    # 加载改进的benchmark数据
    benchmarks = []
    with open('benchmark/nl2code_java_F10L_improved_rc.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                benchmarks.append(json.loads(line))
    
    preview_content = f"""# 改进版 Recent Changes Preview

Generated at: {datetime.now().isoformat()}

## 🎯 改进说明

本版本修复了之前RC生成的逻辑问题：
- **修复前**: RC像是"增量补充"（添加注释、添加检查等）
- **修复后**: RC是为了实现当前任务而做的"前置准备"，有逻辑递进关系

正确的逻辑：RC3 → RC2 → RC1 → 当前任务

---

"""
    
    for i, benchmark in enumerate(benchmarks, 1):
        if 'rc_context' not in benchmark:
            continue
            
        rc_context = benchmark['rc_context']
        task = extract_task_from_prompt(benchmark['prompt'])
        
        preview_content += f"""## {i}. {benchmark['id']}

**原始功能**: {task}

**Recent Changes**: {len(rc_context['hunks'])} 个微改动

**递进逻辑**: {rc_context.get('notes', '无说明')}

"""
        
        # 按hunks分组显示
        hunks_by_level = {}
        for hunk in rc_context['hunks']:
            # 从缓存文件中推断是哪个level的hunk
            level = "unknown"
            hunks_by_level.setdefault(level, []).append(hunk)
        
        # 显示每个hunk
        for j, hunk in enumerate(rc_context['hunks'], 1):
            preview_content += f"""### 改动 {j}

- **文件**: `{hunk['path']}`
- **类型**: {hunk['type']}
- **重叠**: {hunk.get('overlap', 'N/A')}
- **邻近**: {hunk.get('nearby', 'N/A')}

**Diff**:
```diff
{hunk['mini_diff']}
```

"""
        
        preview_content += "---\n\n"
    
    # 保存预览文件
    with open('logs/improved_rc_preview.md', 'w', encoding='utf-8') as f:
        f.write(preview_content)
    
    print(f"✅ 改进版预览文件已生成: logs/improved_rc_preview.md")

def extract_task_from_prompt(prompt):
    """从prompt中提取任务描述"""
    import re
    match = re.search(r'The new feature is (.+?)\.', prompt)
    return match.group(1).strip() if match else "未知任务"

if __name__ == "__main__":
    generate_preview()
