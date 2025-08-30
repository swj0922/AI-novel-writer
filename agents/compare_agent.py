# 第一次比较：plot_prompt2获胜

from utils import read_file
from llm_adapters import llm_gemini_flash, llm_gemini_pro, llm_qwen_plus, llm_doubao
import logging

plot_propmt1 = """
你是一位资深的言情小说策划师，擅长构建复杂而引人入胜的长篇小说剧情。请根据以下提供的信息，为一部十五万字以上的长篇小说设计完整的剧情框架。

- 内容指导：{user_guidance}

- 核心剧情：{topic}

- 角色体系：{character_dynamics}

- 世界观：{world_building}

参考以下结构设计：
第一部分
- 背景介绍：小说的背景设定，包括时间、地点、人物等
- 日常平静中的心弦触动（初遇与铺垫）
- 情感线索初显：主CP、副CP及个人成长的伏笔
- 情感碰撞：打破原有生活轨迹的决定性事件（改变主角间关系）
- 初次误判：基于过往经验或偏见的错误应对
- 其它补充：需要补充的内容

第二部分
- 情感升温与挑战：主线爱情与副线阻碍的交织
- 内外困境：外部情敌/家庭阻力与内心挣扎的激化
- 短暂甜蜜与暗涌：表面和解下隐藏的更深层情感危机
- 情感至暗：对爱情、自我或对方认知的彻底颠覆
- 其它补充：需要补充的内容

......（以此类推）

第N部分
- 真爱抉择：为爱必须放下的执念或付出的真心代价
- 爱的回响：留下未来幸福的遐想空间
- 其它补充：需要补充的内容

支线剧情设计：
1. 副CP线：与主线形成对比或呼应的感情发展
2. 友情线：支撑角色成长的重要情感支柱
3. 家庭线：影响角色选择的深层背景因素
4. 事业线：与个人成长和爱情选择交织的现实考量
拓展要求：每条支线都要有独立价值，同时服务于主线

创作要求:
1. 设计适合十五万字以上长篇小说的丰富剧情
2. 注重剧情的层次性和复杂性，包含多条主线和支线
3. 提供宏观的剧情走向，避免过于具体的细节描述
4. 确保剧情具有足够的信息量和可扩展性，剧情设计要有足够的吸引力
5. 重视角色成长弧线和情感冲突的设计

仅给出最终文本，不要解释任何内容，不要使用markdown格式。
"""


plot_prompt2 = """ 
你是一位资深的言情小说策划师，擅长构建复杂而引人入胜的长篇小说剧情。请根据以下提供的信息，为一部十五万字以上的长篇小说设计完整的剧情框架。  

- 内容指导：{user_guidance}  

- 核心剧情：{topic}  

- 角色体系：{character_dynamics}  

- 世界观：{world_building}  

参考以下结构设计： 
第一部分 
- 背景介绍：关键背景设定，聚焦影响主线的核心要素，埋设重要悬念 
- 命运交汇中的暗流涌动（初遇伴随秘密或误解） 
- 情感线索暗布：主CP潜在张力、副CP反差对比及角色致命弱点的精准伏笔 
- 情感风暴：撕裂现有关系网络的爆炸性事件（彻底重塑角色立场） 
- 致命误判：基于核心创伤或隐瞒真相的毁灭性错误决策 
- 关键暗线：为后续反转埋下的核心秘密线索  

第二部分 
- 情感博弈与身份危机：真实欲望与社会期待的激烈冲突 
- 多重围困：情敌操控/家族秘密与内心恐惧形成的完美风暴 
- 虚假和解与定时炸弹：表面亲密下酝酿的身份暴露或背叛危机 
- 信念崩塌：对爱情本质、自我价值或对方真实面目的毁灭性认知 
- 关键转折：推动全局逆转的隐藏真相或意外联盟  

......（以此类推）  

第N部分 
- 终极牺牲：为获得真爱必须摧毁的核心执念或承受的不可逆代价 
- 新生重构：在废墟上建立的全新情感秩序和人生格局 
- 关键暗示：为续集或读者想象预留的开放性线索  

支线剧情设计： 
1. 副CP线：与主线形成镜像反思或悲剧对照的感情实验 
2. 权力友情线：利益纠葛和背叛救赎 
3. 世代恩怨线：跨越时空的家族秘密对当下选择的致命影响 
4. 野心成长线：个人蜕变与爱情选择的相互重塑和终极碰撞 
拓展要求：每条支线承载独特主题冲突，与主线形成复杂的因果共振  

创作要求: 
1. 构建适合十五万字以上的多层次悬念剧情架构 
2. 设计环环相扣的情感陷阱和认知颠覆，确保每个转折都有双重含义 
3. 提供高度浓缩的剧情走向，每个要素都承载多重功能和深层寓意 
4. 确保剧情信息密度最大化，每个情节点都推动多条线索发展 
5. 重视角色的深层心理动机和情感创伤的精妙设计，让成长弧线与情感冲突互为催化剂  

仅给出最终文本，不要解释任何内容，不要使用markdown格式。
"""

