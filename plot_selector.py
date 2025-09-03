#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情节架构选择工具

该工具帮助用户浏览和选择多模型生成的情节架构，
并自动将选择的结果保存到 plot.txt 文件中。
"""

import os
import logging
from typing import Dict, List

def load_plot_results(filepath: str) -> Dict[str, str]:
    """
    加载所有模型生成的情节架构结果
    
    Args:
        filepath: 输出目录路径
        
    Returns:
        Dict[str, str]: 模型名称到结果内容的映射
    """
    plot_results = {}
    
    # 定义模型配置
    model_configs = [
        {"name": "gemini-flash", "display_name": "Gemini Flash"},
        {"name": "gemini-pro", "display_name": "Gemini Pro"},
        {"name": "qwen-plus", "display_name": "Qwen Plus"},
        {"name": "doubao", "display_name": "Doubao"}
    ]
    
    for config in model_configs:
        model_name = config["name"]
        plot_file = os.path.join(filepath, f"plot_{model_name}.txt")
        
        if os.path.exists(plot_file):
            try:
                with open(plot_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        plot_results[model_name] = {
                            "content": content,
                            "display_name": config["display_name"]
                        }
            except Exception as e:
                logging.warning(f"读取 {plot_file} 时出错: {e}")
    
    return plot_results

def display_plot_options(plot_results: Dict[str, str]) -> None:
    """
    显示所有可选的情节架构
    
    Args:
        plot_results: 模型结果映射
    """
    print("\n" + "=" * 80)
    print("📖 可选的情节架构方案")
    print("=" * 80)
    
    for i, (model_name, result_info) in enumerate(plot_results.items(), 1):
        print(f"\n【方案 {i}】{result_info['display_name']} ({model_name})")
        print("-" * 60)
        
        # 显示内容预览（前300字符）
        content = result_info['content']
        preview = content[:300] + "..." if len(content) > 300 else content
        print(preview)
        print("-" * 60)

def get_user_choice(plot_results: Dict[str, str]) -> str:
    """
    获取用户选择
    
    Args:
        plot_results: 模型结果映射
        
    Returns:
        str: 选择的模型名称
    """
    model_list = list(plot_results.keys())
    
    while True:
        try:
            print(f"\n请选择您偏好的方案 (1-{len(model_list)}):")
            for i, (model_name, result_info) in enumerate(plot_results.items(), 1):
                print(f"  {i}. {result_info['display_name']}")
            
            choice = input("\n请输入选择的序号: ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(model_list):
                    selected_model = model_list[choice_num - 1]
                    print(f"\n✅ 您选择了: {plot_results[selected_model]['display_name']}")
                    return selected_model
            
            print("❌ 无效选择，请输入正确的序号")
            
        except KeyboardInterrupt:
            print("\n\n❌ 用户取消选择")
            return ""
        except Exception as e:
            print(f"❌ 输入错误: {e}")

def save_selected_plot(filepath: str, selected_model: str, plot_results: Dict[str, str]) -> bool:
    """
    保存用户选择的情节架构到 plot.txt
    
    Args:
        filepath: 输出目录路径
        selected_model: 选择的模型名称
        plot_results: 模型结果映射
        
    Returns:
        bool: 保存是否成功
    """
    try:
        selected_content = plot_results[selected_model]['content']
        plot_file = os.path.join(filepath, "plot.txt")
        
        with open(plot_file, "w", encoding="utf-8") as f:
            f.write(selected_content)
        
        print(f"\n✅ 已将 {plot_results[selected_model]['display_name']} 的结果保存到 plot.txt")
        print(f"📁 文件位置: {plot_file}")
        return True
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def create_backup(filepath: str, selected_model: str, plot_results: Dict[str, str]) -> None:
    """
    创建选择记录备份
    
    Args:
        filepath: 输出目录路径
        selected_model: 选择的模型名称
        plot_results: 模型结果映射
    """
    try:
        backup_file = os.path.join(filepath, "plot_selection_log.txt")
        
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("情节架构选择记录\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"选择时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"选择的模型: {plot_results[selected_model]['display_name']} ({selected_model})\n\n")
            f.write("选择的内容:\n")
            f.write("-" * 40 + "\n")
            f.write(plot_results[selected_model]['content'])
            f.write("\n" + "-" * 40 + "\n")
        
        print(f"📋 选择记录已保存到: {backup_file}")
        
    except Exception as e:
        print(f"⚠️ 备份创建失败: {e}")

def main():
    """
    主函数
    """
    print("=" * 80)
    print("🎯 情节架构选择工具")
    print("=" * 80)
    
    # 默认路径，可以通过命令行参数修改
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "./Novel_Output"  # 默认使用正式输出目录
    
    if not os.path.exists(filepath):
        print(f"❌ 输出目录不存在: {filepath}")
        return
    
    # 加载情节架构结果
    print(f"📁 正在从 {filepath} 加载情节架构结果...")
    plot_results = load_plot_results(filepath)
    
    if not plot_results:
        print("❌ 未找到任何情节架构文件")
        print("请先运行多模型生成功能")
        return
    
    print(f"✅ 找到 {len(plot_results)} 个情节架构方案")
    
    # 显示选项
    display_plot_options(plot_results)
    
    # 获取用户选择
    selected_model = get_user_choice(plot_results)
    
    if not selected_model:
        print("❌ 未选择任何方案，退出")
        return
    
    # 保存选择的结果
    if save_selected_plot(filepath, selected_model, plot_results):
        # 创建备份记录
        create_backup(filepath, selected_model, plot_results)
        
        print("\n" + "=" * 80)
        print("🎉 选择完成！")
        print("=" * 80)
        print("您现在可以继续运行小说生成流程的后续步骤")
        print("主流程将使用您选择的情节架构继续生成章节内容")
        print("=" * 80)
    else:
        print("❌ 保存失败，请重试")

if __name__ == "__main__":
    main()