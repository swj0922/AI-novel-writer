#novel_generator/blueprint.py
# -*- coding: utf-8 -*-
"""
章节目录生成（Novel_directory.txt）
"""
import os
import re
import logging
from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter
from prompt_definitions import chapter_blueprint_prompt, chunked_chapter_blueprint_prompt
from utils import read_file, clear_file_content, save_string_to_txt


def limit_chapter_blueprint(blueprint_text: str, limit_chapters: int = 50) -> str:
    """
    从已有章节目录中只取最近的 limit_chapters 章，限制章节目录的长度，
    以避免在生成章节蓝图时，传递给大语言模型的提示（prompt）过长
    """
    # 捕获每个章节的完整内容，包括章节标题和其后的文本，直到下一个章节的开始
    pattern = r"(第\s*\d+\s*章.*?)(?=第\s*\d+\s*章|$)"
    # 在 blueprint_text（章节蓝图文本）中查找所有符合 pattern 定义的章节
    chapters = re.findall(pattern, blueprint_text, flags=re.DOTALL)
    if not chapters:
        return blueprint_text
    if len(chapters) <= limit_chapters:
        return blueprint_text
    # 如果提取出的章节数量超过了 limit_chapters （默认是50章），它会只保留最近的 limit_chapters 章
    selected = chapters[-limit_chapters:]
    return "\n\n".join(selected).strip()

def Chapter_blueprint_generate(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    number_of_chapters: int,   # 需要生成的总章节数
    max_tokens: int,
    chunk_size: int = 25,      # 每次生成多少章节的目录
    limit_chapters: int = 25,  # 每次生成章节目录时，传入已经生成好的最近25章的目录以供模型参考
    temperature: float = 0.7,
    timeout: int = 300
) -> None:
    """
    函数作用：根据小说架构 ( Novel_architecture.txt 由architecture.py输出) 和用户指定的章节数量，生成详细的章节目录或蓝图。
    若 Novel_directory.txt 已存在且内容非空，则表示可能是之前的部分生成结果；
      解析其中已有的章节数，从下一个章节继续分块生成；
      对于已有章节目录，传入时仅保留最近10章目录，避免prompt过长。
    否则：
      - 若章节数 <= chunk_size，直接一次性生成
      - 若章节数 > chunk_size，进行分块生成
    生成完成后输出至 Novel_directory.txt。
    """
    '''
    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if not os.path.exists(arch_file):
        logging.warning("Novel_architecture.txt not found. Please generate architecture first.")
        return

    architecture_text = read_file(arch_file).strip()'''
    arch_file = os.path.join(filepath, "plot.txt")
    if not os.path.exists(arch_file):
        logging.warning("plot.txt not found. Please generate architecture first.")
        return

    architecture_text = read_file(arch_file).strip()

    if not architecture_text:
        logging.warning("Novel_architecture.txt is empty.")
        return

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    filename_dir = os.path.join(filepath, "Novel_directory.txt")
    # 如果Novel_directory.txt不存在，则创建一个
    if not os.path.exists(filename_dir):
        open(filename_dir, "w", encoding="utf-8").close()

    existing_blueprint = read_file(filename_dir).strip()
    logging.info(f"一共需要生成{number_of_chapters}章, 每次生成{chunk_size}章.")

    # 如果 Novel_directory.txt 文件已存在且包含内容，函数会解析已有的章节数，并从下一个章节开始继续生成，实现断点续写功能
    if existing_blueprint:
        logging.info("识别到已经生成的部分章节目录，将继续生成")
        pattern = r"第\s*(\d+)\s*章"
        existing_chapter_numbers = re.findall(pattern, existing_blueprint)
        existing_chapter_numbers = [int(x) for x in existing_chapter_numbers if x.isdigit()]
        # 当前已生成的最大章节数，如果还没又生成具体章节内容则为0
        max_existing_chap = max(existing_chapter_numbers) if existing_chapter_numbers else 0
        logging.info(f"已经生成了{max_existing_chap}章，将继续生成")
        final_blueprint = existing_blueprint
        # 准备开始生成的章节数
        current_start = max_existing_chap + 1
        while current_start <= number_of_chapters:
            # 一次生成chunk_size个章节的目录
            current_end = min(current_start + chunk_size - 1, number_of_chapters)
            limited_blueprint = limit_chapter_blueprint(final_blueprint, limit_chapters)
            chunk_prompt = chunked_chapter_blueprint_prompt.format(
                novel_architecture=architecture_text,
                chapter_list=limited_blueprint,
                number_of_chapters=number_of_chapters,
                n=current_start,
                m=current_end,
            )
            logging.info(f"生成[{current_start}..{current_end}]章目录")
            chunk_result = invoke_with_cleaning(llm_adapter, chunk_prompt, purpose="分块生成章节目录")
            if not chunk_result.strip():
                logging.warning(f"Chunk generation for chapters [{current_start}..{current_end}] is empty.")
                clear_file_content(filename_dir)
                save_string_to_txt(final_blueprint.strip(), filename_dir)
                return
            final_blueprint += "\n\n" + chunk_result.strip()
            clear_file_content(filename_dir)
            save_string_to_txt(final_blueprint.strip(), filename_dir)
            current_start = current_end + 1

        logging.info("所有的章节目录生成完毕")
        return

    # 如果分块生成章节大小大于总共章节数，则可以一次生成所有章节
    if chunk_size >= number_of_chapters:
        prompt = chapter_blueprint_prompt.format(
            novel_architecture=architecture_text,
            number_of_chapters=number_of_chapters,
        )
        # 生成章节目录
        blueprint_text = invoke_with_cleaning(llm_adapter, prompt, purpose="生成章节目录")
        if not blueprint_text.strip():
            logging.warning("Chapter blueprint generation result is empty.")
            return

        clear_file_content(filename_dir)
        save_string_to_txt(blueprint_text, filename_dir)
        logging.info("Novel_directory.txt (chapter blueprint) has been generated successfully (single-shot).")
        return

    logging.info("Will generate chapter blueprint in chunked mode from scratch.")
    final_blueprint = ""
    current_start = 1
    # 不断生成章节目录，直到达到总章节数量
    while current_start <= number_of_chapters:
        current_end = min(current_start + chunk_size - 1, number_of_chapters)
        limited_blueprint = limit_chapter_blueprint(final_blueprint, limit_chapters)
        chunk_prompt = chunked_chapter_blueprint_prompt.format(
            novel_architecture=architecture_text,
            chapter_list=limited_blueprint,
            number_of_chapters=number_of_chapters,
            n=current_start,
            m=current_end,
        )
        logging.info(f"Generating chapters [{current_start}..{current_end}] in a chunk...")
        chunk_result = invoke_with_cleaning(llm_adapter, chunk_prompt, purpose="分块生成章节目录")
        if not chunk_result.strip():
            logging.warning(f"Chunk generation for chapters [{current_start}..{current_end}] is empty.")
            clear_file_content(filename_dir)
            save_string_to_txt(final_blueprint.strip(), filename_dir)
            return
        if final_blueprint.strip():
            final_blueprint += "\n\n" + chunk_result.strip()
        else:
            final_blueprint = chunk_result.strip()
        clear_file_content(filename_dir)
        save_string_to_txt(final_blueprint.strip(), filename_dir)
        current_start = current_end + 1

    logging.info("Novel_directory.txt 章节目录已经成功生成")
