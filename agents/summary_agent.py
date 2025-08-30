"""
对每一章节进行总结，方便审查剧情
"""
import os
from langchain_community.document_loaders import DirectoryLoader
from langchain.chains.summarize import load_summarize_chain
from langchain_community.chat_models.tongyi import ChatTongyi

os.environ["DASHSCOPE_API_KEY"] = "sk-1ef165b563f646a482c2a0b589fa9b09"

# 加载chapters文件夹中的所有txt文件
# *.txt 表示匹配所有以 .txt 结尾的文件
loader = DirectoryLoader('D:/桌面/学习资料/项目/小说/Novel_Output/chapters', glob='*.txt')
# 将文本转成 Document 对象
document = loader.load()
print(f'documents:{len(document)}')

# 加载 llm 模型
llm = ChatTongyi(model_name="qwen-flash-2025-07-28", max_tokens=10000)

# 创建总结链
chain = load_summarize_chain(llm, 
                chain_type="map_reduce", 
                return_intermediate_steps=True,  # 是否返回中间过程结果
                )

# 执行总结链(对前十章进行总结)
result = chain.invoke(document[:10])

# 提取每个文档的小结
map_summaries = result["intermediate_steps"]
print("每个文档的小结：")
total_len=0
for i, summary in enumerate(map_summaries):
    print(f"文档{i+1}小结：{summary}")
    total_len+=len(summary)

print(f"每小章summary拼接后总长度：{total_len}")

# 最终合并的总结
print("\n最终总结：", result["output_text"])
