from utils import read_file
import re
from llm_adapters import create_llm_adapter


def split_novel_directory(chapters_per_file: int):
    """
    根据指定的章节数量切分Novel_directory.txt文件
    :param chapters_per_file: 每个文件包含的章节数量
    """
    # 读取Novel_directory.txt文件
    directory = read_file("./Novel_Output/Novel_directory.txt").strip()
    
    # 按行分割
    lines = directory.split('\n')
    
    # 识别章节边界
    chapters = []
    current_chapter = []
    
    for line in lines:
        # 检查是否是新章节的开始
        if re.match(r'^第\d+章', line):
            # 如果当前章节不为空，将其添加到章节列表中
            if current_chapter:
                chapters.append('\n'.join(current_chapter))
                current_chapter = []
        # 将当前行添加到当前章节中
        current_chapter.append(line)
    
    # 添加最后一个章节
    if current_chapter:
        chapters.append('\n'.join(current_chapter))
    
    # 计算需要创建的文件数量
    total_chapters = len(chapters)
    num_files = (total_chapters + chapters_per_file - 1) // chapters_per_file
    
    # 创建切分后的文件
    for i in range(num_files):
        start_index = i * chapters_per_file
        end_index = min((i + 1) * chapters_per_file, total_chapters)
        
        # 提取章节内容
        chapter_section = chapters[start_index:end_index]
        
        # 写入新文件
        with open(f"./Novel_Output/Novel_directory_part_{i+1}.txt", "w", encoding="utf-8") as f:
            f.write('\n\n'.join(chapter_section))
    
    print(f"已将Novel_directory.txt切分为{num_files}个文件，每个文件包含{chapters_per_file}章。")


def optimize_novel_directory():
    """
    优化前二十章目录
    """
    # 读取前二十章和第二十到第四十章的目录
    directory1 = read_file("./Novel_Output/Novel_directory_part_1.txt").strip()
    directory2 = read_file("./Novel_Output/Novel_directory_part_2.txt").strip()
    
    # 设计prompt
    prompt = f"""你是一位经验丰富的小说编辑，专门负责优化小说目录结构。现在你需要对一部小说的前二十章目录进行专业编辑。
你将收到两个部分的目录内容：
1.  需要优化的前二十章目录：这部分是你需要重点关注和修改的。
2.  后续的第二十到第四十章目录：这部分是为了让你了解故事的整体走向和发展，从而更好地优化前二十章。

你的任务是根据以下要求，对前二十章目录进行优化：
1.  逻辑性：检查章节之间的逻辑关系是否顺畅，确保"衔接要素"能够有效地将章节串联起来，形成连贯的故事线。
2.  节奏感：检查章节之间节奏是否太快，是否可以有补充的故事内容，如果有则在适当位置添加新的章节。

输出要求:
- 仅返回优化后的目录内容
- 直接给出最终结果，无需解释过程
- 保持简洁的纯文本格式
- 不要包含第21-40章的任何内容

前二十章目录(需要优化):
{directory1}

第二十至第四十章目录(参考):
{directory2}"""
    
    # 调用LLM进行优化
    print("正在调用LLM优化前二十章目录...")
    llm = create_llm_adapter(interface_format="gemini",
                            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                            model_name="gemini-2.5-flash",
                            api_key="AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA",
                            max_tokens=65536,
                            temperature=0.1)
    optimized_directory = llm.invoke(prompt)
    print("优化后的目录如下：")
    print(optimized_directory)


if __name__ == "__main__":
    '''
    try:
        split_novel_directory(20)
    except ValueError:
        print("错误: 参数必须是一个整数")
    '''
    optimize_novel_directory()

