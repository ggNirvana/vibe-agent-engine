from ..state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
    temperature=0.7
)

def code_architect(state: AgentState) -> AgentState:
    """
    Agent 角色: 前端架构师 (Frontend Architect)
    
    职责:
    1. 将“品牌设计方案 (Brand Design Plan)”转化为可执行的 HTML5 代码。
    2. 实现动态数据绑定逻辑 (JavaScript)，以便在运行时获取用户内容。
    3. 使用 Tailwind CSS 设计响应式布局。
    4. 根据描述处理资源渲染逻辑（例如照片网格），而无需知道实际的 URL。
    
    输入 (Inputs):
    - state['brand_plan']: 来自规划师 (Planner) 的视觉设计规范。
    - state['assets']: 照片元数据（仅描述）。
    
    输出 (Outputs):
    - state['html_content']: 一个完整的、可供部署的单文件 HTML 模板。
    
    关键特性:
    - **动态获取**: 生成的代码包含一个调用 `/api/v1/projects/${window.PROJECT_ID}` 的脚本。
    - **隐私保护**: 不硬编码任何用户数据。所有内容均由浏览器注入。
    - **自适应布局**: LLM 根据照片的*数量*和*描述*设计照片网格（例如，“广角镜头”占据一整行）。
    """
    print(f"[{state['request_id']}] Coder is working...")
    
    plan = state['brand_plan']
    style = plan['visual_style']
    assets = state['assets']
    photos = assets.get('photos', [])
    
    # 构造 Prompt 的照片信息
    # 我们向 LLM 提供照片的*上下文*（例如，“浪漫的日落之吻”）
    # 以便它决定在布局中将它们放置在*何处*，但我们**不**提供 URL。
    photos_info = ""
    if photos:
        photos_info = "\nPhotos available (Layout Guidance Only):"
        for i, p in enumerate(photos):
            desc = p.get('description', 'No description')
            photos_info += f"\n- Index {i}: {desc}"
    
    # System Prompt
    system_prompt = """You are an expert Frontend Architect specializing in high-end wedding invitations.
Your goal is to generate a **dynamic HTML5 template** using Tailwind CSS (via CDN).

CRITICAL SECURITY REQUIREMENT:
- DO NOT hardcode any user data (names, dates, locations, photos) in the HTML.
- The HTML must fetch data dynamically from an API at runtime.

Technical Specs:
1. Single .html file.
2. Use Tailwind CSS: <script src="https://cdn.tailwindcss.com"></script>
3. Visual Style: {theme} | Primary Color: {primary_color} | Font: {font_family}
4. Dynamic Data Fetching:
   - Assume a global variable `window.PROJECT_ID` is available.
   - On load, fetch data from `/api/v1/projects/${{window.PROJECT_ID}}`.
   - The API returns a JSON object with: `theme`, `color`, `groomName`, `brideName`, `date`, `location`, `coordinates`, `bgmUrl`, `guestMessage`, `photos` (list of {{url, description}}).
   - Use JavaScript to populate the DOM elements (e.g., `document.getElementById('groom-name').textContent = data.groomName`).

Photo Layout Logic:
- You have a list of available photos with their descriptions (but NO URLs).
- Use this information to design a grid or layout that fits the content (e.g., if a photo is described as "wide shot", give it a full-width container).
- IMPORTANT: Render `<img>` tags with `data-photo-index="i"` attribute (where i is the index from 0).
- Leave `src` attribute empty or use a placeholder.
- In your JavaScript, bind the real URLs:
  ```javascript
  const photoElements = document.querySelectorAll('[data-photo-index]');
  photoElements.forEach(img => {{
      const idx = parseInt(img.dataset.photoIndex);
      if (data.photos && data.photos[idx]) {{
          img.src = data.photos[idx].url;
          img.alt = data.photos[idx].description || '';
      }} else {{
          img.style.display = 'none'; // Hide if no photo
      }}
  }});
  ```

Layout Requirements:
- Header: Display Groom & Bride names.
- Hero Section: Date & Location.
- Story/Message: Display `guestMessage` if present.
- Gallery: Pre-render the layout for the {photos_count} photos provided.
- Audio: If `bgmUrl` is present in API data, create a hidden audio player dynamically.

Output ONLY raw HTML code."""

    # User Prompt
    user_message = f"""
Visual Style:
Theme: {style['theme']}
Color: {style['primary_color']}
Font: {style['font_family']}

{photos_info}

Generate the dynamic HTML template now.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_message)
    ])

    # Chain
    chain = prompt | llm | StrOutputParser()

    # Invoke
    try:
        html_content = chain.invoke({
            "theme": style['theme'],
            "primary_color": style['primary_color'],
            "font_family": style['font_family'],
            "photos_count": len(photos)
        })
        
        # Cleanup markdown
        html_content = html_content.replace("```html", "").replace("```", "").strip()
        
        # 注入 Project ID 脚本到 head 或 body 开头
        # 我们找到 <head> 并注入脚本
        # 这是将静态 HTML 连接到动态数据源的“引导程序 (Bootloader)”。
        injection = f"<script>window.PROJECT_ID = '{state['request_id']}';</script>"
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", f"<head>\n    {injection}")
        else:
            html_content = injection + "\n" + html_content
            
    except Exception as e:
        print(f"Error generating code: {e}")
        html_content = "<html><body><h1>Error generating template</h1></body></html>"

    return {
        **state,
        "html_content": html_content,
        "current_step": "CODING"
    }
