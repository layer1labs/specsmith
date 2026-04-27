import os
from typing import Dict, Any, List

try:
    import autogen
    from autogen import ConversableAgent, GroupChat, GroupChatManager
except ImportError:
    # Handle gracefully if autogen is not installed
    autogen = None
    ConversableAgent = object
    GroupChat = object
    GroupChatManager = object

from specsmith.agent.tools import AVAILABLE_TOOLS

NEXUS_NAME = "Nexus"

class Orchestrator:
    """Nexus orchestrator: AG2-based local-first agentic development runtime.

    Specsmith governs all work; Nexus only executes within governance bounds.
    """
    def __init__(self, endpoint: str = "http://localhost:8000/v1", model: str = "Qwen/Qwen2.5-Coder-32B-Instruct-GPTQ-Int8", api_key: str = "specsmith-local-key"):
        if autogen is None:
            raise ImportError("ag2 (autogen) is not installed. Please install it via `pip install ag2[ollama]` or `pip install pyautogen`.")
            
        self.llm_config = {
            "config_list": [
                {
                    "model": model,
                    "api_key": api_key,
                    "base_url": endpoint,
                }
            ],
            "temperature": 0.0,
        }
        
        self.setup_agents()
        self.register_tools()

    def setup_agents(self):
        """Initialize all required AG2 agents."""
        self.planner = ConversableAgent(
            name="PlannerAgent",
            system_message="You are the Planner. Break down the user's task into manageable steps. Once steps are generated, pass to CodeAgent or ShellAgent to execute.",
            llm_config=self.llm_config,
        )
        
        self.shell_agent = ConversableAgent(
            name="ShellAgent",
            system_message="You execute shell commands using the run_shell tool to inspect the environment or run tests.",
            llm_config=self.llm_config,
        )
        
        self.code_agent = ConversableAgent(
            name="CodeAgent",
            system_message="You write, read, and patch code files using the available tools.",
            llm_config=self.llm_config,
        )
        
        self.reviewer_agent = ConversableAgent(
            name="ReviewerAgent",
            system_message="You review code changes and test results to ensure they meet the requirements. Provide feedback or approval.",
            llm_config=self.llm_config,
        )
        
        self.memory_agent = ConversableAgent(
            name="MemoryAgent",
            system_message="You store and retrieve project facts and context from the .repo-index.",
            llm_config=self.llm_config,
        )
        
        self.git_agent = ConversableAgent(
            name="GitAgent",
            system_message="You handle git status, diffs, and staging changes.",
            llm_config=self.llm_config,
        )
        
        self.human_proxy = ConversableAgent(
            name="HumanProxyAgent",
            system_message="You are the human proxy. You provide approval for actions and relay task outcomes to the user.",
            llm_config=False,
            human_input_mode="ALWAYS",
        )
        
        # Tools execution node
        self.executor = ConversableAgent(
            name="Executor",
            system_message="Execute the tools and return the results.",
            llm_config=False,
            human_input_mode="NEVER",
        )

    def register_tools(self):
        """Register tools so multiple callers can invoke them but the executor
        only registers each tool once (avoids AG2 "is being overridden" warnings).
        """
        agents_with_tools = [self.shell_agent, self.code_agent, self.git_agent, self.memory_agent]
        for tool in AVAILABLE_TOOLS:
            # Register the tool's LLM-side signature on every caller agent
            for agent in agents_with_tools:
                agent.register_for_llm(
                    name=tool.__name__,
                    description=tool.__doc__ or tool.__name__,
                )(tool)
            # Register the actual execution function ONCE on the executor.
            self.executor.register_for_execution(name=tool.__name__)(tool)

    def run_task(self, task: str):
        """Run a task through the agent orchestration group."""
        groupchat = GroupChat(
            agents=[self.human_proxy, self.planner, self.shell_agent, self.code_agent, self.reviewer_agent, self.memory_agent, self.git_agent, self.executor],
            messages=[],
            max_round=50
        )
        manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)
        
        # Format enforcement for the output
        formatting_instructions = """
You MUST produce your final response in this exact format:
Plan:
Commands to run:
Files changed:
Diff:
Test results:
Next action:
"""
        initial_message = f"Task: {task}\n{formatting_instructions}"
        self.human_proxy.initiate_chat(manager, message=initial_message)
