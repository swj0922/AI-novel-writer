# -*- coding: utf-8 -*-
"""
Prompt Agent - 基于指定主题改写prompt的智能代理
能够根据用户指定的小说主题，利用大模型对prompt_definitions.py中的prompt进行主题化改写
"""

import sys
import os
from typing import Dict

# 添加父目录到路径中以便导入prompt_definitions和llm_adapters
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt_definitions import *
from llm_adapters import create_llm_adapter

class PromptAgent:
    """
    Prompt改写代理类
    负责根据用户指定的主题，利用大模型对现有prompt进行改写，使其更适合特定的小说类型
    """
    
    def __init__(self, 
                 interface_format: str = "qwen",
                 api_key: str = "sk-1ef165b563f646a482c2a0b589fa9b09",
                 base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model_name: str = "qwen-plus",
                 temperature: float = 0.7,
                 max_tokens: int = 32768,
                 timeout: int = 600):
        """初始化PromptAgent
        
        Args:
            interface_format: 接口格式，默认为"qwen"
            api_key: API密钥
            base_url: API基础URL
            model_name: 模型名称
            temperature: 温度参数，控制生成随机性
            max_tokens: 最大token数
            timeout: 超时时间（秒）
        """
        # 获取所有可用的prompt
        self.available_prompts = self._get_available_prompts()
        
        # 初始化大模型适配器
        self.llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
    
    def _get_available_prompts(self) -> Dict[str, str]:
        """获取所有可用的prompt"""
        prompts = {}
        # 从 prompt_definitions 模块中获取所有以 _prompt 结尾的变量
        # dir(prompt_definitions)返回prompt_definitions中所有变量名
        for name in dir(prompt_definitions):
            if name.endswith('_prompt'):
                prompts[name] = getattr(prompt_definitions, name)
        return prompts
    
    def list_available_prompts(self) -> list:
        """列出所有可用的prompt名称"""
        return list(self.available_prompts.keys())
    
    def rewrite_prompt(self, prompt_name: str, theme: str
    ) -> str:
        """
        根据指定主题使用大模型改写prompt
        
        Args:
            prompt_name: 要改写的prompt名称
            theme: 目标主题（如"都市言情"）
            
        Returns:
            改写后的prompt文本
            
        Raises:
            ValueError: 当prompt_name不存在时
        """
        if prompt_name not in self.available_prompts:
            raise ValueError(f"Prompt '{prompt_name}' 不存在。可用的prompt: {self.list_available_prompts()}")
        
        # 获取原始prompt
        original_prompt = self.available_prompts[prompt_name]
        
        # 构建改写指令
        rewrite_instruction = self._build_rewrite_instruction(original_prompt, theme)
        
        # 使用大模型执行改写
        try:
            rewritten_prompt = self.llm_adapter.invoke(rewrite_instruction)
            return rewritten_prompt
        except Exception as e:
            raise RuntimeError(f"大模型改写失败: {str(e)}")
    
    def _build_rewrite_instruction(self, original_prompt: str, theme: str) -> str:
        """
        构建发送给大模型的改写指令
        
        Args:
            original_prompt: 原始prompt文本
            theme: 目标主题
            
        Returns:
            完整的改写指令
        """
        
        instruction = f"""你是一个专业的prompt改写专家，请根据指定的小说主题对以下原始prompt进行改写。

【小说主题】
{theme}


【原始prompt】
{original_prompt}


【改写要求】
1. 针对「{theme}」主题对原始prompt进行优化改写，使其更适合该类型小说的创作
2. 保持原有的格式要求，不要修改原始prompt {{}} 中的内容

请直接输出改写后的prompt内容，不要包含任何解释或说明
"""

        return instruction
    
    def get_rewritten_prompt_as_variable(self, prompt_name: str, rewritten_prompt: str) -> str:


        """
        获取改写后的prompt作为Python变量定义
        
        Args:
            rewritten_prompt: 改写好的prompt
            
        Returns:
            Python变量定义字符串
        """
        variable_definition = f'{prompt_name} = """{rewritten_prompt}"""'
        
        return variable_definition


# 使用示例和测试函数
def demo_usage():
    """演示PromptAgent的使用方法"""
    
    # 创建代理实例
    agent = PromptAgent(
        interface_format="gemini",
        model_name="gemini-2.5-flash",
        temperature=0.7,
        max_tokens=65536,
        api_key="AIzaSyD36taFUaT7sv0iKwzLyuFeqZiZPoQtSnA",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    # 列出可用的prompt和主题
    print("\n可用的prompt:")
    for prompt in agent.list_available_prompts():
        print(f"  - {prompt}")
    
    # 改写示例
    print("\n=== 大模型改写示例 ===")
    try:
        print("正在改写plot_architecture_prompt...")
        rewritten = agent.rewrite_prompt('plot_architecture_prompt', '都市言情')
        print(f"\n改写后的plot_architecture_prompt:\n{rewritten}")

        # 生成变量定义
        variable_def = agent.get_rewritten_prompt_as_variable('plot_architecture_prompt', rewritten)

        # 建立一个文件夹用于存放修改的prompt
        os.makedirs('D:/桌面/学习资料/项目/小说/prompts', exist_ok=True)
        # 如果已经存在该文件，则会覆盖原有内容
        with open('D:/桌面/学习资料/项目/小说/prompts/plot_architecture_prompt.py', 'w', encoding='utf-8') as f:
            f.write(variable_def)

        print("正在改写world_building_prompt...")
        rewritten = agent.rewrite_prompt('world_building_prompt', '都市言情')
        print(f"\n改写后的world_building_prompt:\n{rewritten}")

        # 生成变量定义
        variable_def = agent.get_rewritten_prompt_as_variable('world_building_prompt', rewritten)

        # 如果已经存在该文件，则会覆盖原有内容
        with open('D:/桌面/学习资料/项目/小说/prompts/world_building_prompt.py', 'w', encoding='utf-8') as f:
            f.write(variable_def)

        print("正在改写character_dynamics_prompt...")
        rewritten = agent.rewrite_prompt('character_dynamics_prompt', '都市言情')
        print(f"\n改写后的character_dynamics_prompt:\n{rewritten}")

        # 生成变量定义
        variable_def = agent.get_rewritten_prompt_as_variable('character_dynamics_prompt', rewritten)

        # 如果已经存在该文件，则会覆盖原有内容
        with open('D:/桌面/学习资料/项目/小说/prompts/character_dynamics_prompt.py', 'w', encoding='utf-8') as f:
            f.write(variable_def)

        print("正在改写core_seed_prompt...")
        rewritten = agent.rewrite_prompt('core_seed_prompt', '都市言情')
        print(f"\n改写后的core_seed_prompt:\n{rewritten}")

        # 生成变量定义
        variable_def = agent.get_rewritten_prompt_as_variable('core_seed_prompt', rewritten)

        # 如果已经存在该文件，则会覆盖原有内容
        with open('D:/桌面/学习资料/项目/小说/prompts/core_seed_prompt.py', 'w', encoding='utf-8') as f:
            f.write(variable_def)

       
    except Exception as e:
        print(f"改写失败: {e}")


if __name__ == "__main__":
    demo_usage()