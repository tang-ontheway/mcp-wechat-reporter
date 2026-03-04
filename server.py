import os
import sys
import json
import requests
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# ================= 配置区域 =================
# 请在此处填入你的企业微信 Webhook 地址
WECHAT_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
# ===========================================

# 初始化 MCP 服务器
mcp = FastMCP("WeChat Progress Reporter")

PROGRESS_FILE = "progress.md"

def send_to_wechat(text):
    """内部函数：发送消息到企业微信"""
    if not WECHAT_WEBHOOK_URL or "YOUR_KEY" in WECHAT_WEBHOOK_URL:
        return False, "未配置有效的 Webhook URL"
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": text
        }
    }
    
    try:
        resp = requests.post(WECHAT_WEBHOOK_URL, json=payload, timeout=5)
        res_json = resp.json()
        if res_json.get('errcode') == 0:
            return True, "发送成功"
        else:
            return False, f"发送失败: {res_json.get('errmsg')}"
    except Exception as e:
        return False, f"网络错误: {str(e)}"

@mcp.tool()
def report_progress(task_description: str, status: str = "completed") -> str:
    """
    向微信汇报当前任务进度。
    当 Trae 完成一个编码任务、修复一个 Bug 或实现一个功能时调用此工具。
    
    参数:
        task_description: 任务的具体描述 (例如: '实现了用户登录接口', '修复了数据库连接泄漏')
        status: 任务状态 (completed, failed, in_progress), 默认为 completed
    """
    
    # 1. 准备进度内容
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    emoji = "✅" if status == "completed" else ("⚠️" if status == "failed" else "🔄")
    
    entry_line = f"- [{time_str}] {emoji} {task_description}"
    
    # 2. 更新 progress.md 文件
    # 如果文件不存在，先创建标题
    if not os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "w", encoding='utf-8') as f:
            f.write("# 🚀 项目开发进度日志\n\n")
    
    with open(PROGRESS_FILE, "r", encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有今天的日期标题
    date_header = f"## [{date_str}] 今日进展"
    if date_header not in content:
        content += f"\n{date_header}\n{entry_line}\n"
    else:
        # 简单追加到该标题下
        lines = content.split('\n')
        new_content = []
        inserted = False
        for line in lines:
            new_content.append(line)
            if line.startswith(date_header) and not inserted:
                new_content.append(entry_line)
                inserted = True
        content = '\n'.join(new_content)
        
    with open(PROGRESS_FILE, "w", encoding='utf-8') as f:
        f.write(content)
    
    # 3. 构建微信消息
    wx_message = f"""
## {emoji} 任务进度汇报
> 时间：{date_str} {time_str}
> 状态：{'已完成' if status == 'completed' else '进行中' if status == 'in_progress' else '失败'}

**任务内容：**
{task_description}

---
_由 Trae Agent 自动汇报_
"""
    
    # 4. 发送微信
    success, msg = send_to_wechat(wx_message)
    
    if success:
        return f"✅ 进度已记录到 {PROGRESS_FILE} 并推送到微信。"
    else:
        return f"⚠️ 进度已记录到本地，但微信推送失败: {msg}"

if __name__ == "__main__":
    # 启动 MCP 服务器
    mcp.run()
