# novel_generator/chapter.py
# -*- coding: utf-8 -*-
"""
章节草稿生成及获取历史章节文本、当前章节摘要等
"""
import os
import logging
from llm_adapters import create_llm_adapter
from prompt_definitions import (
    first_chapter_draft_prompt, 
    next_chapter_draft_prompt, 
    summarize_recent_chapters_prompt,
)
from chapter_directory_parser import get_chapter_info_from_blueprint
from novel_generator.common import invoke_with_cleaning
from utils import read_file, clear_file_content, save_string_to_txt


def get_last_n_chapters_text(chapters_dir: str, current_chapter_num: int, n: int = 1) -> list:
    """
    从目录 chapters_dir 中获取最近 n 章的文本内容，返回文本列表。
    """
    texts = []
    start_chap = max(1, current_chapter_num - n)
    for c in range(start_chap, current_chapter_num):
        chap_file = os.path.join(chapters_dir, f"chapter_{c}.txt")
        if os.path.exists(chap_file):
            text = read_file(chap_file).strip()
            texts.append(text)
        else:
            texts.append("")
    return texts

def summarize_recent_chapters(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    chapters_text_list: list,     # 最近1章的文本内容，1对应get_last_n_chapters_text中的参数n
    novel_number: int,            # 当前正在处理的章节编号    
    chapter_info: dict,           # 当前章节信息
    next_chapter_info: dict,      # 下一章信息
    timeout: int = 600
) -> str:  
    """
    根据前一章内容生成当前章节的摘要。
    如果解析失败，则返回空字符串。
    """
    try:    
        # 最近一章内容
        combined_text = "\n".join(chapters_text_list).strip()
        if not combined_text:
            return ""
            
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        # 确保所有参数都有默认值
        chapter_info = chapter_info or {}
        next_chapter_info = next_chapter_info or {}
        
        prompt = summarize_recent_chapters_prompt.format(
            combined_text=combined_text,  # 最近一章完整内容
            novel_number=novel_number,
            chapter_title=chapter_info.get("chapter_title", "未命名"),
            chapter_role=chapter_info.get("chapter_role", "常规章节"),
            chapter_purpose=chapter_info.get("chapter_purpose", "内容推进"),
            suspense_level=chapter_info.get("suspense_level", "中等"),
            chapter_summary=chapter_info.get("chapter_summary", ""),
            next_chapter_number=novel_number + 1,
            next_chapter_title=next_chapter_info.get("chapter_title", "（未命名）"),
            next_chapter_role=next_chapter_info.get("chapter_role", "过渡章节"),
            next_chapter_purpose=next_chapter_info.get("chapter_purpose", "承上启下"),
            next_chapter_summary=next_chapter_info.get("chapter_summary", "衔接过渡内容"),
            next_chapter_suspense_level=next_chapter_info.get("suspense_level", "中等"),
        )
        
        response_text = invoke_with_cleaning(llm_adapter, prompt, purpose="生成章节摘要")
        summary = extract_summary_from_response(response_text)
        
        if not summary:
            logging.warning("章节摘要生成失败")
            return response_text
            
        return summary 
        
    except Exception as e:
        logging.error(f"Error in summarize_recent_chapters: {str(e)}")
        return ""

