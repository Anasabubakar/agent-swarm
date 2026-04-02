#!/usr/bin/env python3
"""
Agent Swarm — Engine Adapters
Truly agnostic: works with ANY CLI agent that accepts a prompt.

Each engine is just a command template. Add any engine by defining:
  - command: how to invoke the CLI
  - system_prompt_flag: how to pass the agent role
  - task_position: where the task goes in the command
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

SWARM_ROOT = Path(__file__).parent.parent
AGENTS_DIR = SWARM_ROOT / "agents"


class BaseEngine:
    """Base class for all engine adapters"""
    
    name: str = "base"
    command: str = ""
    system_prompt_flag: str = "--system-prompt"
    task_position: str = "end"  # "end" means task goes at the end
    auto_flag: str = ""  # optional flag for autonomous mode
    timeout: int = 1800  # 30 minutes default for complex tasks like motion graphics
    needs_pty: bool = False  # whether this engine needs a pseudo-terminal
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        """Build the command to execute. Uses temp file for long system prompts."""
        # Save system prompt to file to avoid CLI arg length limits
        prompt_file = SWARM_ROOT / "memory" / f"_prompt_{cls.name}.md"
        prompt_file.parent.mkdir(exist_ok=True)
        prompt_file.write_text(system_prompt)
        
        cmd = cls.command.split()
        
        # Add system prompt via file
        if cls.system_prompt_flag:
            cmd.extend([cls.system_prompt_flag, str(prompt_file)])
        
        # Add auto flag if specified
        if cls.auto_flag:
            cmd.append(cls.auto_flag)
        
        # Add task
        if cls.task_position == "end":
            cmd.append(task)
        elif cls.task_position == "after_command":
            cmd = [cmd[0], task] + cmd[1:]
        
        return cmd
    
    @classmethod
    def run(cls, agent_file: str, task: str, output_dir: str = ".") -> dict:
        """Execute a task using this engine"""
        agent_path = AGENTS_DIR / agent_file
        
        if not agent_path.exists():
            return {
                "stdout": "",
                "stderr": f"Agent file not found: {agent_file}",
                "returncode": 1
            }
        
        system_prompt = agent_path.read_text()
        cmd = cls.build_command(system_prompt, task)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=cls.timeout,
                cwd=output_dir
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Engine timed out after {cls.timeout}s",
                "returncode": 124,
                "command": " ".join(cmd)
            }
        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"Command not found: {cls.command}",
                "returncode": 127,
                "command": " ".join(cmd)
            }


# ============================================================
# BUILT-IN ENGINES
# ============================================================

class ClaudeCodeEngine(BaseEngine):
    """Anthropic Claude Code CLI"""
    name = "claude"
    command = "claude"
    system_prompt_flag = "--system-prompt"
    auto_flag = "--print"


class GeminiCLIEngine(BaseEngine):
    """Google Gemini CLI"""
    name = "gemini"
    command = "gemini"
    system_prompt_flag = None
    auto_flag = None
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        # Gemini -p takes prompt as argument, but long prompts break
        # Use -p for headless mode, combine system prompt with task
        full_prompt = f"{system_prompt}\n\n---\n\nYour task: {task}\n\nComplete the task and return your results."
        return ["gemini", "-p", full_prompt]
    
    @classmethod
    def run(cls, agent_file: str, task: str, output_dir: str = ".") -> dict:
        """Run with stdin pipe to avoid shell escaping issues"""
        import os as _os
        agent_path = AGENTS_DIR / agent_file
        if not agent_path.exists():
            return {"stdout": "", "stderr": f"Agent file not found: {agent_file}", "returncode": 1}
        
        system_prompt = agent_path.read_text()
        full_prompt = f"{system_prompt}\n\n---\n\nYour task: {task}\n\nComplete the task and return your results."
        
        import subprocess
        try:
            result = subprocess.run(
                ["gemini", "-p", full_prompt],
                capture_output=True,
                text=True,
                timeout=cls.timeout,
                cwd=output_dir
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": f"gemini -p '<prompt>'"
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": f"Timed out after {cls.timeout}s", "returncode": 124, "command": ""}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "returncode": 1, "command": ""}


class KiloCodeEngine(BaseEngine):
    """Kilo Code CLI"""
    name = "kilocode"
    command = "kilo"
    system_prompt_flag = None
    auto_flag = "--auto"
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        # Combine system prompt and task into one message
        # Keep it concise to avoid token waste
        prompt = f"{system_prompt}\n\n---\n\nYour task: {task}\n\nComplete the task and return your results."
        return ["kilo", "run", "--auto", prompt]


class CodexEngine(BaseEngine):
    """OpenAI Codex CLI"""
    name = "codex"
    command = "codex"
    system_prompt_flag = None
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        full_prompt = f"SYSTEM:\n{system_prompt}\n\nTASK:\n{task}"
        return ["codex", "--quiet", full_prompt]


class CursorAgentEngine(BaseEngine):
    """Cursor Agent CLI"""
    name = "cursor"
    command = "cursor-agent"
    system_prompt_flag = None
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        return ["cursor-agent", "-p", f"{system_prompt}\n\n{task}"]


class AiderEngine(BaseEngine):
    """Aider AI pair programmer"""
    name = "aider"
    command = "aider"
    system_prompt_flag = None
    auto_flag = "--yes"
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        return ["aider", "--yes", "--message", f"{system_prompt}\n\n{task}"]


class WindsurfEngine(BaseEngine):
    """Windsurf/Cascade CLI"""
    name = "windsurf"
    command = "windsurf"
    system_prompt_flag = "--system-prompt"


class CopilotEngine(BaseEngine):
    """GitHub Copilot CLI"""
    name = "copilot"
    command = "gh-copilot"
    system_prompt_flag = None
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        return ["gh", "copilot", "suggest", f"{system_prompt}\n\n{task}"]


class OpenCodeEngine(BaseEngine):
    """OpenCode CLI"""
    name = "opencode"
    command = "opencode"
    system_prompt_flag = None
    
    @classmethod
    def build_command(cls, system_prompt: str, task: str) -> list:
        return ["opencode", "run", f"{system_prompt}\n\n{task}"]


class QwenCodeEngine(BaseEngine):
    """Qwen Code CLI"""
    name = "qwen"
    command = "qwen"
    system_prompt_flag = "--system"


class GenericEngine(BaseEngine):
    """
    Generic engine — works with ANY CLI that:
    1. Accepts a prompt as an argument
    2. Outputs to stdout
    
    Configure via: --engine generic --command "your-cli" --system-flag "--role" --auto-flag "--yes"
    """
    name = "generic"
    command = ""  # Set dynamically
    system_prompt_flag = "--prompt"
    
    @classmethod
    def configure(cls, command: str, system_flag: str = "--prompt", auto_flag: str = ""):
        """Dynamically configure this engine"""
        cls.command = command
        cls.system_prompt_flag = system_flag
        cls.auto_flag = auto_flag


# ============================================================
# ENGINE REGISTRY
# ============================================================

ENGINES = {
    "claude": ClaudeCodeEngine,
    "gemini": GeminiCLIEngine,
    "kilocode": KiloCodeEngine,
    "codex": CodexEngine,
    "cursor": CursorAgentEngine,
    "aider": AiderEngine,
    "windsurf": WindsurfEngine,
    "copilot": CopilotEngine,
    "opencode": OpenCodeEngine,
    "qwen": QwenCodeEngine,
    "generic": GenericEngine,
}


def get_engine(name: str) -> Optional[BaseEngine]:
    """Get an engine by name"""
    return ENGINES.get(name.lower())


def register_engine(name: str, engine_class: type):
    """Register a custom engine"""
    ENGINES[name.lower()] = engine_class


def list_engines() -> list:
    """List all available engines"""
    return [
        {
            "name": name,
            "class": cls.__name__,
            "command": cls.command or "(dynamic)",
            "system_prompt_flag": cls.system_prompt_flag,
            "available": bool(cls.command) and shutil.which(cls.command.split()[0]) is not None,
        }
        for name, cls in ENGINES.items()
    ]


def detect_available_engine() -> Optional[str]:
    """Auto-detect which engine CLI is installed on the system"""
    # Priority order: kilo > gemini > claude > codex > cursor > aider > rest
    priority = ["kilocode", "gemini", "claude", "codex", "cursor", "aider", "windsurf", "copilot", "opencode", "qwen"]
    for name in priority:
        cls = ENGINES.get(name)
        if cls and cls.command:
            cmd = cls.command.split()[0]
            if shutil.which(cmd):
                return name
    return None


def detect_all_available() -> list:
    """List all available engines in priority order"""
    available = []
    for name, cls in ENGINES.items():
        if name == "generic":
            continue
        if cls.command and shutil.which(cls.command.split()[0]):
            available.append(name)
    return available
