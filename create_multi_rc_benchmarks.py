#!/usr/bin/env python3
"""
创建多个Recent Changes版本的benchmark
- 合并现有的40条数据
- 生成3个RC、2个RC、1个RC版本
- 保持优先级: rc1 > rc2 > rc3
"""
import json
import re
import os
from datetime import datetime

def load_existing_data():
    """加载现有的benchmark数据"""
    files_to_merge = [
        'benchmark/nl2code_java_F20-40_with_rc_separated_final_fixed.jsonl',
        'benchmark/nl2code_java_all_20_with_rc_separated_final.jsonl'
    ]
    
    all_data = []
    for file_path in files_to_merge:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        obj = json.loads(line.strip())
                        all_data.append(obj)
            print(f"✅ 加载 {file_path}: {len([line for line in open(file_path, 'r', encoding='utf-8') if line.strip()])} 条")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    print(f"📊 总计加载: {len(all_data)} 条数据")
    return all_data

def extract_recent_changes(prompt):
    """从prompt中提取Recent Changes信息"""
    # 找到Recent Changes部分
    rc_start = prompt.find('## Recent Changes Context')
    rc_end = prompt.find('These recent changes show the development progression')
    
    if rc_start == -1 or rc_end == -1:
        return []
    
    rc_section = prompt[rc_start:rc_end]
    
    # 提取每个Recent Change
    changes = []
    pattern = r'### Recent Change (\d+)(.*?)(?=### Recent Change \d+|$)'
    matches = re.findall(pattern, rc_section, re.DOTALL)
    
    for match in matches:
        change_num = int(match[0])
        change_content = match[1].strip()
        changes.append({
            'number': change_num,
            'content': change_content
        })
    
    # 按编号排序 (rc1 > rc2 > rc3，所以1最优先)
    changes.sort(key=lambda x: x['number'])
    return changes

def create_rc_version(entry, num_changes):
    """创建指定数量Recent Changes的版本"""
    prompt = entry['prompt']

    # 提取Recent Changes
    changes = extract_recent_changes(prompt)

    if len(changes) < num_changes:
        print(f"⚠️  {entry['id']}: 只有{len(changes)}个RC，保持原样")
        # 对于没有足够RC的数据，保持原样，ID不变
        new_entry = entry.copy()
        return new_entry

    # 选择前num_changes个（优先级最高的）
    selected_changes = changes[:num_changes]
    
    # 重新构建Recent Changes部分
    new_rc_section = "## Recent Changes Context\n\n"
    new_rc_section += "Here are some recent changes made to related files that might provide helpful context:\n\n"
    
    for i, change in enumerate(selected_changes):
        new_rc_section += f"### Recent Change {change['number']}\n"
        new_rc_section += change['content']
        if i < len(selected_changes) - 1:
            new_rc_section += "\n\n"
    
    new_rc_section += "\n\nThese recent changes show the development progression"
    
    # 替换原prompt中的Recent Changes部分
    rc_start = prompt.find('## Recent Changes Context')
    rc_end = prompt.find('These recent changes show the development progression')
    rc_end = prompt.find('\n', rc_end) + 1  # 包含整行
    
    new_prompt = prompt[:rc_start] + new_rc_section + prompt[rc_end:]
    
    # 创建新的entry，ID保持不变
    new_entry = entry.copy()
    new_entry['prompt'] = new_prompt

    return new_entry

def main():
    """主函数"""
    print("🚀 开始创建多版本Recent Changes benchmark...")
    
    # 1. 加载现有数据
    all_data = load_existing_data()
    
    if not all_data:
        print("❌ 没有找到数据，退出")
        return
    
    # 2. 创建合并的完整版本 (3个RC)
    output_file_3rc = 'benchmark/nl2code_java_complete_3RC.jsonl'
    with open(output_file_3rc, 'w', encoding='utf-8') as f:
        for entry in all_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"✅ 创建3RC版本: {output_file_3rc} ({len(all_data)} 条)")
    
    # 3. 创建2个RC版本
    output_file_2rc = 'benchmark/nl2code_java_complete_2RC.jsonl'
    with open(output_file_2rc, 'w', encoding='utf-8') as f:
        for entry in all_data:
            new_entry = create_rc_version(entry, 2)
            f.write(json.dumps(new_entry, ensure_ascii=False) + '\n')
    print(f"✅ 创建2RC版本: {output_file_2rc} ({len(all_data)} 条)")

    # 4. 创建1个RC版本
    output_file_1rc = 'benchmark/nl2code_java_complete_1RC.jsonl'
    with open(output_file_1rc, 'w', encoding='utf-8') as f:
        for entry in all_data:
            new_entry = create_rc_version(entry, 1)
            f.write(json.dumps(new_entry, ensure_ascii=False) + '\n')
    print(f"✅ 创建1RC版本: {output_file_1rc} ({len(all_data)} 条)")
    
    # 5. 验证生成的文件
    print("\n🔍 验证生成的文件:")
    for file_path in [output_file_3rc, output_file_2rc, output_file_1rc]:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line for line in f if line.strip()]
                print(f"  {file_path}: {len(lines)} 条")
                
                # 检查第一条的RC数量
                if lines:
                    first_obj = json.loads(lines[0])
                    rc_count = first_obj['prompt'].count('### Recent Change')
                    print(f"    第一条RC数量: {rc_count}")
    
    print(f"\n🎉 完成！生成了3个不同RC数量的benchmark文件")
    print(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