def extract_summary_from_response(response_text: str) -> str:
    """从响应文本中提取摘要部分"""
    if not response_text:
        return ""
        
    # 查找摘要标记
    summary_markers = [
        "当前章节摘要:", 
        "章节摘要:",
        "摘要:",
        "本章摘要:"
    ]
    
    for marker in summary_markers:
        if (marker in response_text):
            # 以marker为界，分割文本以提取摘要
            parts = response_text.split(marker, 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    return response_text.strip()

def format_chapter_info(chapter_info: dict) -> str:
    """将章节信息字典格式化为文本"""
    template = """
章节编号：第{number}章
章节标题：《{title}》
章节定位：{role}
核心作用：{purpose}
悬念密度：{suspense}
章节简述：{summary}
"""
    return template.format(
        number=chapter_info.get('chapter_number', '未知'),
        title=chapter_info.get('chapter_title', '未知'),
        role=chapter_info.get('chapter_role', '未知'),
        purpose=chapter_info.get('chapter_purpose', '未知'),
        suspense=chapter_info.get('suspense_level', '一般'),
        summary=chapter_info.get('chapter_summary', '未提供')
    )

def build_chapter_prompt(
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    novel_number: int,  # 当前正在处理的章节
    word_number: int, # 每章节字数要求
    temperature: float,
    user_guidance: str,
    interface_format: str,
    max_tokens: int,
    genre: str,  # 题材
    timeout: int
) -> str:
    """
    构造当前章节的请求提示词（完整实现版）
    修改重点：
    1. 优化知识库检索流程
    2. 新增内容重复检测机制
    3. 集成提示词应用规则
    """
    # 读取基础文件
    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    novel_architecture_text = read_file(arch_file)
    directory_file = os.path.join(filepath, "Novel_directory.txt")
    blueprint_text = read_file(directory_file)
    #global_summary_file = os.path.join(filepath, "global_summary.txt")
    #global_summary_text = read_file(global_summary_file)
    character_state_file = os.path.join(filepath, "character_state.txt")
    character_state_text = read_file(character_state_file)
    
    # 获取章节信息（从章节目录中获取具体章节信息）
    chapter_info = get_chapter_info_from_blueprint(blueprint_text, novel_number)
    chapter_title = chapter_info["chapter_title"]
    chapter_role = chapter_info["chapter_role"]
    chapter_purpose = chapter_info["chapter_purpose"]
    suspense_level = chapter_info["suspense_level"]
    connection_elements = chapter_info.get("connection_elements", "")
    chapter_summary = chapter_info["chapter_summary"]

    # 获取下一章节信息
    next_chapter_number = novel_number + 1
    next_chapter_info = get_chapter_info_from_blueprint(blueprint_text, next_chapter_number)
    next_chapter_title = next_chapter_info.get("chapter_title", "（未命名）")
    next_chapter_role = next_chapter_info.get("chapter_role", "过渡章节")
    next_chapter_purpose = next_chapter_info.get("chapter_purpose", "承上启下")
    next_chapter_suspense = next_chapter_info.get("suspense_level", "中等")
    next_connection_elements = next_chapter_info.get("connection_elements", "")
    next_chapter_summary = next_chapter_info.get("chapter_summary", "衔接过渡内容")

    # 创建章节目录
    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    # 第一章特殊处理
    if novel_number == 1:
        return first_chapter_draft_prompt.format(
            novel_number=novel_number,
            word_number=word_number,
            chapter_title=chapter_title,
            chapter_role=chapter_role,
            chapter_purpose=chapter_purpose,
            suspense_level=suspense_level,
            connection_elements=connection_elements,
            chapter_summary=chapter_summary,
            novel_setting=novel_architecture_text,
            next_chapter_number=next_chapter_number,
            next_chapter_title=next_chapter_title,
            next_chapter_role=next_chapter_role,
            next_chapter_purpose=next_chapter_purpose,
            next_chapter_suspense_level=next_chapter_suspense,
            next_connection_elements=next_connection_elements,
            next_chapter_summary=next_chapter_summary,
            genre=genre
        )

    # 获取最近一章内容和摘要
    recent_texts = get_last_n_chapters_text(chapters_dir, novel_number, n=1)
    
    try:
        logging.info("正在生成当前章节的摘要")
        # 当前正在创作章节的初步摘要
        short_summary = summarize_recent_chapters(
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            chapters_text_list=recent_texts,
            novel_number=novel_number,
            chapter_info=chapter_info,
            next_chapter_info=next_chapter_info,
            timeout=timeout
        )
        logging.info("当前章节摘要成功生成")
    except Exception as e:
        logging.error(f"Error in summarize_recent_chapters: {str(e)}")
        short_summary = "（摘要生成失败）"

    previous_excerpt = recent_texts[0]
    # 获取前一章结尾，使用标点符号进行智能截取
    '''
    previous_excerpt = ""
    for text in reversed(recent_texts):
        if text.strip():
            # 定义可以作为截取点的标点符号
            end_punctuations = ['。', '！', '？', '”', '’', '!', '?', '.', '"', "'"]
            
            # 如果文本长度小于等于400字符，直接使用全部内容
            if len(text) <= 400:
                previous_excerpt = text
            else:
                # 从最后400字符开始向前查找合适的标点符号截取点
                start_pos = len(text) - 400
                best_cut_pos = start_pos
                
                # 在这400字符范围内查找最早的标点符号
                for i in range(start_pos, len(text)):
                    if text[i] in end_punctuations:
                        best_cut_pos = i + 1  # 在标点符号后面截取
                        break
                
                # 如果找到了合适的标点符号，从该位置开始截取
                previous_excerpt = text[best_cut_pos:]
                
                # 如果截取后内容太短（少于100字符），则使用原来的截取方法
                if len(previous_excerpt.strip()) < 100:
                    previous_excerpt = text[-400:]
            
            break
        '''
    # 返回最终提示词
    return next_chapter_draft_prompt.format(
        previous_chapter_excerpt=previous_excerpt,
        character_state=character_state_text,
        short_summary=short_summary,
        novel_number=novel_number,
        chapter_title=chapter_title,
        chapter_role=chapter_role,
        chapter_purpose=chapter_purpose,
        suspense_level=suspense_level,
        connection_elements=connection_elements,
        chapter_summary=chapter_summary,
        word_number=word_number,
        next_chapter_number=next_chapter_number,
        next_chapter_title=next_chapter_title,
        next_chapter_role=next_chapter_role,
        next_chapter_purpose=next_chapter_purpose,
        next_chapter_suspense_level=next_chapter_suspense,
        next_connection_elements=next_connection_elements,
        next_chapter_summary=next_chapter_summary,
        genre=genre,
    )
    '''
    return next_chapter_draft_prompt.format(
        user_guidance=user_guidance if user_guidance else "无特殊指导",
        global_summary=global_summary_text,
        previous_chapter_excerpt=previous_excerpt,
        character_state=character_state_text,
        short_summary=short_summary,
        novel_number=novel_number,
        chapter_title=chapter_title,
        chapter_role=chapter_role,
        chapter_purpose=chapter_purpose,
        suspense_level=suspense_level,
        chapter_summary=chapter_summary,
        word_number=word_number,
        next_chapter_number=next_chapter_number,
        next_chapter_title=next_chapter_title,
        next_chapter_role=next_chapter_role,
        next_chapter_purpose=next_chapter_purpose,
        next_chapter_suspense_level=next_chapter_suspense,
        next_chapter_summary=next_chapter_summary,
        genre=genre,
    )
    '''

def generate_chapter_draft(
    api_key: str,
    base_url: str,
    model_name: str, 
    filepath: str,
    novel_number: int,
    word_number: int,
    temperature: float,
    user_guidance: str,
    genre: str, 
    interface_format: str,
    max_tokens: int,
    timeout: int
) -> str:
    """
    生成章节草稿，支持自定义提示词
    """

    prompt_text = build_chapter_prompt(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        filepath=filepath,
        novel_number=novel_number,
        word_number=word_number,
        temperature=temperature,
        user_guidance=user_guidance,
        interface_format=interface_format,
        max_tokens=max_tokens,
        genre = genre,
        timeout=timeout
    )

    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    chapter_content = invoke_with_cleaning(llm_adapter, prompt_text, purpose="生成章节正文")
    if not chapter_content.strip():
        logging.warning("Generated chapter draft is empty.")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    clear_file_content(chapter_file)
    save_string_to_txt(chapter_content, chapter_file)
    logging.info(f"第 {novel_number} 章正文成功生成.")
    return chapter_content
