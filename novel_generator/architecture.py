#novel_generator/architecture.py
# -*- coding: utf-8 -*-
"""
小说总体架构生成（Novel_architecture_generate 及相关辅助函数）
"""
import os
import logging
import asyncio
from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter
from prompts.character_dynamics_prompt import character_dynamics_prompt
from prompts.world_building_prompt import world_building_prompt
from prompts.plot_architecture_prompt import plot_architecture_prompt
from prompt_definitions import create_character_state_prompt
from utils import clear_file_content, save_string_to_txt


async def Novel_architecture_generate(
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
        
    # Step3: 多模型情节架构生成
    plot_arch_result = await generate_multi_model_plot_architecture(
        filepath=filepath,
        interface_format=interface_format,
        api_key=api_key,
        base_url=base_url,
        temperature_plot=temperature_plot,
        max_tokens=max_tokens,
        timeout=timeout,
        topic=topic,
        character_dynamics_result=character_dynamics_result,
        world_building_result=world_building_result
    )

    final_content = (
        "#=== 0) 小说设定 ===\n"
        f"类型：{genre},篇幅：约{number_of_chapters}章（每章至少{word_number}字）\n\n"
#        "#=== 1) 核心剧情 ===\n"
#        f"{topic}\n\n"
        "#=== 1) 主要角色信息 ===\n"
        f"{character_dynamics_result}\n\n"
        "#=== 2) 世界观 ===\n"
        f"{world_building_result}\n\n"
        "#=== 3) 剧情架构 ===\n"
        f"{plot_arch_result}\n"
    )

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    clear_file_content(arch_file)
    save_string_to_txt(final_content, arch_file)
    logging.info("Novel_architecture.txt文件已生成.")


# 异步框架+多线程执行
async def generate_multi_model_plot_architecture(
    filepath: str,
    interface_format: str,
    api_key: str,
    base_url: str,
    temperature_plot: float,
    max_tokens: int,
    timeout: int,
    topic: str,
    character_dynamics_result: str,
    world_building_result: str
) -> str:
    """
    使用多种不同的模型同时并发生成剧情架构，并分别保存到不同文件。
    """
    # 定义要使用的模型配置
    model_configs = [
        {
            "name": "gemini-flash",
            "interface_format": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model_name": "gemini-2.5-flash",
            "api_key": "AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA"
        },
        {
            "name": "gemini-pro",
            "interface_format": "gemini",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model_name": "gemini-2.5-pro",
            "api_key": "AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA"
        },
        {
            "name": "qwen-plus",
            "interface_format": "qwen",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model_name": "qwen-plus",
            "api_key": "sk-1ef165b563f646a482c2a0b589fa9b09",
            "max_tokens":16384
        },
        {
            "name": "doubao",
            "interface_format": "doubao",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model_name": "doubao-seed-1-6-250615",
            "api_key": "141c1a18-56d4-4799-a975-44585266f86c",
            "max_tokens":32768
        }
    ]
    
    # 检查是否已存在最终的plot.txt文件
    final_plot_file = os.path.join(filepath, "plot.txt")
    if os.path.exists(final_plot_file):
        logging.info("最终情节架构文件已存在，跳过多模型生成...")
        with open(final_plot_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    # 为每个模型并发生成情节架构
    plot_results = {}
    logging.info("开始使用多个模型并发生成情节架构...")
    
    # 获取需要生成的模型列表（过滤已存在的文件）
    models_to_generate = []
    for config in model_configs:
        model_name = config["name"]
        plot_file = os.path.join(filepath, f"plot_{model_name}.txt")
        
        # 检查该模型的结果是否已存在
        if os.path.exists(plot_file):
            logging.info(f"{config['name']} 的情节架构已存在，跳过生成...")
            with open(plot_file, "r", encoding="utf-8") as f:
                plot_results[model_name] = f.read().strip()
        else:
            models_to_generate.append(config)
    
    # 如果有需要生成的模型，则开始并发生成
    if models_to_generate:
        try:
            # 使用 asyncio.gather 进行并发处理
            tasks = []
            for config in models_to_generate:
                # 将协程包装为一个 Task 对象 并立即调度执行
                task = asyncio.create_task(
                    _generate_single_plot_async(
                        config,
                        filepath,
                        temperature_plot,
                        max_tokens,
                        timeout,
                        topic,
                        character_dynamics_result,
                        world_building_result
                    )
                )
                tasks.append((config["name"], task))
            
            # 等待所有任务完成
            logging.info(f"并发启动 {len(tasks)} 个模型生成任务...")
            
            # 使用 asyncio.gather 收集结果，并处理异常
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True  # 确保一个任务的错误不会影响其它任务
            )
            
            # 依次存储每个模型的结果到plot_results字典中
            for i, (model_name, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    logging.error(f"{model_name} 生成过程中出现错误: {result}")
                elif result:
                    plot_results[model_name] = result
                    logging.info(f"{model_name} 情节架构生成完成！")
                else:
                    logging.warning(f"{model_name} 情节架构生成失败")
                    
        except Exception as e:
            logging.error(f"并发生成情节架构过程中出现错误: {e}")
    
    # 如果没有任何模型成功生成，返回空字符串
    if not plot_results:
        logging.error("所有模型都未能成功生成情节架构")
        return ""
    
    # 生成模型对比文件，便于用户选择
    comparison_file = os.path.join(filepath, "plot_comparison.txt")
    comparison_content = "=" * 60 + "\n"
    comparison_content += "多模型情节架构生成结果对比\n"
    comparison_content += "=" * 60 + "\n\n"
    
    for i, (model_name, result) in enumerate(plot_results.items(), 1):
        config = next(c for c in model_configs if c["name"] == model_name)
        comparison_content += f"方案 {i}: {config['name']}\n"
        comparison_content += "-" * 40 + "\n"
        comparison_content += result + "\n\n"
    
    comparison_content += "=" * 60 + "\n"
    comparison_content += "使用说明：\n"
    comparison_content += "1. 请仔细阅读上述各个模型生成的情节架构\n"
    comparison_content += "2. 选择您认为最优的方案\n"
    comparison_content += "3. 将选中的内容复制到 plot.txt 文件中\n"
    comparison_content += "4. 重新运行生成流程以继续后续步骤\n"
    comparison_content += "=" * 60 + "\n"
    
    clear_file_content(comparison_file)
    save_string_to_txt(comparison_content, comparison_file)
    
    logging.info(f"多模型情节架构生成完成！已保存 {len(plot_results)} 个版本")
    logging.info(f"对比文件已保存至: {comparison_file}")
    logging.info("请查看对比文件，选择最优方案并手动复制到 plot.txt 文件中")
    
    return ""


async def _generate_single_plot_async(
    config: dict,
    filepath: str,
    temperature_plot: float,
    max_tokens: int,
    timeout: int,
    topic: str,
    character_dynamics_result: str,
    world_building_result: str
) -> str:
    """
    异步生成单个模型的情节架构
    
    Args:
        config: 模型配置
        filepath: 文件路径
        temperature_plot: 温度参数
        max_tokens: 最大token数
        timeout: 超时时间
        topic: 主题
        character_dynamics_result: 角色动力学结果
        world_building_result: 世界观结果
        
    Returns:
        str: 生成的情节架构内容，失败返回空字符串
    """
    model_name = config["name"]
    plot_file = os.path.join(filepath, f"plot_{model_name}.txt")
    
    try:
        logging.info(f"正在使用 {config['name']} 生成情节架构...")
        
        # 创建对应的LLM适配器
        llm_adapter = create_llm_adapter(
            interface_format=config["interface_format"],
            base_url=config["base_url"],
            model_name=config["model_name"],
            api_key=config["api_key"],
            temperature=temperature_plot,
            max_tokens=config.get("max_tokens", max_tokens),  # 使用模型特定的max_tokens或默认值
            timeout=timeout
        )
        
        # 生成情节架构
        prompt_plot = plot_architecture_prompt.format(
            topic=topic.strip(),
            character_dynamics=character_dynamics_result.strip(),
            world_building=world_building_result.strip()
        )
        
        # 在单独的线程中运行同步的LLM调用，避免阻塞事件循环
        loop = asyncio.get_running_loop()
        # 调用 run_in_executor 将同步的LLM调用提交到线程池
        plot_result = await loop.run_in_executor(
            None,  # 使用默认的线程池执行器
            lambda: invoke_with_cleaning(
                llm_adapter, 
                prompt_plot, 
                purpose=f"{config['name']}生成情节架构"
            )
        )
        
        if plot_result.strip():
            # 保存结果到对应文件
            clear_file_content(plot_file)
            save_string_to_txt(plot_result, plot_file)
            return plot_result.strip()
        else:
            return ""
            
    except Exception as e:
        logging.error(f"{config['name']} 生成过程中出现错误: {e}")
        return ""