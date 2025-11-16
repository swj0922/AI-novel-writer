#novel_generator/finalization.py
# -*- coding: utf-8 -*-
"""
定稿章节（finalize_chapter）
"""
import os
import logging
import asyncio
import sys
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
    对章节做最终处理：生成正文摘要、更新角色状态文档。
    """
    chapters_dir = os.path.join(filepath, "chapters")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    # 刚完成的章节正文
    chapter_text = read_file(chapter_file).strip()
    if not chapter_text:
        logging.warning(f"Chapter {novel_number} is empty, cannot finalize.")
        return

    # 创建summary_result文件夹，用于存储章节概括
    summary_result_dir = os.path.join(filepath, "summary_result")
    if not os.path.exists(summary_result_dir):
        os.makedirs(summary_result_dir)
        logging.info(f"创建summary_result文件夹: {summary_result_dir}")

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

        # 对新生成的章节内容，进行总结
        prompt_summary = summary_prompt.format(
            chapter_text=chapter_text
        )
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
        summary_task = loop.run_in_executor(
            executor, invoke_with_cleaning, llm_adapter, prompt_summary, f"第{novel_number}章章节概要生成"
        )
        # 根据新生成的章节内容，更新角色状态
        prompt_char_state = update_character_state_prompt.format(
            chapter_text=chapter_text,
            old_state=old_character_state
        )
        char_state_task = loop.run_in_executor(
            executor, invoke_with_cleaning, llm_adapter, prompt_char_state, f"第{novel_number}章角色状态更新"
        )

        # 使用asyncio.gather()同时运行两个任务，await会等待两个任务都完成后才继续执行
        # 执行完成后，分别得到章节概括和新的角色状态
        new_summary, new_char_state = await asyncio.gather(
            summary_task, char_state_task
        )
        logging.info(f"第 {novel_number} 章章节概括和角色状态更新成功")

    # 等待两个任务（summary_task 和 char_state_task）全部执行完成后，继续执行后续代码
    if not new_char_state.strip():
        print("角色状态更新失败,即将退出终端")
        sys.exit(1)
    if not new_summary.strip():
        print("章节概括生成失败,即将退出终端")
        sys.exit(1)

    # 将章节摘要保存到summary_result文件夹中
    summary_file = os.path.join(summary_result_dir, f"chapter_{novel_number}_summary.txt")
    save_string_to_txt(new_summary, summary_file)
    logging.info(f"第 {novel_number} 章概括已保存到: {summary_file}")
    
    clear_file_content(character_state_file)
    # 将更新后的角色状态内容写入到 character_state.txt 文件中
    save_string_to_txt(new_char_state, character_state_file)
    logging.info(f"第 {novel_number} 章生成结束")
