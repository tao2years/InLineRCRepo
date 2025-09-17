# 整体需求描述

在已有的Benchmark上补充 Recent Changes的上下文。

1. 背景

我们在基于 ShenYu 项目构建的 benchmark（10条样例，在路径benchmark/nl2code_java_F10L.jsonl），

当前 benchmark 缺少“最近改动（Recent Changes, RC）”上下文。为模拟真实开发场景，我们希望由 LLM 自动合成“像刚刚发生过的微改动”，并注入到每条样例。

2. 目标

生成 RC：在同文件和同目录（邻居文件）中，构造一组“刚改过”的微改动（hunks）。

全文件上下文：提供主文件完整代码（以及邻居大段代码），让 LLM 基于“当前 benchmark 任务”，倒推上一步开发者可能会做的微改动。

不设行数上限：让 LLM 自行决定 hunk 的规模。

不做剪枝/排序：保留 LLM 输出，只做最小安全检查。

最小安全闸门：禁止 import/依赖新增、禁止方法签名/类结构修改、禁止直接完成任务本身。

生成新的 Benchmark：在原条目中新增 rc_context，落盘后形成“引入 RC 的 benchmark”。

3. 输出格式
在每条样例的 JSON 中新增：
"rc_context": {
  "hunks": [
    {
      "path": "<relative/path/to/File.java>",
      "type": "same_file" | "neighbor",
      "overlap": true | false,
      "nearby": true | false,
      "mini_diff": "<unified mini diff with ONE @@ block>",
      "after": "<after-side ±3 行文本>"
    }
  ],
  "notes": "<可选，简短说明>"
}

并额外生成：

rc_preview.md：以可读 diff 形式展示。

gen_log：记录模型参数、过滤/丢弃原因。

4. LLM 自动合成的模板：见根目录下面的 RC生成Prompt.txt
密钥和模型信息模板：

Model: gpt-4o
api_key: sk-q9fMcdnptLRU2oCLUN8JHORs4VS8rWJVqrwboB5SF8vrAyo8
url:https://api2.aigcbest.top/v1/chat/completions

1 curl https://api2.aigcbest.top/v1/chat/completions \
2   -H 'Content-Type: application/json' \
3   -H 'Authorization: Bearer api_key' \
4   -d '{
5   "model": "gpt-4o",
6   "messages": [XXXX],
7   "temperature": 0.7
8 }'





