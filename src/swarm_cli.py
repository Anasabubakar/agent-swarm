#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║    ███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗         ║
║    ██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║         ║
║    ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║         ║
║    ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║         ║
║    ███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║         ║
║    ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝         ║
║                                                           ║
║    Interactive Agent Swarm CLI                            ║
║    by Anas Abubakar                                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

The main interactive CLI application.
Opens like Claude Code / Gemini CLI.
"""

import sys
import os
import json
import subprocess
import threading
import itertools
import time
import signal
import tty
import termios
import select
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

# ═══════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════

SWARM_ROOT = Path(os.environ.get("SWARM_ROOT", Path(__file__).parent.parent))
AGENTS_DIR = SWARM_ROOT / "agents"
MEMORY_DIR = SWARM_ROOT / "memory"
CHAT_HISTORY_DIR = MEMORY_DIR / "chats"
CONFIG_FILE = SWARM_ROOT / "swarm.config.json"

CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════
# TERMINAL HELPERS
# ═══════════════════════════════════════════════════════

class Term:
    """Low-level terminal control"""
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    
    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright
    BRED = "\033[91m"
    BGREEN = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE = "\033[94m"
    BMAGENTA = "\033[95m"
    BCYAN = "\033[96m"
    BWHITE = "\033[97m"
    
    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    
    @staticmethod
    def clear():
        os.system('clear' if os.name != 'nt' else 'cls')
    
    @staticmethod
    def move_up(n=1):
        sys.stdout.write(f"\033[{n}A")
    
    @staticmethod
    def clear_line():
        sys.stdout.write("\r\033[K")
    
    @staticmethod
    def hide_cursor():
        sys.stdout.write("\033[?25l")
    
    @staticmethod
    def show_cursor():
        sys.stdout.write("\033[?25h")
    
    @staticmethod
    def flush():
        sys.stdout.flush()


T = Term


# ═══════════════════════════════════════════════════════
# AVAILABLE ENGINES AND MODELS
# ═══════════════════════════════════════════════════════

ENGINES = {
    "auto": {"name": "Auto-detect", "description": "Detect best available engine automatically"},
    "claude": {
        "name": "Claude Code",
        "command": "claude",
        "models": ["claude-opus-4", "claude-sonnet-4", "claude-haiku", "auto"],
    },
    "gemini": {
        "name": "Gemini CLI",
        "command": "gemini",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "auto"],
    },
    "kilo": {
        "name": "Kilo Code",
        "command": "kilo",
        "models": ["kilo-auto", "kilo-pro", "auto"],
    },
    "codex": {
        "name": "Codex",
        "command": "codex",
        "models": ["o4-mini", "o3", "gpt-4.1", "auto"],
    },
    "aider": {
        "name": "Aider",
        "command": "aider",
        "models": ["claude-sonnet-4", "gpt-4.1", "auto"],
    },
}


def detect_installed_engines() -> list:
    """Find which engines are actually installed"""
    import shutil
    installed = []
    for key, eng in ENGINES.items():
        if key == "auto":
            continue
        if shutil.which(eng["command"]):
            installed.append(key)
    return installed


# ═══════════════════════════════════════════════════════
# INTERACTIVE MENU
# ═══════════════════════════════════════════════════════

class InteractiveMenu:
    """Arrow-key navigable menu"""
    
    def __init__(self, title: str, options: list, descriptions: list = None):
        self.title = title
        self.options = options
        self.descriptions = descriptions or [""] * len(options)
        self.selected = 0
    
    def show(self) -> int:
        """Show menu and return selected index. Returns -1 on ESC."""
        T.hide_cursor()
        try:
            while True:
                # Draw menu
                print(f"\n  {T.BOLD}{T.BCYAN}{self.title}{T.RESET}")
                print(f"  {T.DIM}{'─' * 40}{T.RESET}")
                
                for i, opt in enumerate(self.options):
                    if i == self.selected:
                        prefix = f"  {T.BGREEN}▸{T.RESET}"
                        style = f"{T.BOLD}{T.BWHITE}"
                        desc = f"  {T.DIM}{self.descriptions[i]}{T.RESET}" if self.descriptions[i] else ""
                    else:
                        prefix = f"  {T.DIM} {T.RESET}"
                        style = f"{T.DIM}"
                        desc = ""
                    
                    print(f"{prefix} {style}{opt}{T.RESET}{desc}")
                
                print(f"\n  {T.DIM}↑/↓ navigate • Enter select • ESC cancel{T.RESET}")
                
                # Read key
                key = self._read_key()
                
                # Clear menu
                for _ in range(len(self.options) + 4):
                    T.move_up()
                    T.clear_line()
                
                if key == "UP":
                    self.selected = (self.selected - 1) % len(self.options)
                elif key == "DOWN":
                    self.selected = (self.selected + 1) % len(self.options)
                elif key == "ENTER":
                    return self.selected
                elif key == "ESC":
                    return -1
        finally:
            T.show_cursor()
    
    def _read_key(self) -> str:
        """Read a single keypress"""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A': return "UP"
                    if ch3 == 'B': return "DOWN"
                    if ch3 == 'C': return "RIGHT"
                    if ch3 == 'D': return "LEFT"
                return "ESC"
            elif ch == '\r' or ch == '\n':
                return "ENTER"
            elif ch == '\x03':
                raise KeyboardInterrupt
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ═══════════════════════════════════════════════════════
# APPROVAL DIALOG
# ═══════════════════════════════════════════════════════

class ApprovalDialog:
    """Interactive approval for agent actions"""
    
    OPTIONS = [
        ("y", "Yes, proceed"),
        ("p", "Proceed and don't ask again for this project"),
        ("s", "Skip this step"),
        ("d", "Deny"),
        ("e", "Deny and tell agent what to do instead"),
    ]
    
    @staticmethod
    def show(action_description: str) -> str:
        """
        Show approval dialog. Returns one of: y, p, s, d, e
        """
        print(f"\n  {T.BYELLOW}⚠ Agent wants to:{T.RESET}")
        print(f"  {T.DIM}{action_description}{T.RESET}")
        print()
        
        for key, desc in ApprovalDialog.OPTIONS:
            print(f"  {T.BCYAN}[{key}]{T.RESET} {desc}")
        
        print()
        T.hide_cursor()
        try:
            while True:
                sys.stdout.write(f"  {T.BWHITE}?{T.RESET} Your choice: ")
                T.flush()
                
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1).lower()
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
                
                T.show_cursor()
                print(ch)
                
                valid = [o[0] for o in ApprovalDialog.OPTIONS]
                if ch in valid:
                    return ch
                elif ch == '\x03':
                    return "d"
                else:
                    T.hide_cursor()
                    print(f"  {T.DIM}Invalid. Press y/p/s/d/e{T.RESET}")
        finally:
            T.show_cursor()


# ═══════════════════════════════════════════════════════
# SPINNER
# ═══════════════════════════════════════════════════════

class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, message: str = "Working"):
        self.message = message
        self._stop = False
        self._thread = None
    
    def start(self):
        self._stop = False
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self
    
    def _animate(self):
        for frame in itertools.cycle(self.FRAMES):
            if self._stop:
                break
            sys.stdout.write(f"\r  {T.CYAN}{frame}{T.RESET} {self.message}")
            T.flush()
            time.sleep(0.08)
    
    def stop(self, success: bool = True, message: str = ""):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=0.5)
        icon = f"{T.GREEN}✓{T.RESET}" if success else f"{T.RED}✗{T.RESET}"
        msg = message or self.message
        T.clear_line()
        print(f"  {icon} {msg}")


# ═══════════════════════════════════════════════════════
# CHAT MEMORY
# ═══════════════════════════════════════════════════════

class ChatMemory:
    """Persistent chat history across sessions"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.chat_file = self.project_dir / ".swarm-chat.json"
        self.messages = self._load()
    
    def _load(self) -> list:
        if self.chat_file.exists():
            try:
                return json.loads(self.chat_file.read_text())
            except:
                return []
        return []
    
    def save(self):
        self.chat_file.write_text(json.dumps(self.messages, indent=2, default=str))
    
    def add(self, role: str, content: str, agent: str = None):
        self.messages.append({
            "role": role,
            "content": content,
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
        })
        self.save()
    
    def get_context(self, max_messages: int = 20) -> str:
        """Get recent chat history as context string"""
        recent = self.messages[-max_messages:]
        parts = []
        for msg in recent:
            role = msg["role"].upper()
            agent = f" [{msg['agent']}]" if msg.get("agent") else ""
            parts.append(f"{role}{agent}: {msg['content'][:500]}")
        return "\n".join(parts)
    
    def clear(self):
        self.messages = []
        self.save()


