# -*- coding: utf-8 -*-
"""
角色状态总结模块
用于每五章后对角色的"触发或加深的事件"进行总结
"""

import os
import re
import sys
import logging
from llm_adapters import create_llm_adapter
from novel_generator.common import invoke_with_cleaning
from utils import read_file, save_string_to_txt


def extract_character_events(character_state_content: str) -> str:
    """
    从character_state.txt内容中提取"角色X："格式的角色及其"触发或加深的事件"部分
    只提取[触发或加深的事件]部分，保持原有的文本格式，仅处理"新出场角色："之前的内容
    
    Args:
        character_state_content: character_state.txt的完整内容
    
    Returns:
        提取出的角色事件文本，格式：角色X：角色名 + [触发或加深的事件] + 事件列表
    """
    # 先找到"新出场角色："的位置，只处理之前的内容
    new_character_match = re.search(r'新出场角色：', character_state_content)
    if new_character_match:
        content_to_process = character_state_content[:new_character_match.start()]
    else:
        content_to_process = character_state_content
    
    result_parts = []
    
    # 按"角色X："分割内容
    character_sections = re.split(r'(?=角色[一二三四五六七八九十]：)', content_to_process)
    
    for section in character_sections:
        if not section.strip():
            continue
            
        # 检查是否是"角色X："格式开头
        lines = section.strip().split('\n')
        if not (lines and lines[0].startswith('角色') and '：' in lines[0]):
            continue
            
        # 查找"[触发或加深的事件]"部分
        events_start_idx = -1
        events_end_idx = len(lines)
        
        for i, line in enumerate(lines):
            if '[触发或加深的事件]' in line:
                events_start_idx = i
                break
        
        if events_start_idx == -1:
            continue  # 没找到事件部分，跳过该角色
            
        # 查找下一个"["开头的部分或下一个角色作为结束标志
        for i in range(events_start_idx + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith('[') or line.startswith('角色[一二三四五六七八九十]：'):
                events_end_idx = i
                break
        
        # 提取角色名称和事件部分
        character_header = lines[0]  # 角色X：角色名
        events_section = '\n'.join(lines[events_start_idx:events_end_idx])
        
        # 组合角色事件信息（只包含角色名和事件部分）
        character_info = f"{character_header}\n{events_section}"
        result_parts.append(character_info)
    
    return '\n\n'.join(result_parts)


def summarize_character_events_text(
    character_events_text: str,
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float = 0.6,
    max_tokens: int = 4000,
    timeout: int = 600
) -> str:
    """
    使用大模型对提取的角色事件文本进行总结
    
    Args:
        character_events_text: 提取的角色事件文本
        其他参数：LLM配置参数
    
    Returns:
        总结后的事件文本
    """
    if not character_events_text.strip():
        return character_events_text
        
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
    
    prompt = f"""请对以下角色的[触发或加深的事件]进行总结。

原始内容：
{character_events_text}

请按以下要求进行总结：
1. 对每个角色的[触发或加深的事件]进行总结概况。
2. 可以将多个相关的事件合并概述，也可以简化一个事件的表述。
2. 保持原有的格式：角色X：角色名 + [触发或加深的事件] + 事件列表
3. 每个事件以"- "开头

示例：
原始内容：
角色一：顾清霜
[触发或加深的事件]
- 29岁生日临近，在母亲的最后通牒下（下周六外婆寿宴），内心焦灼绝望，感到被传统、世俗与“完美女儿”标签压得喘不过气，理性与掌控感彻底崩塌。
- 在极度绝望中，回想起陆衍在“旧时光”咖啡馆的温和与洞察力，将其视为打破僵局的“变数”和“救火队员”，决定启用“雇佣协议”寻找假扮男友。
- 面对家族重压和失控的人生，她试图用金钱和契约掌控局面，将陆衍这个“变数”纳入轨道，将“雇佣协议”视为一场绝望的反击。
- 她以律师的严谨拟定“雇佣协议”条款，并在“旧时光”咖啡馆亲自向陆衍提出邀请，要求他假扮男伴出席外婆寿宴，并支付市场价五倍酬金。
- 收到陆衍的回复邮件，他不仅将酬金翻了三倍至十五倍，更提出了包括肢体接触、亲密称谓等在内的“情侣互动”附加条款。这让顾清霜原本的掌控感瞬间崩塌，感到个人底线受到挑战，并开始重新评估陆衍的动机和真实身份，意识到这场“雇佣”已演变为一场博弈，内心涌起一丝不被察觉的好奇。

返回内容：
角色一：顾清霜
[触发或加深的事件]
-在29岁生日与母亲的催婚压力下，顾清霜感到极度绝望，决定雇佣一位假扮男友来应对家族的最后通牒。
-她以严谨的律师身份与陆衍签订“雇佣协议”，但陆衍提出更高酬金和更多“情侣互动”的补充条款，打破了她的掌控感。

请直接返回总结后的内容，保持原有格式："""

    try:
        summarized_text = invoke_with_cleaning(llm_adapter, prompt, purpose="总结角色状态")
        
        if summarized_text and summarized_text.strip():
            # 移除开头和结尾的空白
            return summarized_text.strip()
        else:
            logging.warning("角色事件总结失败，返回原始内容")
            return character_events_text
            
    except Exception as e:
        logging.error(f"总结角色事件时出错: {e}")
        return character_events_text


def update_character_state_file(
    filepath: str,
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    chapter_num: int,
    temperature: float = 0.6,
    max_tokens: int = 4000,
    timeout: int = 600
):
    """
    更新character_state.txt文件，对所有角色的"触发或加深的事件"进行总结
    并保存一份以章节号命名的备份文件
    
    Args:
        filepath: Novel_Output目录路径
        chapter_num: 当前章节号，用于命名备份文件
        其他参数：LLM配置参数
    """
    character_state_file = os.path.join(filepath, "character_state.txt")
    
    if not os.path.exists(character_state_file):
        logging.warning(f"角色状态文件不存在: {character_state_file}")
        return
    
    try:
        # 读取原始角色状态
        original_content = read_file(character_state_file)
        if not original_content.strip():
            logging.warning("角色状态文件为空")
            return
        
        # 提取角色事件文本
        character_events_text = extract_character_events(original_content)
        
        if not character_events_text.strip():
            logging.warning("未找到任何角色事件")
            sys.exit(1)
        
        logging.info("找到角色事件，开始进行总结...")
        
        # 使用大模型进行总结
        summarized_events_text = summarize_character_events_text(
            character_events_text=character_events_text,
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        # 在原内容中替换角色事件部分
        # 对每个角色的[触发或加深的事件]部分进行替换
        updated_content = original_content
        
        # 解析总结概况后的内容，提取每个角色的事件部分
        # 是一个列表，包含多个字符串，每个字符串表示一个角色
        summarized_sections = re.split(r'(?=角色[一二三四五六七八九十]：)', summarized_events_text)
        #print(f"summarized_sections: {summarized_sections}")

        # 遍历每个角色
        for section in summarized_sections:
            # 跳过空的部分
            if not section.strip():
                continue
            
            # 验证是否以"角色X："格式开头
            # 根据换行符\n进行切分
            lines = section.strip().split('\n')
            #print(f"lines: {lines}")
            if not (lines and lines[0].startswith('角色') and '：' in lines[0]):
                continue
                
            # 提取角色名称，例如从"角色一：顾清霜"中提取出"顾清霜"，用于在原文件中定位该角色
            character_name = lines[0].split('：')[1].strip()
            
            # 找到新的事件列表
            events_start = -1
            for i, line in enumerate(lines):
                if '[触发或加深的事件]' in line:
                    # [触发或加深的事件]之后的元素都是具体事件
                    events_start = i + 1
                    break
            
            if events_start == -1:
                continue
                
            # 提取新的事件列表
            new_events_lines = lines[events_start:]
            # 重新加入换行符
            new_events_text = '\n'.join(new_events_lines)
            
            # 在原内容中找到该角色的[触发或加深的事件]部分并替换
            # 使用正则表达式匹配该角色的事件部分，确保保持正确的换行符格式
            character_pattern = rf'(角色[一二三四五六七八九十]：{re.escape(character_name)}.*?\[触发或加深的事件\]\n)(.*?)(?=\n\n角色[一二三四五六七八九十]：|\n\n新出场角色：|$)'
            
            # 执行替换[触发或加深的事件]操作
            if re.search(character_pattern, updated_content, re.DOTALL):
                # 确保新事件内容后面有正确的换行符以保持角色间的分隔
                replacement_text = new_events_text
                if not replacement_text.endswith('\n'):
                    replacement_text += '\n'
                
                updated_content = re.sub(
                    character_pattern,
                    lambda m: m.group(1) + replacement_text,
                    updated_content,
                    flags=re.DOTALL
                )
                logging.info(f"角色 '{character_name}' 的[触发或加深的事件]替换完成")
            else:
                logging.warning(f"未能找到角色 '{character_name}' 的[触发或加深的事件]部分进行替换")
        
        # 保存更新后的内容到原文件
        save_string_to_txt(updated_content, character_state_file)
        logging.info("角色状态文件更新完成")
        
        # 保存一份以章节号命名的备份文件
        backup_filename = f"character_state{chapter_num}.txt"
        backup_file_path = os.path.join(filepath, backup_filename)
        save_string_to_txt(updated_content, backup_file_path)
        logging.info(f"已保存第{chapter_num}章角色状态备份文件: {backup_filename}")
        
    except Exception as e:
        logging.error(f"更新角色状态文件时出错: {e}")


if __name__ == "__main__":
    # 测试代码
    test_content = """角色一：顾清霜
[性格]
- 事业心极强，理性、逻辑性强，情感表达内敛，甚至有些僵硬。
- 对亲密关系抱有戒备，对"真爱"和"承诺"不信任。
[背景与外貌]
- 出生于沪上显赫的法律世家，父母皆为业界翨楚。
- 身材高挑，气质清冷，女，29岁。
[主要角色间关系网]
- 陆衍：假戏真做的欢喜冤家，从雇佣到相爱。
- 顾夫人：母女冲突，爱之深责之切。
[触发或加深的事件]
- 在29岁生日与母亲的催婚压力下，顾清霜感到极度绝望。
- 她以严谨的律师身份与陆衍签订"雇佣协议"。
- 尽管内心挣扎，但面对家族重压她最终妥协。

角色二：陆衍
[性格]
- 表面温和深邃，平易近人又带点神秘感。
- 随性而自由，对生活充满好奇。
[背景与外貌]
- 表面是咖啡店普通服务员，实则为国内顶尖科技公司继承人。
- 外貌清秀，身形修长，男，30岁。
[主要角色间关系网]
- 顾清霜：假戏真做的欢喜冤家，彼此的救赎。
- 顾夫人：价值观冲突，认为他身份不明。
[触发或加深的事件]
- 观察顾清霜多时，洞察其高冷外表下的疲惫自我保护。
- 在合同谈判中凭借精准洞察成功捍卫十五倍酬金。
- 预测顾清霜的反应并成功擕开其坚硬外壳裂缝。

新出场角色：
- 小李：顾清霜的助理。
- 沈佳宜：顾清霜的闺蜜。
"""
    
    # 测试提取功能
    extracted_text = extract_character_events(test_content)
    print("提取的角色事件文本:")
    print(extracted_text)
    
    print("\n" + "="*50)
    print("提取结果分析:")
    print(f"原始文本长度: {len(test_content)} 字符")
    print(f"提取结果长度: {len(extracted_text)} 字符")
    
    # 检查是否包含新出场角色
    if "小李" in extracted_text or "沈佳宜" in extracted_text:
        print("⚠️ 错误：提取结果包含了新出场角色")
    else:
        print("✅ 正确：没有提取新出场角色")
        
    # 检查是否只包含[触发或加深的事件]部分
    if "[性格]" not in extracted_text and "[背景与外貌]" not in extracted_text:
        print("✅ 正确：只提取了[触发或加深的事件]部分")
    else:
        print("⚠️ 错误：提取结果包含了其他部分")
        
    # 检查是否正确提取了主要角色
    if "角色一：顾清霜" in extracted_text and "角色二：陆衍" in extracted_text:
        print("✅ 正确：成功提取了主要角色")
    else:
        print("⚠️ 错误：未能正确提取主要角色")