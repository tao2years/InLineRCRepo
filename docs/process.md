# Recent Changes Benchmark 修复流程指南

本文档详细记录了修复 Recent Changes 部分行号对齐和diff格式问题的完整流程，供初学者或无记忆的Agent参考。

## 📋 问题背景

在 `benchmark/nl2code_java_F20-40_with_rc_separated_final.jsonl` 文件中，Recent Changes 部分存在以下问题：
1. **行号不对齐**: Recent Changes中的行号与context code不对应
2. **diff格式错误**: 减号行和加号行交错显示，不符合标准diff格式
3. **缩进丢失**: 代码缩进与context中的原始缩进不一致
4. **行号顺序错误**: 减号行或加号行内部顺序不是递增的

## 🎯 标准diff格式要求

```diff
@@ -起始行,行数 +起始行,行数 @@
-  行号: 删除的代码行1
-  行号: 删除的代码行2
+  行号: 添加的代码行1
+  行号: 添加的代码行2
   行号: 上下文行
```

**关键要求**:
- 先显示所有删除行（-），再显示所有添加行（+），最后显示上下文行（空格）
- 每组内部按行号递增排序
- 保留原始代码缩进
- 行号必须与context code完全对应

## 🔧 修复流程

### 步骤1: 创建修复脚本

创建 `tools/fix_rc_strict.py` 脚本，包含以下核心函数：

#### 1.1 解析context函数
```python
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
    
    # 解析 context below (同样逻辑)
    # ...
    
    return ctx
```

#### 1.2 代码标准化函数
```python
def norm_code(s: str) -> str:
    # 标准化代码用于匹配（保留字符串内容；去多余空白与注释）
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"//.*$", "", s)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    return s.lower().strip()

def strip_existing_lineno(code: str) -> str:
    # 去掉行首可能存在的旧行号标注，但保留行号后面的所有内容，包括缩进
    return re.sub(r"^\s*\d+:", "", code)
```

#### 1.3 行号分配函数
```python
def assign_numbers_for_block(diff_text: str, ctx_map: dict):
    # 核心逻辑：
    # 1. 先为 '+' 行匹配 context 行号（精确匹配 + 模糊匹配）
    # 2. 再为 ' ' 行匹配
    # 3. 为 '-' 行与相邻 '+' 行配对复用行号
    # 4. 其余未编号的按范围顺序分配
    
    # 输出时按标准diff格式排序：
    # 先删除行，再添加行，最后上下文行，各组内部按行号递增
    minus_items = [it for it in line_items if it['sign'] == '-']
    plus_items = [it for it in line_items if it['sign'] == '+']
    space_items = [it for it in line_items if it['sign'] == ' ']
    
    minus_items.sort(key=lambda x: x['num'] if x['num'] is not None else 999999)
    plus_items.sort(key=lambda x: x['num'] if x['num'] is not None else 999999)
    space_items.sort(key=lambda x: x['num'] if x['num'] is not None else 999999)
    
    sorted_items = header_items + minus_items + plus_items + space_items
```

### 步骤2: 执行修复

```bash
python tools/fix_rc_strict.py
```

### 步骤3: 验证结果

创建验证脚本检查：
- 行号是否与context对应
- diff格式是否正确（先删除行，再添加行）
- 缩进是否保留
- 行号是否递增

```python
# 验证脚本示例
def validate_diff_format(jsonl_file):
    for entry in entries:
        for rc in recent_changes:
            # 检查删除行是否在添加行之前
            # 检查行号是否递增
            # 检查缩进是否保留
            # 检查行号是否在context中存在
```

## ⚠️ 常见错误及解决方案

### 错误1: 行号交错显示
**问题**: 减号行和加号行交错显示
```diff
-  18: old code
+  18: new code  
-  19: old code
+  19: new code
```

**解决**: 按符号分组排序，先所有减号行，再所有加号行

### 错误2: 缩进丢失
**问题**: 正则表达式 `r"\s*(\d+):\s*(.*)$"` 会吃掉冒号后的空格

**解决**: 改为 `r"\s*(\d+):(.*)$"`，不要吃掉冒号后的空格

### 错误3: 行号不对应
**问题**: Recent Changes中的行号在context中不存在

**解决**: 
1. 使用智能匹配算法（精确匹配 + 模糊匹配）
2. 从context中获取正确的代码内容和行号
3. 确保所有"+"行的行号都在context中存在

### 错误4: 上下文行缺少空格前缀
**问题**: 上下文行显示为 `2: code` 而不是 `   2: code`

**解决**: 确保上下文行有正确的空格前缀符号

## 📊 验证标准

修复完成后，每个Recent Changes块应该满足：

1. **格式正确**: `@@ -start,count +start,count @@`
2. **顺序正确**: 删除行 → 添加行 → 上下文行
3. **行号递增**: 每组内部行号严格递增
4. **缩进保留**: 代码缩进与context完全一致
5. **行号对应**: 所有行号都能在context中找到对应内容

## 🎉 成功标准

- 所有20条数据验证通过
- 100%成功率
- 符合标准unified diff格式
- 与context code完全对齐

## 📝 工具文件

- `tools/fix_rc_strict.py`: 核心修复脚本
- `validate_final.py`: 验证脚本  
- `final_check.py`: 完整检查脚本
- `debug_errors.py`: 调试脚本

按照此流程执行，可以确保生成正确的Benchmark数据。
