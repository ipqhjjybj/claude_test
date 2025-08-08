import anyio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions, Message

async def main():
    messages: list[Message] = []
    
    # 从 system_prompt.txt 文件读取系统提示
    system_prompt_path = Path("system_prompt.txt")
    try:
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        print(f"警告：找不到 {system_prompt_path} 文件，使用默认系统提示")
        system_prompt = "You are a helpful coding assistant specialized in C++, DPDK, and high-performance networking"
    except Exception as e:
        print(f"读取系统提示文件时出错：{e}，使用默认系统提示")
        system_prompt = "You are a helpful coding assistant specialized in C++, DPDK, and high-performance networking"
    
    options = ClaudeCodeOptions(
        max_turns=10,
        system_prompt=system_prompt,
        cwd=Path("/home/ubuntu/git/claude_test"),
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    
    project_prompt = """
    请帮我创建一个使用C++ DPDK技术获取币安WebSocket行情数据的高性能项目。

    项目需求：
    1. 使用DPDK框架进行高性能网络处理
    2. 连接币安WebSocket API获取实时行情数据
    3. 数据解析和处理
    4. 性能优化和延迟控制

    请在 big_project 目录下创建以下结构：
    - src/ : 源代码目录
    - include/ : 头文件目录  
    - examples/ : 示例代码
    - docs/ : 文档
    - scripts/ : 构建和部署脚本
    - CMakeLists.txt : CMake构建文件
    - README.md : 项目说明

    请创建核心模块：
    1. DPDK初始化和配置模块
    2. WebSocket客户端模块
    3. 币安API接口模块
    4. 数据解析模块
    5. 性能监控模块
    6. 示例应用程序

    每个模块都要包含头文件、实现文件和示例代码。
    """
    
    async for message in query(
        prompt=project_prompt,
        options=options
    ):
        messages.append(message)
    
    print("项目创建完成，消息记录：")
    for i, msg in enumerate(messages):
        print(f"消息 {i+1}: {msg.content if hasattr(msg, 'content') else str(msg)}")

anyio.run(main) 