#novel_generator/architecture.py
# -*- coding: utf-8 -*-
"""
小说总体架构生成（Novel_architecture_generate 及相关辅助函数）
"""
import os
import logging
from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter
from prompts.character_dynamics_prompt import character_dynamics_prompt
from prompts.world_building_prompt import world_building_prompt
from prompts.plot_architecture_prompt import plot_architecture_prompt
from prompt_definitions import create_character_state_prompt, reverse_plot_prompt
from utils import clear_file_content, save_string_to_txt


def Novel_architecture_generate(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    topic: str,    # 主题
    genre: str,    # 类型
    number_of_chapters: int,    # 章节数
    word_number: int,    # 每章字数
    filepath: str,
    user_guidance: str = "",  
    temperature: float = 0.8,
    temperature_plot: float = 1.3,
    max_tokens: int = 1000000,
    timeout: int = 600
) -> None:
    """
    依次调用:
      1. character_dynamics_prompt
      2. world_building_prompt
      3. plot_architecture_prompt
    若在中间任何一步报错且重试多次失败，则将已经生成的内容写入 partial_architecture.json 并退出；
    下次调用时可从该步骤继续。
    最终输出 Novel_architecture.txt

    新增：
    - 在完成角色动力学设定后，依据该角色体系，使用 create_character_state_prompt 生成初始角色状态表，
      并存储到 character_state.txt，后续维护更新。
    """
    os.makedirs(filepath, exist_ok=True)
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    # Step1: 角色动力学
    character_information_file = os.path.join(filepath, "character_information.txt")
    if not os.path.exists(character_information_file):
        logging.info("Step1: 开始生成角色信息...")
        prompt_character = character_dynamics_prompt.format(
            topic=topic.strip(),
        )
        character_dynamics_result = invoke_with_cleaning(llm_adapter, prompt_character, purpose="生成角色信息")
        if not character_dynamics_result.strip():
            logging.warning("角色信息生成失败")
            return
        clear_file_content(character_information_file)
        save_string_to_txt(character_dynamics_result, character_information_file)
    else:
        logging.info("角色信息文件已存在，跳过生成...")
        # 从已存在的文件中读取内容
        with open(character_information_file, "r", encoding="utf-8") as f:
            character_dynamics_result = f.read().strip()
    # 生成初始角色状态
    character_state_file = os.path.join(filepath, "character_state.txt")
    if not os.path.exists(character_state_file):
        logging.info("开始根据角色信息生成角色初始状态...")
        prompt_char_state_init = create_character_state_prompt.format(
            character_dynamics=character_dynamics_result.strip()
        )
        character_state_init = invoke_with_cleaning(llm_adapter, prompt_char_state_init, purpose="初始化角色状态")
        if not character_state_init.strip():
            logging.warning("角色初始状态生成失败")
            return
        clear_file_content(character_state_file)
        save_string_to_txt(character_state_init, character_state_file)
        logging.info("角色初始状态生成完毕")
    elif os.path.exists(character_state_file):
        logging.info("角色状态文件已存在，跳过生成...")
        # 从已存在的文件中读取内容
        with open(character_state_file, "r", encoding="utf-8") as f:
            character_state_init = f.read().strip()

    # Step2: 世界观
    world_building_file = os.path.join(filepath, "world_building.txt")
    if not os.path.exists(world_building_file):
        logging.info("Step2: 开始生成世界观...")
        prompt_world = world_building_prompt.format(
            topic=topic.strip(),
            user_guidance=user_guidance,  
            character_dynamics_result=character_dynamics_result.strip()
        )
        world_building_result = invoke_with_cleaning(llm_adapter, prompt_world, purpose="生成世界观")
        if not world_building_result.strip():
            logging.warning("世界观生成失败")
            return
        clear_file_content(world_building_file)
        save_string_to_txt(world_building_result, world_building_file)
    else:
        logging.info("世界观已经存在，跳过生成...")
        # 从已存在的文件中读取内容
        with open(world_building_file, "r", encoding="utf-8") as f:
            world_building_result = f.read().strip()
        
    # Step3: 情节架构
    plot_llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature_plot,
        max_tokens=max_tokens,
        timeout=timeout
    )

    plot_file = os.path.join(filepath, "plot.txt")
    if not os.path.exists(plot_file):
        logging.info("Step3: 开始生成情节架构...")
        prompt_plot = plot_architecture_prompt.format(
            topic=topic.strip(),
            character_dynamics=character_dynamics_result.strip(),
            world_building=world_building_result.strip() 
        )
        plot_arch_result = invoke_with_cleaning(plot_llm_adapter, prompt_plot, purpose="生成情节架构")
        if not plot_arch_result.strip():
            logging.warning("情节架构生成失败")
            return
        clear_file_content(plot_file)
        save_string_to_txt(plot_arch_result, plot_file)
    else:
        logging.info("情节架构已经存在，跳过生成...")
        # 从已存在的文件中读取内容
        with open(world_building_file, "r", encoding="utf-8") as f:
            plot_arch_result = f.read().strip()

    '''
    # Step4： 为情节添加反转元素
    reverse_prompt = reverse_plot_prompt.format(
        plot=plot_arch_result.strip(),
    )
    reverse_plot = invoke_with_cleaning(llm_adapter, prompt=reverse_prompt, purpose="添加反转元素")
    save_string_to_txt(reverse_plot, plot_file)
    '''

    final_content = (
        "#=== 0) 小说设定 ===\n"
        f"类型：{genre},篇幅：约{number_of_chapters}章（每章{word_number}字）\n\n"
        "#=== 1) 核心剧情 ===\n"
        f"{topic}\n\n"
        "#=== 2) 角色信息 ===\n"
        f"{character_dynamics_result}\n\n"
        "#=== 3) 世界观 ===\n"
        f"{world_building_result}\n\n"
        "#=== 4) 剧情架构 ===\n"
        f"{plot_arch_result}\n"
    )

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    clear_file_content(arch_file)
    save_string_to_txt(final_content, arch_file)
    logging.info("Novel_architecture.txt文件已生成.")