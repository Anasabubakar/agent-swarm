#!/usr/bin/env python3
"""
Agent Swarm — Beautiful Terminal UI
Structured, animated, professional CLI experience.
Like Claude Code / Codex / Gemini CLI.
"""

import sys
import time
import threading
import itertools
from datetime import datetime


class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


C = Colors


class Spinner:
    """Animated spinner for loading states"""
    
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
            sys.stdout.write(f"\r  {C.CYAN}{frame}{C.RESET} {self.message}...")
            sys.stdout.flush()
            time.sleep(0.08)
    
    def stop(self, success: bool = True, message: str = ""):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=0.5)
        
        icon = f"{C.GREEN}✓{C.RESET}" if success else f"{C.RED}✗{C.RESET}"
        msg = message or self.message
        sys.stdout.write(f"\r  {icon} {msg}          \n")
        sys.stdout.flush()


class TUI:
    """Beautiful terminal UI for Agent Swarm"""
    
    VERSION = "1.0.0"
    
    @staticmethod
    def clear_line():
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
    
    @staticmethod
    def banner():
        print(f"""
{C.BRIGHT_CYAN}{C.BOLD}
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    ███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗         ║
    ║    ██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║         ║
    ║    ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║         ║
    ║    ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║         ║
    ║    ███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║         ║
    ║    ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝         ║
    ║                                                           ║
    ║{C.BRIGHT_WHITE}    Engine-agnostic multi-agent orchestration               {C.BRIGHT_CYAN}║
    ║{C.DIM}    by Anas Abubakar • v{C.RESET}{C.BRIGHT_CYAN}{C.DIM}{TUI.VERSION}{C.RESET}{C.BRIGHT_CYAN}{C.DIM}                                    {C.BRIGHT_CYAN}║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
{C.RESET}""")
    
    @staticmethod
    def mini_banner():
        print(f"""
{C.BRIGHT_CYAN}{C.BOLD}  ╭──────────────────────────────────────╮
  │  🛡️  SWARM v{TUI.VERSION}                      │
  │  {C.DIM}Engine-agnostic agent orchestration{C.RESET}{C.BRIGHT_CYAN}{C.BOLD}  │
  ╰──────────────────────────────────────╯{C.RESET}
""")
    
    @staticmethod
    def goal(goal: str, workspace: str, engine: str):
        print(f"""
{C.BRIGHT_WHITE}{C.BOLD}  🎯 GOAL{C.RESET}
  {goal}

{C.DIM}  📁 {workspace}
  🔧 Engine: {engine}{C.RESET}
""")
    
    @staticmethod
    def phase_header(phase_num: int, phase_name: str, description: str):
        icons = {1: "❓", 2: "📐", 3: "🚀", 4: "🐛", 5: "🔍"}
        colors = {1: C.BRIGHT_YELLOW, 2: C.BRIGHT_BLUE, 3: C.BRIGHT_GREEN, 4: C.BRIGHT_RED, 5: C.BRIGHT_MAGENTA}
        
        icon = icons.get(phase_num, "•")
        color = colors.get(phase_num, C.WHITE)
        
        print(f"""
{C.BOLD}  ╭─ Phase {phase_num}/5 ─────────────────────────────────────────╮
  │ {icon}  {color}{phase_name}{C.RESET}{C.BOLD} — {C.DIM}{description}{C.RESET}{C.BOLD}                │
  ╰─────────────────────────────────────────────────────────╯{C.RESET}
""")
    
    @staticmethod
    def agent_start(agent_name: str, engine: str):
        print(f"  {C.BRIGHT_BLUE}▸{C.RESET} {agent_name} {C.DIM}[{engine}]{C.RESET}")
    
    @staticmethod
    def agent_success(agent_name: str, duration: float):
        print(f"  {C.GREEN}✓{C.RESET} {agent_name} {C.DIM}({duration:.1f}s){C.RESET}")
    
    @staticmethod
    def agent_fail(agent_name: str, error: str):
        print(f"  {C.RED}✗{C.RESET} {agent_name} {C.DIM}— {error[:60]}{C.RESET}")
    
    @staticmethod
    def agent_debug(agent_name: str):
        print(f"  {C.YELLOW}🐛{C.RESET} {agent_name} {C.DIM}(attempting fix...){C.RESET}")
    
    @staticmethod
    def summary(total: int, succeeded: int, failed: int, debugged: int, duration: float):
        success_rate = (succeeded / max(1, total)) * 100
        
        bar_width = 30
        filled = int(bar_width * succeeded / max(1, total))
        bar = f"{C.GREEN}{'█' * filled}{C.DIM}{'░' * (bar_width - filled)}{C.RESET}"
        
        print(f"""
{C.BOLD}  ╭─ Results ──────────────────────────────────────────────╮
  │                                                         │
  │  {bar}  {success_rate:.0f}%                        │
  │                                                         │
  │  {C.GREEN}✓{C.RESET} {succeeded} succeeded    {C.RED}✗{C.RESET} {failed} failed    {C.YELLOW}🐛{C.RESET} {debugged} debugged    │
  │  {C.DIM}⏱  {duration:.1f}s total{C.RESET}                                        │
  │                                                         │
  ╰─────────────────────────────────────────────────────────╯{C.RESET}
""")
    
    @staticmethod
    def complete(workspace: str):
        print(f"""
{C.BRIGHT_GREEN}{C.BOLD}  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║    ✅  SWARM COMPLETE                                     ║
  ║                                                           ║
  ║{C.RESET}{C.DIM}    Workspace: {workspace:<44}{C.BRIGHT_GREEN}{C.BOLD}║
  ║{C.RESET}{C.DIM}    Report:    .swarm-report.json{C.DIM}                        {C.BRIGHT_GREEN}{C.BOLD}║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝{C.RESET}
""")
    
    @staticmethod
    def prompt(question: str) -> str:
        """Interactive prompt for user input"""
        try:
            return input(f"\n  {C.BRIGHT_YELLOW}?{C.RESET} {question}\n  {C.CYAN}▸{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""
    
    @staticmethod
    def info(message: str):
        print(f"  {C.BRIGHT_BLUE}ℹ{C.RESET}  {message}")
    
    @staticmethod
    def warn(message: str):
        print(f"  {C.YELLOW}⚠{C.RESET}  {message}")
    
    @staticmethod
    def error(message: str):
        print(f"  {C.RED}✗{C.RESET}  {message}")
    
    @staticmethod
    def success(message: str):
        print(f"  {C.GREEN}✓{C.RESET}  {message}")
    
    @staticmethod
    def divider():
        print(f"  {C.DIM}{'─' * 55}{C.RESET}")
    
    @staticmethod
    def agent_table(agents: list):
        """Print a clean agent status table"""
        print(f"\n  {C.BOLD}{'Agent':<25} {'Engine':<10} {'Status':<12} {'Time':<8}{C.RESET}")
        print(f"  {C.DIM}{'─' * 55}{C.RESET}")
        
        for a in agents:
            status_icon = {
                "running": f"{C.YELLOW}●{C.RESET}",
                "success": f"{C.GREEN}✓{C.RESET}",
                "failed": f"{C.RED}✗{C.RESET}",
                "debugging": f"{C.YELLOW}🐛{C.RESET}",
            }.get(a.get("status", ""), "○")
            
            duration = f"{a.get('duration', 0):.1f}s" if a.get("duration") else "—"
            print(f"  {status_icon} {a['name']:<23} {a.get('engine', '—'):<10} {a.get('status', '—'):<12} {duration:<8}")
        
        print()
