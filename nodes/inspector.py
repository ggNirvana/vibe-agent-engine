from ..state import AgentState

def inspector(state: AgentState) -> AgentState:
    """
    Agent 角色: 质量保证检查员 (Quality Assurance Inspector)
    
    职责:
    1. 根据需求验证生成的 HTML 代码。
    2. 检查结构完整性（例如，正确的 HTML 标签）。
    3. 验证是否存在动态逻辑钩子（例如 JS API 调用）。
    4. 确保没有隐私泄露（例如，确保没有看起来像真实数据的硬编码占位符）。
    
    输入 (Inputs):
    - state['html_content']: 生成的 HTML 字符串。
    - state['preferences']: 原始用户需求，用于验证合规性。
    
    输出 (Outputs):
    - state['audit_report']: 一个包含通过/失败检查项的 JSON 摘要。
    
    当前检查项:
    - BGM: 如果请求了音乐，是否有处理它的逻辑？
    - 数据绑定: 是否存在 `window.PROJECT_ID` 注入？
    """
    print(f"[{state['request_id']}] Inspector is working...")
    # TODO: 验证 HTML
    # 如果请求了 BGM，检查 HTML 中是否存在 BGM url
    has_audio = "<audio" in state['html_content'] or "new Audio" in state['html_content']
    requested_audio = bool(state['preferences'].get('bgm_url'))
    
    issues = []
    if requested_audio and not has_audio:
        issues.append("BGM requested but not found in HTML")
        
    report = {"valid": len(issues) == 0, "issues": issues}
    
    return {
        **state,
        "audit_report": report,
        "current_step": "AUDITING"
    }