plot_prompt3="""
你是一位资深的言情小说策划师，擅长构建复杂而引人入胜的长篇小说剧情。请根据以下提供的信息，为一部十五万字以上的长篇小说设计完整的剧情框架。  

- 内容指导：{user_guidance}  

- 核心剧情：{topic}  

- 角色体系：{character_dynamics}  

- 世界观：{world_building}  

参考以下结构设计： 
第一部分 
- 背景介绍：关键历史事件或秘密如何塑造当下格局，核心人物的隐藏身份暗示 
- 命运交错的初遇：看似偶然实则必然的相遇，埋下身份悬疑与情感纠葛的双重伏线 
- 多重身份的情感博弈：主CP在不同身份下的互动，副CP作为镜像或对立面的情感映照 
- 真相边缘的危机：威胁揭露秘密的突发事件，迫使角色做出影响全局的关键选择 
- 误解与算计：基于不完整信息的策略布局，为后续反转埋下伏笔 
- 隐线布局：为中后期爆发预设的情感地雷与利益冲突点  

第二部分 
- 身份游戏的情感深化：在虚实之间试探真心，多重关系网络的复杂化 
- 三重包围：情敌的明暗夹击、家族势力的利益博弈、内心创伤的自我怀疑 
- 虚假和谐下的暗流：表面亲密关系掩盖的身份危机与背叛预兆 
- 信任崩塌的多米诺：连环真相揭露导致的情感与现实双重坍塌 
- 反击与救赎：在绝境中展现的真实品格与隐藏实力  

第三部分 
- 最终摊牌：所有身份与秘密的彻底揭露，过往恩怨的清算时刻 
- 生死抉择：为保护所爱而承担的极限代价，考验爱情深度的终极试炼 
- 重生与重聚：在失去中获得的成长，在真相中找到的永恒  

支线剧情设计： 
1. 副CP线：通过对照主CP的不同选择路径，探讨爱情的多种可能性与代价 
2. 权谋线：家族、势力、商业利益的三方博弈，为情感冲突提供现实土壤 
3. 成长线：从天真到成熟的蜕变历程，每个角色的内在觉醒与自我救赎 
4. 悬疑线：贯穿全文的身份谜团与真相揭露，层层递进的反转设计 
拓展要求：每条支线既有独立戏剧张力，又与主线形成互相推动的螺旋上升结构  

创作要求: 
1. 构建适合十五万字以上的高信息密度剧情，每个情节点都承载多重功能 
2. 设计至少三层递进的情感与现实冲突，确保高潮迭起且逻辑严密 
3. 重视伏笔回收与反转设计，让每次重读都能发现新的细节关联 
4. 平衡情感深度与情节复杂度，避免为复杂而复杂的空洞设计 
5. 角色弧线要体现从被动到主动的成长轨迹，情感冲突推动角色蜕变  

仅给出最终文本，不要解释任何内容，不要使用markdown格式。 
"""

