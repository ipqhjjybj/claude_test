import anyio
from pathlib import Path
from claude_code_sdk import query, ClaudeCodeOptions, Message
import json
import time
from typing import List, Dict, Any

class AutoProjectBuilder:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.system_prompt = self._load_system_prompt()
        self.project_state = {
            "phase": "initialization",
            "completed_tasks": [],
            "failed_tasks": [],
            "current_errors": [],
            "build_status": "not_started"
        }
        
    def _load_system_prompt(self) -> str:
        try:
            with open("system_prompt.txt", 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            return "You are an expert C++/DPDK developer and project automation specialist"
    
    async def run_automated_build_cycle(self):
        """完全自动化的项目构建周期"""
        phases = [
            ("project_setup", "创建项目结构和基础文件"),
            ("dependencies", "配置依赖和构建系统"),
            ("core_implementation", "实现核心模块"),
            ("compilation", "编译和构建"),
            ("testing", "运行测试"),
            ("optimization", "性能优化"),
            ("integration", "集成测试"),
            ("deployment", "部署准备")
        ]
        
        for phase_name, phase_desc in phases:
            print(f"\n{'='*50}")
            print(f"开始阶段: {phase_desc}")
            print(f"{'='*50}")
            
            success = await self._execute_phase(phase_name)
            if not success:
                print(f"阶段 {phase_name} 失败，尝试自动修复...")
                await self._auto_fix_issues(phase_name)
                
                # 重试
                success = await self._execute_phase(phase_name)
                if not success:
                    print(f"阶段 {phase_name} 修复失败，需要人工干预")
                    break
            
            self.project_state["completed_tasks"].append(phase_name)
            self._save_project_state()
    
    async def _execute_phase(self, phase: str) -> bool:
        """执行特定阶段的任务"""
        phase_prompts = {
            "project_setup": self._get_project_setup_prompt(),
            "dependencies": self._get_dependencies_prompt(),
            "core_implementation": self._get_core_implementation_prompt(),
            "compilation": self._get_compilation_prompt(),
            "testing": self._get_testing_prompt(),
            "optimization": self._get_optimization_prompt(),
            "integration": self._get_integration_prompt(),
            "deployment": self._get_deployment_prompt()
        }
        
        prompt = phase_prompts.get(phase, "继续项目开发")
        return await self._run_claude_task(prompt, phase)
    
    async def _run_claude_task(self, prompt: str, phase: str) -> bool:
        """运行Claude任务并检查结果"""
        try:
            options = ClaudeCodeOptions(
                max_turns=15,  # 增加轮次支持复杂任务
                system_prompt=self.system_prompt,
                cwd=self.base_path,
                allowed_tools=["Read", "Write", "Bash"],
                permission_mode="acceptEdits"
            )
            
            messages = []
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
                print(f"[{phase}] AI响应: {message}")
            
            # 检查任务执行结果
            return await self._verify_phase_completion(phase, messages)
            
        except Exception as e:
            print(f"执行阶段 {phase} 时出错: {e}")
            self.project_state["failed_tasks"].append(phase)
            return False
    
    async def _verify_phase_completion(self, phase: str, messages: List[Message]) -> bool:
        """验证阶段是否成功完成"""
        verification_prompts = {
            "project_setup": "检查 big_project 目录结构是否完整创建",
            "dependencies": "验证 CMakeLists.txt 和依赖配置是否正确",
            "core_implementation": "检查核心C++源文件是否实现",
            "compilation": "尝试编译项目并检查是否成功",
            "testing": "运行所有测试并检查结果",
            "optimization": "验证性能优化是否实施",
            "integration": "检查集成测试是否通过",
            "deployment": "验证部署配置是否就绪"
        }
        
        verify_prompt = f"""
        请验证以下阶段是否成功完成: {phase}
        验证内容: {verification_prompts.get(phase, '通用验证')}
        
        请执行必要的检查命令，如：
        - ls -la 检查文件结构
        - cat 检查文件内容
        - cmake/make 尝试构建
        - 运行测试命令
        
        如果发现问题，请列出具体错误。
        最后回答: SUCCESS 或 FAILED，并说明原因。
        """
        
        try:
            options = ClaudeCodeOptions(
                max_turns=5,
                system_prompt="You are a project verification specialist",
                cwd=self.base_path,
                allowed_tools=["Read", "Write", "Bash"],
                permission_mode="acceptEdits"
            )
            
            verification_messages = []
            async for message in query(prompt=verify_prompt, options=options):
                verification_messages.append(message)
                content = str(message).lower()
                if "success" in content:
                    return True
                elif "failed" in content:
                    self.project_state["current_errors"].append(content)
                    return False
            
            return False
            
        except Exception as e:
            print(f"验证阶段 {phase} 时出错: {e}")
            return False
    
    async def _auto_fix_issues(self, phase: str):
        """自动修复问题"""
        fix_prompt = f"""
        阶段 {phase} 执行失败，当前发现的错误：
        {self.project_state['current_errors']}
        
        请分析这些错误并自动修复：
        1. 检查缺失的文件或目录
        2. 修复编译错误
        3. 解决依赖问题
        4. 修正配置错误
        
        请逐步执行修复操作，并验证每个修复步骤。
        """
        
        await self._run_claude_task(fix_prompt, f"{phase}_fix")
    
    def _get_project_setup_prompt(self) -> str:
        return """
        创建完整的 DPDK + 币安WebSocket 项目结构:
        
        big_project/
        ├── src/
        │   ├── dpdk_init.cpp
        │   ├── websocket_client.cpp
        │   ├── binance_api.cpp
        │   ├── data_parser.cpp
        │   ├── performance_monitor.cpp
        │   └── main.cpp
        ├── include/
        │   ├── dpdk_init.h
        │   ├── websocket_client.h
        │   ├── binance_api.h
        │   ├── data_parser.h
        │   └── performance_monitor.h
        ├── examples/
        │   ├── simple_ticker.cpp
        │   └── multi_stream.cpp
        ├── tests/
        │   ├── test_websocket.cpp
        │   └── test_parser.cpp
        ├── scripts/
        │   ├── build.sh
        │   ├── run.sh
        │   └── setup_dpdk.sh
        ├── docs/
        │   ├── API.md
        │   └── PERFORMANCE.md
        ├── CMakeLists.txt
        └── README.md
        
        请创建所有目录和基础文件框架。
        """
    
    def _get_dependencies_prompt(self) -> str:
        return """
        配置项目依赖和构建系统：
        
        1. 创建完整的 CMakeLists.txt，包含：
           - DPDK 依赖查找和链接
           - libwebsockets 依赖
           - nlohmann/json 依赖
           - C++17 标准
           - 编译优化选项
           
        2. 创建 build.sh 脚本自动化构建
        3. 创建 setup_dpdk.sh 配置DPDK环境
        4. 更新 README.md 包含依赖安装说明
        """
    
    def _get_core_implementation_prompt(self) -> str:
        return """
        实现核心模块的完整代码：
        
        1. dpdk_init.cpp/h - DPDK初始化和配置
        2. websocket_client.cpp/h - WebSocket客户端实现
        3. binance_api.cpp/h - 币安API接口封装
        4. data_parser.cpp/h - JSON数据解析器
        5. performance_monitor.cpp/h - 性能监控
        6. main.cpp - 主程序入口
        
        每个模块要包含：
        - 完整的类定义和实现
        - 错误处理
        - 日志输出
        - 性能优化
        """
    
    def _get_compilation_prompt(self) -> str:
        return """
        编译和构建项目：
        
        1. 运行 mkdir -p build && cd build
        2. 执行 cmake ..
        3. 执行 make -j$(nproc)
        4. 检查编译错误并修复
        5. 验证可执行文件生成
        
        如果出现编译错误，请：
        - 分析错误信息
        - 修复源代码问题
        - 调整CMakeLists.txt配置
        - 重新编译直到成功
        """
    
    def _get_testing_prompt(self) -> str:
        return """
        运行项目测试：
        
        1. 编译测试程序
        2. 运行单元测试
        3. 检查测试结果
        4. 修复失败的测试
        
        测试内容：
        - WebSocket连接测试
        - 数据解析测试
        - DPDK初始化测试
        - 性能基准测试
        """
    
    def _get_optimization_prompt(self) -> str:
        return """
        性能优化：
        
        1. 分析性能瓶颈
        2. 优化内存分配
        3. 优化网络处理
        4. 添加性能监控
        5. 生成性能报告
        """
    
    def _get_integration_prompt(self) -> str:
        return """
        集成测试：
        
        1. 测试完整的数据流程
        2. 验证币安WebSocket连接
        3. 检查数据处理pipeline
        4. 压力测试
        """
    
    def _get_deployment_prompt(self) -> str:
        return """
        部署准备：
        
        1. 创建部署脚本
        2. 配置生产环境参数
        3. 生成文档
        4. 创建Docker配置
        """
    
    def _save_project_state(self):
        """保存项目状态"""
        state_file = self.base_path / "project_state.json"
        with open(state_file, 'w') as f:
            json.dump(self.project_state, f, indent=2)

async def main():
    builder = AutoProjectBuilder("/home/ubuntu/git/claude_test")
    await builder.run_automated_build_cycle()

if __name__ == "__main__":
    anyio.run(main()) 