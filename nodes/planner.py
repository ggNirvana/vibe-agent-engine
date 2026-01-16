from ..state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Initialize LLM
# 我们使用支持 JSON 模式的模型（如 GPT-4o）来确保规划阶段输出结构化的数据。
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
    temperature=0.7,
    model_kwargs={"response_format": {"type": "json_object"}} # Force JSON mode for planner
)

def brand_planner(state: AgentState) -> AgentState:
    """
    Agent 角色: 创意总监 (Creative Director)
    
    职责:
    1. 分析用户偏好（主题、色调、布局）。
    2. 确定项目的整体视觉风格方向。
    3. 生成结构化的“品牌设计方案 (Brand Design Plan)”，用于指导后续的编码阶段。
    
    输入 (Inputs):
    - state['preferences']: 用户选择的风格选项（例如 'Retro Cinema', 'Warm Rose'）。
    
    输出 (Outputs):
    - state['brand_plan']: 一个包含以下内容的 JSON 对象：
        - visual_style: 包含字体、颜色和布局类的 CSS 就绪值。
        
    注意:
    - 为了保护隐私，该节点**不可见**用户的具体内容（姓名、照片、故事）。
    - 它仅基于元数据和风格标签进行工作。
    """
    print(f"[{state['request_id']}] Planner is working...")
    
    # 从状态中提取数据
    prefs = state['preferences']
    
    # 系统提示词 - 已移除上下文中的敏感用户数据
    # 该提示词指导 LLM 扮演设计师角色，将高层概念（如“复古”）转化为具体的技术规格（如“Cinzel 字体”）。
    system_prompt = """You are a Creative Director for luxury events. 
Your task is to analyze the user's preferences to generate a structured "Brand Design Plan" for a wedding invitation website.

Input Data:
- Preferences: Explicit choices (style, color, layout).

Output Schema (JSON):
{
  "visual_style": {
    "theme": "string (e.g., 'Retro Cinema', 'Garden Party')",
    "primary_color": "hex string",
    "font_family": "string (css font family)",
    "layout": "string (e.g., 'single-page-scroll')"
  }
}

Focus ONLY on the visual style and layout structure. Do NOT include any content placeholders."""

    # 用户提示词
    user_message = f"""
Preferences: {prefs}

Generate the Brand Design Plan JSON.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_message)
    ])

    # 链式调用
    chain = prompt | llm | JsonOutputParser()
    
    try:
        plan = chain.invoke({})
        # 合并/回退逻辑：优先使用 prefs 中的硬性约束
        # 如果用户明确选择了颜色，确保它覆盖 LLM 的建议
        if prefs.get('primary_color'):
            plan['visual_style']['primary_color'] = prefs.get('primary_color')
            
    except Exception as e:
        print(f"Error generating plan: {e}")
        # 降级机制：确保即使 LLM 失败，工作流也能继续
        plan = {
            "visual_style": {
                "theme": prefs.get('style', 'modern'),
                "primary_color": prefs.get('primary_color', '#000000'),
                "font_family": "serif",
                "layout": "single-page"
            }
        }
    
    return {
        **state, 
        "brand_plan": plan, 
        "current_step": "PLANNING"
    }
