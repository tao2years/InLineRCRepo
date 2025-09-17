#!/usr/bin/env python3
"""
清理项目，将无用文件移到backup
"""

import os
import shutil
from datetime import datetime

class ProjectCleaner:
    def __init__(self):
        self.backup_dir = "backup"
        
        # 需要保留的核心文件和文件夹
        self.keep_files = {
            # 核心数据文件夹
            'benchmark',
            'final_gpt4o_output_10',
            'final_gpt4o_output_20', 
            'gpt5_manual_10',
            'gpt5_manual_20',
            'gpt5_result_10',
            'gpt5_result_20',
            
            # 核心配置和文档
            'instruction.md',
            'README.md',
            'LICENSE',
            'Recent Changes设计.pptx',
            
            # 最新prompt模板
            'RC_prompt_v9_improved.txt',
            
            # 备份文件夹本身
            'backup',
            '__pycache__'
        }
        
        # 需要移动到backup的文件和文件夹
        self.move_to_backup = []
    
    def scan_files(self):
        """扫描当前目录，找出需要移动的文件"""
        current_files = set(os.listdir('.'))
        
        for item in current_files:
            if item not in self.keep_files and not item.startswith('.'):
                self.move_to_backup.append(item)
        
        print(f"📁 当前文件总数: {len(current_files)}")
        print(f"✅ 保留文件数: {len(self.keep_files)}")
        print(f"📦 需要移动到backup: {len(self.move_to_backup)}")
        
        return self.move_to_backup
    
    def move_files_to_backup(self):
        """将文件移动到backup"""
        if not self.move_to_backup:
            print("✅ 没有需要移动的文件")
            return
        
        # 创建带时间戳的backup子目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = os.path.join(self.backup_dir, f"cleanup_{timestamp}")
        os.makedirs(backup_subdir, exist_ok=True)
        
        moved_count = 0
        failed_count = 0
        
        for item in self.move_to_backup:
            try:
                src = item
                dst = os.path.join(backup_subdir, item)
                
                if os.path.isfile(src):
                    shutil.move(src, dst)
                    print(f"📄 移动文件: {src} → {dst}")
                elif os.path.isdir(src):
                    shutil.move(src, dst)
                    print(f"📁 移动文件夹: {src} → {dst}")
                
                moved_count += 1
                
            except Exception as e:
                print(f"❌ 移动失败 {src}: {e}")
                failed_count += 1
        
        print(f"\n🎉 清理完成！")
        print(f"✅ 成功移动: {moved_count} 个项目")
        print(f"❌ 移动失败: {failed_count} 个项目")
        print(f"📦 备份位置: {backup_subdir}")
        
        return moved_count, failed_count
    
    def show_preview(self):
        """显示清理预览"""
        print("=== 项目清理预览 ===")
        print("\n🔒 将保留的核心文件/文件夹:")
        for item in sorted(self.keep_files):
            if os.path.exists(item):
                print(f"  ✅ {item}")
            else:
                print(f"  ⚠️ {item} (不存在)")
        
        print(f"\n📦 将移动到backup的文件/文件夹:")
        for item in sorted(self.move_to_backup):
            if os.path.isfile(item):
                print(f"  📄 {item}")
            elif os.path.isdir(item):
                print(f"  📁 {item}/")
            else:
                print(f"  ❓ {item} (类型未知)")
    
    def cleanup(self, preview_only=False):
        """执行清理"""
        print("=== 开始项目清理 ===")
        
        # 扫描文件
        self.scan_files()
        
        # 显示预览
        self.show_preview()
        
        if preview_only:
            print("\n📋 这是预览模式，没有实际移动文件")
            return
        
        # 确认执行
        print(f"\n⚠️ 即将移动 {len(self.move_to_backup)} 个项目到backup")
        confirm = input("确认执行清理? (y/N): ").strip().lower()
        
        if confirm == 'y':
            # 执行移动
            moved, failed = self.move_files_to_backup()
            
            # 显示最终状态
            print(f"\n📊 清理后的项目结构:")
            remaining_files = [f for f in os.listdir('.') if not f.startswith('.')]
            for item in sorted(remaining_files):
                if os.path.isfile(item):
                    print(f"  📄 {item}")
                elif os.path.isdir(item):
                    print(f"  📁 {item}/")
            
            print(f"\n🎯 项目已清理完成，保留 {len(remaining_files)} 个核心项目")
        else:
            print("❌ 清理已取消")

if __name__ == "__main__":
    cleaner = ProjectCleaner()
    
    # 先显示预览
    cleaner.cleanup(preview_only=True)
    
    print("\n" + "="*50)
    
    # 执行清理
    cleaner.cleanup(preview_only=False)
