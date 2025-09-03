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
#topic = "男主追求女主，但女主看不起男主，常常在男主面前与男二做亲密动作，男主即伤心又愤怒，却又无可奈何，突然有一天男主获得了超能力，吸引了女主的注意，女主开始追求男主，同时也有其它女生追求男主。反转：女主由于父亲负债被迫与男二在一起"


async def main():
    """
    主函数：演示完整的小说生成流程
    """
    
    # 可以通过以下方式控制监控功能的开启/关闭
    set_monitoring_enabled(True)   # 开启监控
    # set_monitoring_enabled(False)  # 关闭监控

    # ==================== 配置参数 ====================
    interface_format = 'gemini'
    # api_key ="AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA" # 自己的
    # api_key = "AIzaSyBCaevYiLbu8kE5VdPYZA8w8mUCWX9zwZA"  # 购买1
    api_key = "AIzaSyB-AwMVI5PYGihROiUME3DOz7_lkk0Tovw"  # 购买2

    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model_name1 = "gemini-2.5-flash"   # 更新角色和总结角色
    model_name2 = "gemini-2.5-pro"   # 小说架构，章节目录和章节正文
    
    # 生成参数
    temperature1 = 0.7     # 小说架构和章节内容
    temperature2 = 0.1     # 章节目录、更新角色状态和总结角色状态
    temperature3 = 1.3     # 单独控制小说剧情
    max_tokens = 65536            # gemini最大输出token
    timeout = 600


    # 小说基本设置
    topic = "出身平凡的男生始终倾慕着家境优渥、气质出众的女孩，却因两人之间悬殊的差距，连靠近的机会都寥寥无几，这份心意只能深埋心底。一次偶然的善举，他救助了一位陷入困境的老人，意外获得了足以改写境遇的超能力。凭借这份 “馈赠”，他在众多家境优越、条件出众的追求者中脱颖而出，不仅打破了曾经的差距壁垒，更成功打动女孩，赢得了她的青睐。就在两人感情逐渐升温，他以为终于抓住幸福时，超能力却毫无征兆地突然消失。曾经靠超能力搭建的优势瞬间崩塌，他不得不面对一个残酷的问题：失去 “外挂” 的自己，还能留住这份来之不易的爱情吗？"
    # topic = "女主曾是家境优渥的千金，却因家族企业破产而跌入谷底。她不得不从零开始，进入职场，与男主，一位曾经被她看不起的普通职员，再次相遇。男主默默帮助她，女主也凭借自己的努力和智慧，一步步重振家族。"
    genre = "都市言情"
    number_of_chapters = 100       # 总章节数
    word_number = 1200             # 每章字数（小说要求每章至少1200字）
    chunk_size = 25                # 章节目录生成时，每次生成多少章节
    limit_chapters = 25            # 每次生成章节时，提供多少章已经生成好的章节信息

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
            llm_model=model_name2,
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            filepath=filepath,
            user_guidance=user_guidance,
            temperature=temperature1,
            temperature_plot=temperature3,
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
            chunk_size=chunk_size,
            limit_chapters=limit_chapters,
            timeout=timeout
        )
        print("✅ 章节蓝图生成完成！")
        '''

        # 第三步：逐章生成内容
        print("\n✍️ 第三步：开始生成章节内容...")
        for chapter_num in range(31, number_of_chapters + 1):
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