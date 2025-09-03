#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型情节架构生成测试脚本

该脚本用于测试新的多模型情节架构生成功能。
它会使用多个不同的AI模型同时生成情节架构，并生成对比文件供用户选择。
"""

import os
import logging
from novel_generator.architecture import Novel_architecture_generate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_model_plot_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def test_multi_model_plot_generation():
    """
    测试多模型情节架构生成功能
    """
    print("=" * 60)
    print("🚀 多模型情节架构生成测试")
    print("=" * 60)
    
    # 测试配置
    test_config = {
        "interface_format": "gemini",  # 主要接口格式（用于角色和世界观生成）
        "api_key": "AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "llm_model": "gemini-2.5-pro",
        "topic": "出身平凡的男生始终倾慕着家境优渥、气质出众的女孩，却因两人之间悬殊的差距，连靠近的机会都寥寥无几，这份心意只能深埋心底。一次偶然的善举，他救助了一位陷入困境的老人，意外获得了足以改写境遇的超能力。凭借这份"馈赠"，他在众多家境优越、条件出众的追求者中脱颖而出，不仅打破了曾经的差距壁垒，更成功打动女孩，赢得了她的青睐。就在两人感情逐渐升温，他以为终于抓住幸福时，超能力却毫无征兆地突然消失。曾经靠超能力搭建的优势瞬间崩塌，他不得不面对一个残酷的问题：失去"外挂"的自己，还能留住这份来之不易的爱情吗？",
        "genre": "都市言情",
        "number_of_chapters": 50,
        "word_number": 1200,
        "filepath": "./Test_Novel_Output",
        "user_guidance": "故事情节要丰富，循序渐进地推进剧情。叙述手法多样化。人物的背景不要一开始就全盘托出，而是要随着剧情的展开逐步揭示。",
        "temperature": 0.7,
        "temperature_plot": 1.3,  # 情节生成使用更高的创造性
        "max_tokens": 65536,
        "timeout": 600
    }
    
    # 创建测试输出目录
    os.makedirs(test_config["filepath"], exist_ok=True)
    
    try:
        print("\n📋 开始生成小说架构（包含多模型情节生成）...")
        
        Novel_architecture_generate(
            interface_format=test_config["interface_format"],
            api_key=test_config["api_key"],
            base_url=test_config["base_url"],
            llm_model=test_config["llm_model"],
            topic=test_config["topic"],
            genre=test_config["genre"],
            number_of_chapters=test_config["number_of_chapters"],
            word_number=test_config["word_number"],
            filepath=test_config["filepath"],
            user_guidance=test_config["user_guidance"],
            temperature=test_config["temperature"],
            temperature_plot=test_config["temperature_plot"],
            max_tokens=test_config["max_tokens"],
            timeout=test_config["timeout"]
        )
        
        print("\n✅ 小说架构生成完成！")
        print("\n📁 生成的文件：")
        
        # 列出生成的文件
        output_files = [
            "character_information.txt",
            "character_state.txt", 
            "world_building.txt",
            "plot_gemini-flash.txt",
            "plot_gemini-pro.txt", 
            "plot_qwen-plus.txt",
            "plot_doubao.txt",
            "plot_comparison.txt",
            "plot_default.txt",
            "Novel_architecture.txt"
        ]
        
        for filename in output_files:
            filepath = os.path.join(test_config["filepath"], filename)
            if os.path.exists(filepath):
                print(f"   ✅ {filename}")
            else:
                print(f"   ❌ {filename} (未生成)")
        
        print("\n" + "=" * 60)
        print("📖 使用说明：")
        print("=" * 60)
        print("1. 打开 plot_comparison.txt 文件查看各模型生成的情节架构对比")
        print("2. 选择您认为最优的版本")
        print("3. 将选中的内容复制到 plot.txt 文件中")
        print("4. 重新运行主生成流程以继续后续步骤")
        print("=" * 60)
        
        # 显示对比文件路径
        comparison_file = os.path.join(test_config["filepath"], "plot_comparison.txt")
        if os.path.exists(comparison_file):
            print(f"\n📋 对比文件位置: {comparison_file}")
        
    except Exception as e:
        logging.error(f"测试过程中出现错误: {e}")
        print(f"\n❌ 测试失败: {e}")

def show_plot_comparison(filepath: str = "./Test_Novel_Output"):
    """
    显示情节架构对比结果
    """
    comparison_file = os.path.join(filepath, "plot_comparison.txt")
    
    if not os.path.exists(comparison_file):
        print("❌ 未找到对比文件，请先运行多模型生成")
        return
    
    print("\n" + "=" * 60)
    print("📖 情节架构对比结果")
    print("=" * 60)
    
    with open(comparison_file, "r", encoding="utf-8") as f:
        content = f.read()
        print(content)

if __name__ == "__main__":
    # 运行测试
    test_multi_model_plot_generation()
    
    # 可选：直接显示对比结果
    input("\n按回车键查看对比结果...")
    show_plot_comparison()