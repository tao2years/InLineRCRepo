#!/usr/bin/env python3
"""
随机小说生成器 - 每隔几秒输出一段随机生成的小说内容
"""
import time
import random
import datetime

class StoryGenerator:
    def __init__(self):
        self.characters = [
            "李明", "王小红", "张三", "赵四", "刘德华", "陈美丽", "孙悟空", "猪八戒",
            "小明", "小红", "老王", "阿强", "美美", "大壮", "小芳", "阿杰"
        ]
        
        self.locations = [
            "古老的图书馆", "神秘的森林", "繁华的都市", "宁静的小村庄", "高耸的山峰",
            "深邃的海底", "废弃的工厂", "豪华的宫殿", "偏僻的小屋", "热闹的市场",
            "幽暗的地下室", "美丽的花园", "荒凉的沙漠", "冰冷的雪山", "温暖的咖啡厅"
        ]
        
        self.actions = [
            "发现了一个神秘的宝箱", "遇到了一位奇怪的老人", "听到了诡异的声音",
            "看见了闪闪发光的东西", "感受到了强大的力量", "找到了一张古老的地图",
            "遇到了失散多年的朋友", "发现了隐藏的秘密通道", "拾到了一本魔法书",
            "看到了美丽的彩虹", "听到了天使的歌声", "遇到了会说话的动物",
            "发现了时空裂缝", "找到了传说中的宝剑", "遇到了来自未来的人"
        ]
        
        self.emotions = [
            "兴奋不已", "忐忑不安", "充满好奇", "有些害怕", "非常惊讶",
            "感到温暖", "略显紧张", "十分激动", "有点困惑", "格外开心",
            "深感震撼", "倍感神秘", "异常平静", "满怀期待", "心情复杂"
        ]
        
        self.outcomes = [
            "这改变了他的一生", "从此开始了新的冒险", "让他明白了生活的真谛",
            "使他获得了意想不到的力量", "帮他找到了回家的路", "让他结识了真正的朋友",
            "使他变得更加勇敢", "让他学会了珍惜当下", "帮他解开了心中的谜团",
            "使他找到了人生的方向", "让他体验了前所未有的快乐", "帮他克服了内心的恐惧",
            "使他获得了智慧的启发", "让他发现了自己的潜能", "帮他实现了多年的梦想"
        ]
        
        self.chapter_count = 1
    
    def generate_story_segment(self):
        """生成一段随机小说内容"""
        character = random.choice(self.characters)
        location = random.choice(self.locations)
        action = random.choice(self.actions)
        emotion = random.choice(self.emotions)
        outcome = random.choice(self.outcomes)
        
        story = f"""
╔══════════════════════════════════════════════════════════════╗
║                    第 {self.chapter_count} 章                    ║
╚══════════════════════════════════════════════════════════════╝

    在{location}里，{character}{action}。

    他{emotion}地看着眼前的一切，心中涌起了千万种想法。
    
    这个发现让他意识到，{outcome}。

    时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.chapter_count += 1
        return story
    
    def generate_random_thoughts(self):
        """生成随机想法"""
        thoughts = [
            "🤔 人生就像一盒巧克力，你永远不知道下一颗是什么味道...",
            "✨ 今天的阳光格外温暖，仿佛在诉说着什么故事...",
            "🌟 如果时间可以倒流，你最想回到哪一刻？",
            "🎭 每个人都是自己人生的主角，也是别人故事里的配角...",
            "🌈 梦想就像天边的彩虹，虽然遥远但值得追寻...",
            "🎵 音乐是心灵的语言，能够跨越一切障碍...",
            "📚 书籍是人类进步的阶梯，也是心灵的港湾...",
            "🌙 夜晚的星空总是让人想起远方的朋友...",
            "🍃 风吹过树叶的声音，像是大自然在轻声歌唱...",
            "💭 有时候，最简单的快乐就是最珍贵的财富..."
        ]
        
        return f"""
┌─────────────────────────────────────────────────────────────┐
│  💭 随机思考时刻 - {datetime.datetime.now().strftime('%H:%M:%S')}                     │
├─────────────────────────────────────────────────────────────┤
│  {random.choice(thoughts)}
│                                                             │
└─────────────────────────────────────────────────────────────┘
"""

def main():
    """主函数 - 运行计时器"""
    generator = StoryGenerator()
    
    print("🎬 欢迎来到随机小说生成器！")
    print("📖 每隔3-6秒将为您生成精彩的故事片段...")
    print("⏰ 按 Ctrl+C 可以停止程序")
    print("=" * 70)
    
    try:
        while True:
            # 随机选择输出类型
            if random.random() < 0.7:  # 70% 概率输出故事
                content = generator.generate_story_segment()
            else:  # 30% 概率输出随机想法
                content = generator.generate_random_thoughts()
            
            print(content)
            
            # 随机等待3-6秒
            wait_time = random.uniform(3, 6)
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n\n🎭 故事暂时告一段落...")
        print("💫 感谢您的陪伴，期待下次相遇！")
        print("=" * 70)

if __name__ == "__main__":
    main()
