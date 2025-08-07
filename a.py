import anyio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions, Message

async def main():
    messages: list[Message] = []
    options = ClaudeCodeOptions(
        max_turns=3,
        system_prompt="You are a helpful coding assistant",
        cwd=Path("/home/ubuntu/git/claude_test/test"),  # Can be string or Path
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    async for message in query(
        prompt="请创建一个 Python 程序，生成斐波那契数列的前20个数字，并将结果写入到 foo.py 文件中。程序应该包含一个生成斐波那契数列的函数。",
        options=options
    ):
        messages.append(message)
    
    print("执行完成，消息记录：")
    for i, msg in enumerate(messages):
        print(f"消息 {i+1}: {msg}")

anyio.run(main)
