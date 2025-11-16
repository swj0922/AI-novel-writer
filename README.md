architecture.py
利用大模型根据以下prompt，生成对应结果
      1. core_seed_prompt
      2. character_dynamics_prompt
      3. world_building_prompt
      4. plot_architecture_prompt
将四个结果写入Novel_architecture.txt文件中

根据character_dynamics_prompt生成create_character_state_prompt
将create_character_state_prompt保存至character_state.txt文件中

===============================================================================

blueprint.py
根据Novel_architecture.txt，生成Novel_directory.txt文件，即小说目录
1.如果Novel_directory.txt已经存在，且包含了部分已经生成好的章节目录：
利用chunked_chapter_blueprint_prompt继续生成之后的目录
2.如果Novel_directory.txt为空：
利用chunked_chapter_blueprint_prompt生成目录

chunked_chapter_blueprint_promp中关键元素：
1.已生成的章节目录
2.novel_architecture

关键参数：
1.chunk_size：每次生成多少章节的目录，默认为10
2.limit_chapters：在生成章节目录时，提供已经生成好的最近limit_chapters章节的目录，以供模型参考，默认为50

===============================================================================

chapter.py
利用chapter_directory_parser.py文件中的get_chapter_info_from_blueprint函数
从Novel_directory.txt文件中提取章节的：
1.本章定位
2.核心作用
3.悬念密度
4.本章简述

summarize_recent_chapters函数利用summarize_recent_chapters_prompt根据：
1.前三章的完整内容
2.当前章的目录信息（即上述1，2，3，4）
3.下一章的目录信息
生成当前章节的摘要，目前限制最多400字

build_chapter_prompt函数，返回用于完成章节正文创作的prompt：
1.如果是第一章的创作，则使用first_chapter_draft_prompt：
主要利用：章节目录信息和Novel_architecture.txt
2.如果不是第一章的创作，则使用next_chapter_draft_prompt：
主要利用：global_summary.txt，前一章节的最后400字，
character_state.txt，当前章节摘要，当前章节目录信息和下一章目录信息

generate_chapter_draft函数：
根据build_chapter_prompt函数返回的prompt，利用大模型生成章节正文
将生成的章节正文写入到chapter.txt文件中

===============================================================================

finalization.py
根据新生成的章节内容，利用summary_prompt和update_character_state_prompt
更新前文摘要和角色状态列表
并分别写入到global_summary.txt和character_state.txt文件中

===============================================================================

知识库逻辑
在完成一章节的正文以后，对正文进行分块后存入chromadb向量库
准备写一章时，利用大模型根据章节目录提炼要在向量库搜素的内容，
也就是利用大模型根据章节目录生成一句话，用这句话在向量库中进行相似度检索，从而召回文档
用户辅助生成章节内容。

===============================================================================

生成大概，角色信息等内容，需要调用9次大模型
（4+5次章节目录生成）
第一章生成需要调用3次大模型
（1次正文生成+2次角色状态更新和摘要更新）
之后的每一章需要调用4次大模型
（1次摘要生成+1次正文生成+2次角色状态更新和摘要）

以50章为例：
若全部使用gemini-2.5-pro
总共需要调用：9+3+4*49=208次
若更新角色状态和摘要使用gemini-2.5-flash
总共需要调用：9+1+2*49=108次gemini-2.5-pro
和2*50=100次gemini-2.5-flash
也就是如果从零开始生成小说，最多生成到45章

===============================================================================

续写机制：
在Novel_Output文件夹中的json文件中，
如果没有发现相应内容，则会初始生成。
如果发现相应内容，则会跳过生成。


