#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说生成器命令行脚本
"""

import os
import logging
from novel_generator import (
    Novel_architecture_generate,
    Chapter_blueprint_generate,
    generate_chapter_draft,
    finalize_chapter
)
from character_summary import update_character_state_file
from database.config_manager import set_monitoring_enabled

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('novel_generation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# API配置
#interface_format = "qwen"  
#api_key = "sk-1ef165b563f646a482c2a0b589fa9b09" 
#base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"  
#model_name = "qwen3-235b-a22b-thinking-2507"  
# max_tokens = 32768   # qwen3

#interface_format = "doubao"
#api_key = "141c1a18-56d4-4799-a975-44585266f86c"
#base_url = "https://ark.cn-beijing.volces.com/api/v3"
#model_name = "doubao-seed-1-6-flash-250715"
# max_tokens = 32000  # doubao

#topic = """顶流男明星与才华横溢但低调的女编剧因工作相知相惜，发展为隐秘的地下恋情。恋情意外被狗仔曝光，引发轩然大波。男主遭遇粉丝流失、事业重创，女主承受巨大舆论压力濒临崩溃。同为顶流的女二看准时机，试图利用自身资源乘虚而入，介入两人关系。面对事业崩盘和外界诱惑，男女主选择坚守彼此，共同抵抗压力。​​ 两人共同面对舆论，男主转型，女主用实力证明自己，最终走出低谷，事业爱情双丰收。"""
#topic = "顶流男歌手江楠为逃避经纪人安排的炒作，躲进一家花店，遇到了安静的花艺师周晴。两人在花香中相恋，但江楠的前女友——同样是明星的许雅——发现了这段感情，故意泄露给媒体。舆论风暴中，周晴的花店被粉丝围堵，她不堪重负选择离开。江楠在演唱会上公开表白，用一首为周晴写的歌挽回爱情。"
#topic = "高冷女律师为了在家族聚会中摆脱催婚，临时雇佣咖啡店服务员假扮男友。没想到这个看似普通的服务员竟是隐藏身份的科技公司继承人，两人在一次次演戏中假戏真做。"

async def main():
    """
    主函数：演示完整的小说生成流程
    """
    
    # 可以通过以下方式控制监控功能的开启/关闭
    set_monitoring_enabled(True)   # 开启监控
    # set_monitoring_enabled(False)  # 关闭监控

    # ==================== 配置参数 ====================
    interface_format = 'gemini'
    api_key ="AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA"
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model_name1 = "gemini-2.5-flash"   # 小说架构，更新角色和总结角色
    model_name2 = "gemini-2.5-pro"   # 章节目录和章节正文
    

    # 生成参数
    temperature1 = 0.6     # 小说架构和章节内容
    temperature2 = 0.2     # 章节目录、更新角色状态和总结角色状态
    max_tokens = 65536     # gemini最大输出token
    timeout = 600


    # 小说基本设置
    topic = "穷屌丝在与一众高富帅的竞争中脱颖而出，逆袭迎娶白富美的爽文故事"
    genre = "都市言情"
    number_of_chapters = 100  # 总章节数
    word_number = 1100 # 每章字数（小说要求每章至少1100字）
    
    # 用户指导（可选）
    user_guidance = "故事情节要丰富，循序渐进地推进剧情。叙述手法多样化。人物的背景不要一开始就全盘托出，而是要随着剧情的展开逐步揭示。在剧情需要时，可以加入新的角色。"
    
    # 文件保存路径
    filepath = "./Novel_Output"  # 小说输出目录
    
    # ==================== 开始生成流程 ====================
    
    print("=" * 60)
    print("🚀 开始小说生成流程")
    print("=" * 60)
    
    # 创建输出目录
    os.makedirs(filepath, exist_ok=True)
    
    try:
        '''
        # 第一步：生成小说架构
        print("\n📋 第一步：生成小说架构...")
        Novel_architecture_generate(
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            llm_model=model_name1,
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            filepath=filepath,
            user_guidance=user_guidance,
            temperature=temperature1,
            max_tokens=max_tokens,
            timeout=timeout
        )
        print("✅ 小说架构生成完成！")
        
        # 第二步：生成章节蓝图
        print("\n📖 第二步：生成章节蓝图...")
        Chapter_blueprint_generate(
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            llm_model=model_name2,
            filepath=filepath,
            number_of_chapters=number_of_chapters,
            temperature=temperature2,
            max_tokens=max_tokens,
            timeout=timeout
        )
        print("✅ 章节蓝图生成完成！")
        ''' 
        # 第三步：逐章生成内容
        print("\n✍️ 第三步：开始生成章节内容...")
        for chapter_num in range(41, number_of_chapters + 1):
            print(f"\n--- 正在生成第 {chapter_num} 章 ---")

            # 生成章节草稿
            draft_content = generate_chapter_draft(
                api_key=api_key,
                base_url=base_url,
                model_name=model_name2,
                filepath=filepath,
                novel_number=chapter_num,
                word_number=word_number,
                temperature=temperature1,
                user_guidance=user_guidance,
                interface_format=interface_format,
                max_tokens=max_tokens,
                genre=genre,
                timeout=timeout
            )
            
            if draft_content:
                print(f"✅ 第 {chapter_num} 章草稿生成完成！")
                
                # 定稿章节
                print(f"🎯 正在定稿第 {chapter_num} 章...")
                await finalize_chapter(
                    novel_number=chapter_num,
                    api_key=api_key,
                    base_url=base_url,
                    model_name=model_name1,
                    temperature=temperature2,
                    filepath=filepath,
                    interface_format=interface_format,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                print(f"✅ 第 {chapter_num} 章定稿完成！")
                
                # 每五章进行角色状态总结
                if chapter_num % 10 == 0:
                    print(f"\n🔄 正在对前 {chapter_num} 章进行角色状态总结...")
                    try:
                        update_character_state_file(
                            filepath=filepath,
                            interface_format=interface_format,
                            api_key=api_key,
                            base_url=base_url,
                            model_name=model_name1,
                            chapter_num=chapter_num,
                            temperature=temperature2,
                            max_tokens=max_tokens,
                            timeout=timeout
                        )
                        print(f"✅ 第 {chapter_num} 章角色状态总结完成！")
                        break
                        '''
                        # 保存global_summary备份文件
                        print(f"📁 正在保存第 {chapter_num} 章global_summary备份...")
                        try:
                            global_summary_file = os.path.join(filepath, "global_summary.txt")
                            if os.path.exists(global_summary_file):
                                # 读取当前global_summary内容
                                global_summary_content = read_file(global_summary_file)
                                
                                # 保存备份文件
                                backup_filename = f"global_summary{chapter_num}.txt"
                                backup_file_path = os.path.join(filepath, backup_filename)
                                save_string_to_txt(global_summary_content, backup_file_path)
                                print(f"✅ 已保存第{chapter_num}章global_summary备份文件: {backup_filename}")
                            else:
                                print(f"⚠️ global_summary.txt文件不存在，跳过备份")
                        except Exception as backup_error:
                            print(f"⚠️ global_summary备份失败：{str(backup_error)}")
                            logging.error(f"global_summary备份错误：{str(backup_error)}", exc_info=True)
                        '''
                    except Exception as e:
                        print(f"⚠️ 角色状态总结失败：{str(e)}")
                        logging.error(f"角色状态总结错误：{str(e)}", exc_info=True)
            else:
                print(f"❌ 第 {chapter_num} 章生成失败！")
                break
              

        print("\n" + "=" * 60)
        print("🎉 小说生成完成！")
        print(f"📁 输出目录：{os.path.abspath(filepath)}")
        print("=" * 60)
        
        # 显示生成的文件
        print("\n📄 生成的文件：")
        for root, dirs, files in os.walk(filepath):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, filepath)
                print(f"  - {rel_path}")
                
    except Exception as e:
        print(f"❌ 生成过程中出现错误：{str(e)}")
        logging.error(f"生成错误：{str(e)}", exc_info=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())