# ═══════════════════════════════════════════════════════
# SLASH COMMANDS
# ═══════════════════════════════════════════════════════

class SlashCommands:
    """Handle /commands"""
    
    COMMANDS = {
        "/help": "Show available commands",
        "/employee": "Choose a specific agent to work with",
        "/employee list": "List all available agents",
        "/employee list add": "Add a custom agent",
        "/model": "Change AI engine/model",
        "/model list": "List available models",
        "/memory": "Show chat history",
        "/memory clear": "Clear chat history",
        "/workspace": "Show workspace info",
        "/status": "Show swarm status",
        "/credits": "Show credits",
        "/quit": "Exit swarm",
        "/exit": "Exit swarm",
    }
    
    @staticmethod
    def handle(command: str, swarm: 'SwarmCLI') -> bool:
        """
        Handle a slash command. Returns True if handled, False if unknown.
        """
        cmd = command.strip().lower()
        
        if cmd == "/help":
            SlashCommands._show_help()
            return True
        
        elif cmd == "/credits":
            SlashCommands._show_credits()
            return True
        
        elif cmd.startswith("/employee list add"):
            SlashCommands._add_employee(swarm)
            return True
        
        elif cmd.startswith("/employee list"):
            SlashCommands._list_employees(swarm)
            return True
        
        elif cmd.startswith("/employee"):
            SlashCommands._choose_employee(swarm)
            return True
        
        elif cmd.startswith("/model list"):
            SlashCommands._list_models(swarm)
            return True
        
        elif cmd.startswith("/model"):
            SlashCommands._change_model(swarm)
            return True
        
        elif cmd == "/memory":
            SlashCommands._show_memory(swarm)
            return True
        
        elif cmd == "/memory clear":
            swarm.memory.clear()
            print(f"  {T.GREEN}✓{T.RESET} Chat history cleared")
            return True
        
        elif cmd == "/workspace":
            SlashCommands._show_workspace(swarm)
            return True
        
        elif cmd == "/status":
            SlashCommands._show_status(swarm)
            return True
        
        elif cmd in ["/quit", "/exit"]:
            print(f"\n  {T.BCYAN}Goodbye! 🛡️{T.RESET}\n")
            sys.exit(0)
        
        else:
            print(f"  {T.RED}Unknown command: {command}{T.RESET}")
            print(f"  {T.DIM}Type /help for available commands{T.RESET}")
            return True
    
    @staticmethod
    def _show_help():
        print(f"\n  {T.BOLD}{T.BCYAN}Slash Commands{T.RESET}")
        print(f"  {T.DIM}{'─' * 40}{T.RESET}")
        for cmd, desc in SlashCommands.COMMANDS.items():
            print(f"  {T.BCYAN}{cmd:<25}{T.RESET} {T.DIM}{desc}{T.RESET}")
        print()
    
    @staticmethod
    def _show_credits():
        print(f"""
  {T.BOLD}{T.BCYAN}═══════════════════════════════════════{T.RESET}
  {T.BOLD}🛡️  Agent Swarm{T.RESET}
  
  {T.DIM}Created by:{T.RESET} {T.BOLD}Anas Abubakar{T.RESET}
  {T.DIM}License:{T.RESET}    MIT
  {T.DIM}Version:{T.RESET}    1.0.0
  {T.DIM}Repo:{T.RESET}      github.com/Anasabubakar/agent-swarm
  
  {T.DIM}Powered by:{T.RESET}
  • agency-agents (185 agents)
  • everything-claude-code (147 skills)
  • superpowers (parallel dispatch)
  • get-shit-done (meta-prompting)
  • claude-mem (persistent memory)
  
  {T.BOLD}{T.BCYAN}═══════════════════════════════════════{T.RESET}
""")
    
    @staticmethod
    def _list_employees(swarm):
        installed = detect_installed_engines()
        config = swarm._load_config()
        agents = config.get("agents", {})
        
        print(f"\n  {T.BOLD}Available Agents ({len(agents)} total){T.RESET}")
        print(f"  {T.DIM}{'─' * 50}{T.RESET}")
        
        categories = {}
        for name, conf in agents.items():
            source = conf.get("source", "custom")
            if source not in categories:
                categories[source] = []
            categories[source].append(name)
        
        for cat, names in sorted(categories.items()):
            print(f"\n  {T.BCYAN}{cat.upper()}{T.RESET} ({len(names)})")
            for name in sorted(names)[:10]:
                print(f"    {T.DIM}•{T.RESET} {name}")
            if len(names) > 10:
                print(f"    {T.DIM}... and {len(names) - 10} more{T.RESET}")
        print()
    
    @staticmethod
    def _choose_employee(swarm):
        menu = InteractiveMenu(
            "Choose an agent to work with:",
            ["frontend-dev", "backend-dev", "devops", "security", "qa-tester", 
             "project-manager", "tech-lead", "motion-graphics", "ui-ux-scout", "Cancel"],
            ["React/Next.js UI", "Node.js API", "Docker/CI-CD", "Security audit", 
             "Testing", "Task breakdown", "Architecture review", "Animations",
             "Design inspiration", "Go back"]
        )
        idx = menu.show()
        if idx >= 0 and idx < len(menu.options) - 1:
            agent = menu.options[idx]
            swarm.active_agent = agent
            print(f"  {T.GREEN}✓{T.RESET} Active agent: {T.BOLD}{agent}{T.RESET}")
        print()
    
    @staticmethod
    def _change_model(swarm):
        installed = detect_installed_engines()
        if not installed:
            print(f"  {T.RED}No engines installed{T.RESET}")
            return
        
        menu = InteractiveMenu(
            "Choose an engine:",
            installed + ["auto", "Cancel"],
            [ENGINES.get(e, {}).get("description", "") for e in installed] + ["Auto-detect", "Go back"]
        )
        idx = menu.show()
        if idx >= 0 and idx < len(menu.options) - 1:
            engine = menu.options[idx]
            
            # If specific engine, also choose model
            if engine != "auto" and engine in ENGINES:
                models = ENGINES[engine].get("models", [])
                if models:
                    model_menu = InteractiveMenu(
                        f"Choose a model for {engine}:",
                        models + ["Cancel"],
                    )
                    midx = model_menu.show()
                    if midx >= 0 and midx < len(models):
                        swarm.engine = engine
                        swarm.model = models[midx]
                        print(f"  {T.GREEN}✓{T.RESET} Engine: {T.BOLD}{engine}{T.RESET} | Model: {T.BOLD}{swarm.model}{T.RESET}")
                        return
            
            swarm.engine = engine
            print(f"  {T.GREEN}✓{T.RESET} Engine: {T.BOLD}{engine}{T.RESET}")
        print()
    
    @staticmethod
    def _list_models(swarm):
        print(f"\n  {T.BOLD}Available Models by Engine{T.RESET}")
        print(f"  {T.DIM}{'─' * 50}{T.RESET}")
        for eng_key, eng in ENGINES.items():
            if eng_key == "auto":
                continue
            models = eng.get("models", [])
            if models:
                print(f"\n  {T.BCYAN}{eng['name']}{T.RESET}")
                for m in models:
                    print(f"    {T.DIM}•{T.RESET} {m}")
        print()
    
    @staticmethod
    def _show_memory(swarm):
        msgs = swarm.memory.messages
        if not msgs:
            print(f"  {T.DIM}No chat history yet{T.RESET}")
            return
        
        print(f"\n  {T.BOLD}Chat History ({len(msgs)} messages){T.RESET}")
        print(f"  {T.DIM}{'─' * 50}{T.RESET}")
        for msg in msgs[-10:]:
            role = msg["role"]
            icon = "▸" if role == "user" else "◂"
            color = T.BWHITE if role == "user" else T.BCYAN
            print(f"  {color}{icon}{T.RESET} {msg['content'][:80]}")
        print()
    
    @staticmethod
    def _show_workspace(swarm):
        print(f"\n  {T.BOLD}Workspace{T.RESET}")
        print(f"  {T.DIM}{'─' * 40}{T.RESET}")
        print(f"  {T.DIM}Directory:{T.RESET} {os.getcwd()}")
        print(f"  {T.DIM}Engine:{T.RESET}    {swarm.engine}")
        print(f"  {T.DIM}Model:{T.RESET}     {swarm.model or 'auto'}")
        print(f"  {T.DIM}Agent:{T.RESET}     {swarm.active_agent or 'auto (via orchestrator)'}")
        print(f"  {T.DIM}Messages:{T.RESET}  {len(swarm.memory.messages)}")
        print()
    
    @staticmethod
    def _show_status(swarm):
        installed = detect_installed_engines()
        print(f"\n  {T.BOLD}Swarm Status{T.RESET}")
        print(f"  {T.DIM}{'─' * 40}{T.RESET}")
        print(f"  {T.GREEN}✓{T.RESET} Engines: {', '.join(installed) if installed else 'none'}")
        
        # Count agents
        config = swarm._load_config()
        agent_count = len(config.get("agents", {}))
        print(f"  {T.GREEN}✓{T.RESET} Agents: {agent_count}")
        print(f"  {T.GREEN}✓{T.RESET} Skills: 239")
        print(f"  {T.GREEN}✓{T.RESET} Commands: 125")
        print(f"  {T.GREEN}✓{T.RESET} Rules: 77")
        print()
    
    @staticmethod
    def _add_employee(swarm):
        print(f"\n  {T.BYELLOW}Create a custom agent{T.RESET}")
        print(f"  {T.DIM}Enter the agent definition (markdown format){T.RESET}")
        print(f"  {T.DIM}Type 'DONE' on a new line when finished{T.RESET}\n")
        
        lines = []
        while True:
            try:
                line = input(f"  {T.CYAN}>{T.RESET} ")
                if line.strip().upper() == "DONE":
                    break
                lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        
        if lines:
            name = lines[0].replace("#", "").strip().lower().replace(" ", "-")
            content = "\n".join(lines)
            
            agent_file = AGENTS_DIR / "custom" / f"{name}.md"
            agent_file.parent.mkdir(parents=True, exist_ok=True)
            agent_file.write_text(content)
            
            print(f"\n  {T.GREEN}✓{T.RESET} Agent '{name}' saved to {agent_file}")
        print()


