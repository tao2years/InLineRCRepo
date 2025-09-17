#!/usr/bin/env python3
"""
设计正确的prompt逻辑
"""

def design_correct_logic():
    print("=== 正确的逻辑设计 ===")
    print()
    print("理解benchmark的结构:")
    print("1. Context Above + Context Below = 当前代码状态（没有新方法）")
    print("2. Task = 要实现的新功能")
    print("3. good_example_response = 新方法的实现")
    print("4. 最终状态 = 当前代码 + 新方法实现")
    print()
    print("RC应该倒推的过程:")
    print("初始状态 -> RC3 -> RC2 -> RC1 -> 最终状态（包含新方法）")
    print()
    
def construct_correct_final_state():
    print("=== 构造正确的最终状态 ===")
    print()
    print("当前状态（Context）:")
    print("- ClassLoaderUtils类，包含getURLs、loadAndInvoke等方法")
    print("- 但没有loadClassWithApplicationLoader方法")
    print()
    print("新方法实现（good_example_response）:")
    print("""    public static void loadClassWithApplicationLoader(String className) {
        try {
            ClassLoader appClassLoader = ClassLoader.getSystemClassLoader();
            log.info("Application ClassLoader: {}", appClassLoader);

            Class<?> loadedClass = appClassLoader.loadClass(className);
            log.info("Loaded Class: {}", loadedClass.getName());
        } catch (ClassNotFoundException e) {
            log.error("load error: {}", e.getMessage());
        }
    }""")
    print()
    print("最终状态应该是:")
    print("- 当前代码 + 新方法实现")
    print("- 这样LLM才能正确倒推出为实现新方法而做的准备工作")

def design_new_prompt():
    print("=== 设计新的prompt ===")
    print()
    print("新prompt应该:")
    print("1. 明确区分'当前状态'和'要实现的新功能'")
    print("2. 构造包含新方法的'最终状态'")
    print("3. 让LLM倒推出为实现新方法而做的准备工作")
    print()
    print("新prompt结构:")
    print("[CURRENT_TASK] 要实现的新功能")
    print("[CURRENT_STATE] 当前代码状态（不包含新方法）")
    print("[NEW_METHOD] 要实现的新方法")
    print("[FINAL_STATE] 最终状态（当前代码+新方法）")
    print("[INTENT] 倒推RC，为实现新方法做准备")

if __name__ == "__main__":
    design_correct_logic()
    print()
    construct_correct_final_state()
    print()
    design_new_prompt()