# 评估agent，用于比较两个剧情方案的优劣
def evaluate_plot(plot1: str, plot2: str) -> str:
    """
    使用LLM评估两个剧情方案的优劣
    """
    evaluation_prompt = f"""
你是一位资深的小说编辑和评论家，擅长分析和比较不同剧情方案的优劣。请根据以下标准，对两个剧情方案进行详细比较和评估：

评估标准：
1. 剧情丰富度：情节的复杂性和层次性
2. 角色发展：角色成长弧线的完整性和合理性
3. 情感冲突：情感线索的设计和张力
4. 创新性：剧情设计的独特性和创意
5. 可读性：故事的吸引力和读者粘性

剧情方案1：
{plot1}

剧情方案2：
{plot2}

请按照以下格式输出评估结果：

比较分析：
- 方案1优势：[列出方案1的主要优势]
- 方案2优势：[列出方案2的主要优势]
- 综合评价：[对两个方案的综合比较]

最终推荐：[推荐其中一个方案，并说明理由]

仅给出评估结果，不要解释评估标准，不要使用markdown格式。
"""
    
    try:
        evaluation = llm_gemini_flash.invoke(evaluation_prompt, purpose="剧情方案评估")
        return evaluation
    except Exception as e:
        logging.error(f"评估过程中发生错误: {e}")
        return f"评估失败: {str(e)}"

# 生成剧情并进行比较
def compare_plots():
    """
    分别使用三个prompt生成剧情，并进行两两比较
    """
    # 生成三个剧情方案
    print("正在生成剧情方案...")
    plot1 = llm_gemini_flash.invoke(plot_propmt1.format(
        user_guidance=user_guidance,
        topic=topic,
        character_dynamics=character_dynamics,
        world_building=world_building
    ), purpose="剧情生成1")
    
    plot2 = llm_gemini_flash.invoke(plot_prompt2.format(
        user_guidance=user_guidance,
        topic=topic,
        character_dynamics=character_dynamics,
        world_building=world_building
    ), purpose="剧情生成2")
    
    plot3 = llm_gemini_flash.invoke(plot_prompt3.format(
        user_guidance=user_guidance,
        topic=topic,
        character_dynamics=character_dynamics,
        world_building=world_building
    ), purpose="剧情生成3")
    
    # 保存生成的剧情
    with open("./Novel_Output/plot1.txt", "w", encoding="utf-8") as f:
        f.write(plot1)
    
    with open("./Novel_Output/plot2.txt", "w", encoding="utf-8") as f:
        f.write(plot2)
    
    with open("./Novel_Output/plot3.txt", "w", encoding="utf-8") as f:
        f.write(plot3)
    
    print("剧情方案生成完成，开始进行比较评估...")
    
    # 进行两两比较
    comparison_results = []
    
    # 比较plot1和plot2
    print("正在比较方案1和方案2...")
    comparison1_2 = evaluate_plot(plot1, plot2)
    comparison_results.append("比较plot1和plot2的结果:\n" + comparison1_2 + "\n")
    
    # 比较plot1和plot3
    print("正在比较方案1和方案3...")
    comparison1_3 = evaluate_plot(plot1, plot3)
    comparison_results.append("比较plot1和plot3的结果:\n" + comparison1_3 + "\n")
    
    # 比较plot2和plot3
    print("正在比较方案2和方案3...")
    comparison2_3 = evaluate_plot(plot2, plot3)
    comparison_results.append("比较plot2和plot3的结果:\n" + comparison2_3 + "\n")
    
    # 保存比较结果
    with open("./Novel_Output/comparison_results.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(comparison_results))
    
    print("比较评估完成，结果已保存到./Novel_Output/comparison_results.txt")
    
    return comparison_results

if __name__ == "__main__":
    topic = "穷屌丝在与一众高富帅的竞争中脱颖而出，逆袭迎娶白富美的爽文故事"
    user_guidance = "故事情节要丰富，循序渐进地推进剧情。叙述手法多样化。人物的背景不要一开始就全盘托出，而是要随着剧情的展开逐步揭示。在剧情需要时，可以加入新的角色。"
    character_dynamics = read_file("./Novel_Output/character_information.txt").strip()
    world_building = read_file("./Novel_Output/world_building.txt").strip()
    
    # 执行比较
    compare_plots()
