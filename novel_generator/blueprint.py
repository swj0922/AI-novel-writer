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
from prompt_definitions import chapter_blueprint_prompt, chunked_chapter_blueprint_prompt, part_based_chapter_blueprint_prompt
from utils import read_file, clear_file_content, save_string_to_txt


def parse_plot_parts(plot_text: str) -> list:
    """
    从plot.txt文件中解析出各个剧情部分
    返回剧情部分列表，每个元素包含部分标题和内容
    """
    import re
    
    # 使用正则表达式匹配每个部分
    pattern = r'第([一二三四五六七八九十]+)部分：([^\n]+)\n\n(.*?)(?=第[一二三四五六七八九十]+部分：|$)'
    matches = re.findall(pattern, plot_text, re.DOTALL)
    
    parts = []
    for match in matches:
        part_number, part_title, part_content = match
        parts.append({
            'number': part_number,
            'title': part_title.strip(),
            'content': part_content.strip()
        })
    
    return parts


def get_recent_part_chapters(blueprint_text: str, chapters_per_part: int = 15) -> str:
    """
    从已有章节目录中提取最近一个部分的章节目录
    按照章节数量倒推，获取最近生成的一个部分的章节
    """
    if not blueprint_text.strip():
        return ""
    
    # 提取所有章节
    pattern = r"(第\s*\d+\s*章.*?)(?=第\s*\d+\s*章|$)"
    chapters = re.findall(pattern, blueprint_text, flags=re.DOTALL)
    
    if not chapters:
        return ""
    
    # 获取最近的一个部分的章节（按chapters_per_part数量）
    recent_chapters = chapters[-chapters_per_part:] if len(chapters) >= chapters_per_part else chapters
    
    return "\n\n".join(recent_chapters).strip()



def get_plot_context_for_part(parts: list, part_index: int) -> str:
    """
    根据部分索引获取用于生成目录的剧情上下文
    第一部分使用第1和第2部分，第二部分使用第1、2、3部分，依此类推
    最后一部分使用倒数第二部分和最后一部分
    """
    if not parts:
        return ""
    
    total_parts = len(parts)
    
    if part_index == 0:  # 第一部分
        if total_parts >= 2:
            context_parts = parts[0:2]  # 第1和第2部分
        else:
            context_parts = parts[0:1]  # 只有第1部分
    elif part_index == total_parts - 1:  # 最后一部分
        if total_parts >= 2:
            context_parts = parts[-2:]  # 倒数第二部分和最后一部分
        else:
            context_parts = parts[-1:]  # 只有最后一部分
    else:  # 中间部分
        start_idx = max(0, part_index - 1)
        end_idx = min(total_parts, part_index + 2)
        context_parts = parts[start_idx:end_idx]
    
    # 构建上下文文本
    context_text = ""
    for part in context_parts:
        context_text += f"第{part['number']}部分：{part['title']}\n\n{part['content']}\n\n"
    
    return context_text.strip()



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


def Chapter_blueprint_generate_by_parts(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    max_tokens: int,
    min_chapters_per_part: int = 15,  # 每个部分至少生成的章节数（用于提取最近部分章节）
    temperature: float = 0.7,
    timeout: int = 300
) -> None:
    """
    基于plot.txt中的剧情部分来依次生成章节目录
    
    生成规则：
    - 使用第1和第2部分的剧情来创建第一部分的目录
    - 使用第1、2、3部分来创建第二部分的目录
    - 使用第2、3、4部分来创建第三部分的目录
    - 依此类推
    - 使用倒数第二部分和最后一部分来创建最后一部分的目录
    
    优化特性：
    - 只提供最近一个部分已生成的章节目录
    - 每个部分要求生成至少{min_chapters_per_part}章，不指定具体数量
    - 在prompt中明确告知当前是根据第几部分生成目录
    """
    plot_file = os.path.join(filepath, "plot.txt")
    if not os.path.exists(plot_file):
        logging.warning("plot.txt not found. Please generate plot first.")
        return

    plot_text = read_file(plot_file).strip()
    if not plot_text:
        logging.warning("plot.txt is empty.")
        return

    # 解析剧情部分
    plot_parts = parse_plot_parts(plot_text)
    if not plot_parts:
        logging.warning("No plot parts found in plot.txt")
        return

    logging.info(f"Found {len(plot_parts)} plot parts in plot.txt")
    
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
    if not os.path.exists(filename_dir):
        open(filename_dir, "w", encoding="utf-8").close()

    existing_blueprint = read_file(filename_dir).strip()
    final_blueprint = existing_blueprint
    
    # 为每个剧情部分生成章节
    for part_index, part in enumerate(plot_parts):
        logging.info(f"正在为第{part['number']}部分：{part['title']} 生成章节目录")
        
        # 获取这个部分的剧情上下文
        plot_context = get_plot_context_for_part(plot_parts, part_index)
        
        # 获取最近一个部分的已生成章节（仅在非第一部分时）
        recent_chapters = ""
        if part_index > 0:  # 不是第一部分时，提供最近一部分的章节
            recent_chapters = get_recent_part_chapters(final_blueprint, min_chapters_per_part)
        
        # 构建提示词
        part_prompt = part_based_chapter_blueprint_prompt.format(
            plot_context=plot_context,
            current_part_title=part['title'],
            current_part_number=part['number'],
            min_chapters=min_chapters_per_part,
            recent_chapters=recent_chapters if recent_chapters else "无"
        )
        
        logging.info(f"正在生成第{part['number']}部分的章节目录（至少{min_chapters_per_part}章）")
        
        # 调用LLM生成这个部分的章节目录
        part_result = invoke_with_cleaning(
            llm_adapter, 
            part_prompt, 
            purpose=f"第{part['number']}部分章节目录生成"
        )
        
        if not part_result.strip():
            logging.warning(f"Part {part_index + 1} chapter generation result is empty.")
            continue
        
        # 添加到总目录
        if final_blueprint.strip():
            final_blueprint += "\n\n" + part_result.strip()
        else:
            final_blueprint = part_result.strip()
        
        # 保存当前进度
        clear_file_content(filename_dir)
        save_string_to_txt(final_blueprint.strip(), filename_dir)
        
        logging.info(f"第{part['number']}部分章节目录生成完成")
    
    logging.info("基于剧情部分的章节目录生成完成")
