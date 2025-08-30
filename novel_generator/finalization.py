#novel_generator/finalization.py
# -*- coding: utf-8 -*-
"""
定稿章节和扩写章节（finalize_chapter、enrich_chapter_text）
"""
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from llm_adapters import create_llm_adapter
from prompt_definitions import summary_prompt, update_character_state_prompt
from novel_generator.common import invoke_with_cleaning
from utils import read_file, clear_file_content, save_string_to_txt


async def finalize_chapter(
    novel_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    filepath: str,
    interface_format: str,
    max_tokens: int,
    timeout: int = 600
):
    """
    对指定章节做最终处理：更新前文摘要、更新角色状态、插入向量库等。
    默认无需再做扩写操作，若有需要可在外部调用 enrich_chapter_text 处理后再定稿。
    """
    chapters_dir = os.path.join(filepath, "chapters")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    chapter_text = read_file(chapter_file).strip()
    if not chapter_text:
        logging.warning(f"Chapter {novel_number} is empty, cannot finalize.")
        return

    '''
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    old_global_summary = read_file(global_summary_file)
    '''
    character_state_file = os.path.join(filepath, "character_state.txt")
    old_character_state = read_file(character_state_file)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    # 使用ThreadPoolExecutor创建一个线程池，with语句确保线程池在使用完毕后会自动关闭，释放资源
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()

        # 根据新生成的章节内容，更新前文章节摘要
        '''
        prompt_summary = summary_prompt.format(
            chapter_text=chapter_text,
            global_summary=old_global_summary
        )
        '''
        # run_in_executor用于在异步程序中执行同步函数，避免同步操作阻塞事件循环
        # 接收三个主要参数：
        # executor：指定线程池（如 ThreadPoolExecutor），若为 None 则使用默认线程池
        # func：需要执行的同步函数（不能是协程）
        # *args：传递给同步函数的参数
        # 执行流程：
        # 把 func(*args) 这个同步任务提交到指定的线程池
        # 立即返回一个 Future 对象（可等待对象），代表这个任务的结果
        # 同步函数在线程池的某个线程中异步执行（不阻塞事件循环）
        # 当同步函数执行完成后，Future 对象会被标记为完成，并携带返回结果
        '''
        summary_task = loop.run_in_executor(
            executor, invoke_with_cleaning, llm_adapter, prompt_summary
        )'''

        # 根据新生成的章节内容，更新角色状态
        prompt_char_state = update_character_state_prompt.format(
            chapter_text=chapter_text,
            old_state=old_character_state
        )
        char_state_task = loop.run_in_executor(
            executor, invoke_with_cleaning, llm_adapter, prompt_char_state
        )

        # 使用asyncio.gather()同时运行两个任务，await会等待两个任务都完成后才继续执行
        # 执行完成后，分别得到新的全局摘要和新的角色状态
        '''new_global_summary, new_char_state = await asyncio.gather(
            summary_task, char_state_task
        )'''
        new_char_state_list = await asyncio.gather(char_state_task)
        new_char_state = new_char_state_list[0]  # 从列表中取出第一个元素
        logging.info(f"第 {novel_number} 章全局摘要和角色状态更新成功")

    # 等待两个任务（summary_task 和 char_state_task）全部执行完成后，继续执行后续代码
    '''if not new_global_summary.strip():
        new_global_summary = old_global_summary'''
    if not new_char_state.strip():
        new_char_state = old_character_state

    #clear_file_content(global_summary_file)
    # 将更新后的全局摘要内容写入到 global_summary.txt 文件中
    #save_string_to_txt(new_global_summary, global_summary_file)
    clear_file_content(character_state_file)
    # 将更新后的角色状态内容写入到 character_state.txt 文件中
    save_string_to_txt(new_char_state, character_state_file)
    logging.info(f"第 {novel_number} 章生成结束")

def enrich_chapter_text(
    chapter_text: str,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    interface_format: str,
    max_tokens: int,
    timeout: int=600
) -> str:
    """
    对章节文本进行扩写，使其更接近 word_number 字数，保持剧情连贯。
    """
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
    prompt = f"""以下章节文本较短，请在保持剧情连贯的前提下进行扩写，使其更充实，接近 {word_number} 字左右：
原内容：
{chapter_text}
"""
    enriched_text = invoke_with_cleaning(llm_adapter, prompt, purpose="扩写章节内容")
    return enriched_text if enriched_text else chapter_text