# ═══════════════════════════════════════════════════════
# MAIN CLI
# ═══════════════════════════════════════════════════════

class SwarmCLI:
    """The main interactive swarm CLI"""
    
    def __init__(self):
        self.engine = "auto"
        self.model = None
        self.active_agent = None
        self.project_dir = os.getcwd()
        self.memory = ChatMemory(self.project_dir)
        self.denied_actions = set()  # Actions denied with "don't ask again"
    
    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
        return {"agents": {}}
    
    def banner(self):
        print(f"""
{T.BCYAN}{T.BOLD}
  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║    ███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗         ║
  ║    ██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║         ║
  ║    ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║         ║
  ║    ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║         ║
  ║    ███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║         ║
  ║    ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝         ║
  ║                                                           ║
  ║{T.BWHITE}    Interactive Agent Swarm CLI                            {T.BCYAN}║
  ║{T.DIM}    by Anas Abubakar • v1.0.0                              {T.BCYAN}║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝
{T.RESET}""")
    
    def select_model(self):
        """Interactive model selection on startup"""
        installed = detect_installed_engines()
        
        if not installed:
            print(f"  {T.RED}No AI engines found!{T.RESET}")
            print(f"  {T.DIM}Install one of: kilo, claude, gemini, codex, aider{T.RESET}\n")
            self.engine = "auto"
            return
        
        if len(installed) == 1:
            self.engine = installed[0]
            print(f"  {T.GREEN}✓{T.RESET} Using: {T.BOLD}{installed[0]}{T.RESET} (only engine found)\n")
            return
        
        # Multiple engines — let user choose
        options = ["auto"] + installed
        descriptions = ["Detect best available"] + [
            f"{ENGINES.get(e, {}).get('name', e)} ({e})" for e in installed
        ]
        
        menu = InteractiveMenu("Select your engine:", options, descriptions)
        idx = menu.show()
        
        if idx < 0:
            self.engine = "auto"
        else:
            self.engine = options[idx]
        
        print(f"  {T.GREEN}✓{T.RESET} Engine: {T.BOLD}{self.engine}{T.RESET}\n")
    
    def run_goal(self, goal: str):
        """Run the orchestrator for a goal"""
        import shutil
        
        # Build orchestrator command
        cmd = [sys.executable, str(SWARM_ROOT / "orchestrator.py")]
        
        if self.engine != "auto":
            cmd.extend(["--engine", self.engine])
        
        if self.active_agent:
            cmd.extend(["--agent", self.active_agent])
        
        # Add chat context
        context = self.memory.get_context()
        if context:
            goal_with_context = f"{goal}\n\n[Previous conversation context:\n{context[-1000:]}]"
        else:
            goal_with_context = goal
        
        cmd.append(goal_with_context)
        
        # Save to memory
        self.memory.add("user", goal)
        
        # Run
        print()
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, timeout=600)
            self.memory.add("assistant", f"Completed: {goal}", agent=self.active_agent or "orchestrator")
        except subprocess.TimeoutExpired:
            print(f"\n  {T.RED}✗{T.RESET} Timed out after 10 minutes")
            self.memory.add("assistant", f"Timed out: {goal}")
        except KeyboardInterrupt:
            print(f"\n  {T.YELLOW}⏸{T.RESET} Interrupted")
        print()
    
    def chat_loop(self):
        """Main interactive chat loop"""
        self.banner()
        self.select_model()
        
        print(f"  {T.DIM}Type your goal, or /help for commands. ESC or /quit to exit.{T.RESET}\n")
        
        while True:
            try:
                # Prompt
                engine_display = f"{T.DIM}[{self.engine}]{T.RESET}" if self.engine != "auto" else ""
                agent_display = f"{T.DIM}({self.active_agent}){T.RESET}" if self.active_agent else ""
                
                sys.stdout.write(f"  {T.BGREEN}▸{T.RESET} {engine_display}{agent_display} ")
                T.flush()
                
                user_input = input().strip()
                
                if not user_input:
                    continue
                
                # Handle slash commands
                if user_input.startswith("/"):
                    SlashCommands.handle(user_input, self)
                    continue
                
                # Handle ESC to exit
                if user_input.lower() in ["quit", "exit", "q"]:
                    print(f"\n  {T.BCYAN}Goodbye! 🛡️{T.RESET}\n")
                    break
                
                # Run goal
                self.run_goal(user_input)
                
            except KeyboardInterrupt:
                print(f"\n\n  {T.BCYAN}Goodbye! 🛡️{T.RESET}\n")
                break
            except EOFError:
                print()
                break


# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

def main():
    cli = SwarmCLI()
    cli.chat_loop()


if __name__ == "__main__":
    main()
