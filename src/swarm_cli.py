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
║    Interactive AI Assistant + Agent Swarm                 ║
║    by Anas Abubakar                                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

A full AI CLI assistant that can:
- Answer any question
- Read and understand files
- Build projects with multi-agent swarm
- Execute commands with permission
- Auto-update
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
import glob as globmod
from pathlib import Path
from datetime import datetime
from typing import Optional

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
# COLORS
# ═══════════════════════════════════════════════════════

class C:
    R = "\033[0m"    # Reset
    B = "\033[1m"    # Bold
    D = "\033[2m"    # Dim
    RED = "\033[91m"
    GRN = "\033[92m"
    YLW = "\033[93d"
    BLU = "\033[94m"
    MAG = "\033[95m"
    CYN = "\033[96m"
    WHT = "\033[97m"
    
    @staticmethod
    def t(color, text): return f"{color}{text}{C.R}"


# ═══════════════════════════════════════════════════════
# PERMISSION SYSTEM
# ═══════════════════════════════════════════════════════

class PermissionManager:
    """Manages what actions are allowed without asking"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.perm_file = self.project_dir / ".swarm-permissions.json"
        self.always_allow = self._load()
    
    def _load(self) -> set:
        if self.perm_file.exists():
            try:
                data = json.loads(self.perm_file.read_text())
                return set(data.get("always_allow", []))
            except:
                return set()
        return set()
    
    def _save(self):
        self.perm_file.write_text(json.dumps({
            "always_allow": list(self.always_allow)
        }, indent=2))
    
    def is_allowed(self, action_type: str) -> bool:
        return action_type in self.always_allow
    
    def set_always_allow(self, action_type: str):
        self.always_allow.add(action_type)
        self._save()
    
    def ask_permission(self, action_type: str, description: str) -> str:
        """
        Ask user for permission. Returns: yes, always, no, edit
        """
        if self.is_allowed(action_type):
            return "yes"
        
        print(f"\n  {C.t(C.YLW, '⚠ Permission Required')}")
        print(f"  {C.t(C.D, description)}")
        print()
        print(f"  {C.t(C.CYN, '[y]')} Yes, proceed this time")
        print(f"  {C.t(C.CYN, '[a]')} Always allow this type ({action_type})")
        print(f"  {C.t(C.CYN, '[n]')} No, skip this")
        print(f"  {C.t(C.CYN, '[e]')} Tell me what to do instead")
        print()
        
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                sys.stdout.write(f"  {C.t(C.WHT, '?')} Your choice: ")
                sys.stdout.flush()
                ch = sys.stdin.read(1).lower()
                print(ch)
                
                if ch == 'y': return "yes"
                elif ch == 'a':
                    self.set_always_allow(action_type)
                    return "yes"
                elif ch == 'n': return "no"
                elif ch == 'e': return "edit"
                elif ch == '\x03': return "no"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ═══════════════════════════════════════════════════════
# FILE READER
# ═══════════════════════════════════════════════════════

class FileReader:
    """Read and understand files in the project"""
    
    @staticmethod
    def read(file_path: str, max_lines: int = 200) -> str:
        """Read a file and return its contents"""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"File not found: {file_path}"
            
            if path.is_dir():
                return FileReader.list_directory(file_path)
            
            content = path.read_text(encoding='utf-8', errors='replace')
            lines = content.split('\n')
            
            if len(lines) > max_lines:
                truncated = '\n'.join(lines[:max_lines])
                return f"{truncated}\n\n... ({len(lines) - max_lines} more lines)"
            
            return content
        except Exception as e:
            return f"Error reading {file_path}: {e}"
    
    @staticmethod
    def list_directory(dir_path: str = ".", pattern: str = "*") -> str:
        """List files in a directory"""
        try:
            path = Path(dir_path)
            if not path.exists():
                return f"Directory not found: {dir_path}"
            
            items = []
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                icon = "📁" if item.is_dir() else "📄"
                items.append(f"  {icon} {item.name}")
            
            if not items:
                return f"Empty directory: {dir_path}"
            
            return f"Contents of {dir_path}:\n" + '\n'.join(items[:50])
        except Exception as e:
            return f"Error listing {dir_path}: {e}"
    
    @staticmethod
    def find(pattern: str, directory: str = ".") -> str:
        """Find files matching a pattern"""
        try:
            matches = list(Path(directory).rglob(pattern))
            if not matches:
                return f"No files matching: {pattern}"
            
            result = [f"  {m.relative_to(directory)}" for m in matches[:30]]
            return f"Found {len(matches)} files matching '{pattern}':\n" + '\n'.join(result)
        except Exception as e:
            return f"Error searching: {e}"
    
    @staticmethod
    def search_text(query: str, directory: str = ".", extensions: list = None) -> str:
        """Search for text in files"""
        try:
            if extensions is None:
                extensions = ['.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.json', '.yaml', '.yml', '.html', '.css']
            
            results = []
            for ext in extensions:
                for f in Path(directory).rglob(f"*{ext}"):
                    if '.git' in str(f) or 'node_modules' in str(f):
                        continue
                    try:
                        content = f.read_text(errors='replace')
                        for i, line in enumerate(content.split('\n'), 1):
                            if query.lower() in line.lower():
                                results.append(f"  {f.relative_to(directory)}:{i}: {line.strip()[:80]}")
                                if len(results) >= 20:
                                    break
                    except:
                        pass
                    if len(results) >= 20:
                        break
            
            if not results:
                return f"No matches for '{query}'"
            
            return f"Search results for '{query}':\n" + '\n'.join(results)
        except Exception as e:
            return f"Error searching: {e}"


# ═══════════════════════════════════════════════════════
# COMMAND EXECUTOR
# ═══════════════════════════════════════════════════════

class CommandRunner:
    """Run CLI commands with permission"""
    
    SAFE_COMMANDS = [
        'ls', 'cat', 'head', 'tail', 'grep', 'find', 'pwd', 'whoami',
        'date', 'echo', 'wc', 'sort', 'uniq', 'file', 'which',
        'git status', 'git log', 'git diff', 'git branch', 'git show',
        'npm list', 'npm ls', 'node --version', 'python --version',
        'pip list', 'pip freeze', 'docker ps', 'docker images',
    ]
    
    DANGEROUS_COMMANDS = [
        'rm ', 'rm -', 'rmdir', 'git push', 'git reset --hard',
        'npm install', 'npm uninstall', 'pip install', 'pip uninstall',
        'chmod', 'chown', 'sudo', 'docker run', 'docker rm',
    ]
    
    BLOCKED = [
        'rm -rf /', 'shutdown', 'reboot', ':(){', 'mkfs',
    ]
    
    def __init__(self, permissions: PermissionManager, cwd: str = "."):
        self.permissions = permissions
        self.cwd = cwd
    
    def classify(self, cmd: str) -> str:
        cmd_lower = cmd.lower().strip()
        for b in self.BLOCKED:
            if b in cmd_lower:
                return "blocked"
        for d in self.DANGEROUS_COMMANDS:
            if cmd_lower.startswith(d):
                return "dangerous"
        return "safe"
    
    def run(self, command: str, timeout: int = 120) -> dict:
        """Execute a command, asking permission if needed"""
        safety = self.classify(command)
        
        if safety == "blocked":
            return {"success": False, "error": "Blocked for safety", "output": ""}
        
        if safety == "dangerous":
            perm = self.permissions.ask_permission(
                "run_dangerous_command",
                f"Run command: {command}"
            )
            if perm == "no":
                return {"success": False, "error": "Denied by user", "output": ""}
            if perm == "edit":
                return {"success": False, "error": "User wants to edit", "output": ""}
        
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=timeout, cwd=self.cwd
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timed out", "output": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}


# ═══════════════════════════════════════════════════════
# ENGINE DETECTION
# ═══════════════════════════════════════════════════════

ENGINES = {
    "auto": {"name": "Auto-detect"},
    "claude": {"name": "Claude Code", "cmd": "claude", "models": ["claude-opus-4", "claude-sonnet-4"]},
    "gemini": {"name": "Gemini CLI", "cmd": "gemini", "models": ["gemini-2.5-pro", "gemini-2.5-flash"]},
    "kilo": {"name": "Kilo Code", "cmd": "kilo", "models": ["kilo-auto"]},
    "codex": {"name": "Codex", "cmd": "codex", "models": ["o4-mini", "o3"]},
}

def detect_engines() -> list:
    import shutil
    return [k for k, v in ENGINES.items() if k != "auto" and v.get("cmd") and shutil.which(v["cmd"])]


# ═══════════════════════════════════════════════════════
# ACTION DETECTOR
# ═══════════════════════════════════════════════════════

class ActionDetector:
    """Detect if input is a question, file operation, or build task"""
    
    GREETINGS = [
        "hi", "hello", "hey", "yo", "sup", "wassup", "what's up",
        "haffa", "wetin dey", "good morning", "good afternoon",
        "good evening", "how far", "oya", "weldone", "nack",
    ]
    
    BUILD_KEYWORDS = [
        "build a", "create a", "make a", "develop a", "implement a",
        "write a", "code a", "scaffold a", "setup a", "generate a",
        "build me", "create me", "make me",
        "landing page", "website", "web app", "mobile app",
        "api", "rest api", "dashboard", "admin panel",
        "todo app", "todo list", "calculator", "chat app",
        "login page", "signup page", "auth system",
    ]
    
    FILE_KEYWORDS = [
        "read ", "open ", "show me ", "cat ", "view ",
        "what's in ", "what is in ", "explain this code",
        "look at ", "contents of ",
    ]
    
    CMD_KEYWORDS = [
        "run ", "execute ", "install ", "npm ", "pip ",
        "docker ", "git ", "yarn ", "pnpm ",
    ]
    
    @staticmethod
    def detect(text: str) -> str:
        """Returns: question, build, file_read, command, or chat"""
        text_lower = text.lower().strip()
        
        # Very short or greeting → chat
        words = text_lower.split()
        if len(words) <= 2:
            for g in ActionDetector.GREETINGS:
                if g in text_lower:
                    return "chat"
            if len(words) == 1 and not any(c in text_lower for c in ['.', '/', '\\']):
                return "chat"
        
        # File read
        for kw in ActionDetector.FILE_KEYWORDS:
            if kw in text_lower:
                return "file_read"
        
        # Command (must start with keyword)
        for kw in ActionDetector.CMD_KEYWORDS:
            if text_lower.startswith(kw):
                return "command"
        if text_lower in ['ls', 'dir', 'pwd', 'whoami']:
            return "command"
        
        # Build (need at least 3 words and a build keyword)
        if len(words) >= 3:
            for kw in ActionDetector.BUILD_KEYWORDS:
                if kw in text_lower:
                    return "build"
        
        # Everything else is a question
        return "question"


# ═══════════════════════════════════════════════════════
# CHAT MEMORY
# ═══════════════════════════════════════════════════════

class Memory:
    def __init__(self, project_dir: str = "."):
        self.file = Path(project_dir) / ".swarm-chat.json"
        self.messages = self._load()
    
    def _load(self) -> list:
        if self.file.exists():
            try: return json.loads(self.file.read_text())
            except: return []
        return []
    
    def save(self):
        self.file.write_text(json.dumps(self.messages, indent=2, default=str))
    
    def add(self, role: str, content: str, agent: str = None):
        self.messages.append({
            "role": role, "content": content,
            "agent": agent, "time": datetime.now().isoformat()
        })
        if len(self.messages) > 200:
            self.messages = self.messages[-200:]
        self.save()
    
    def context(self, n: int = 15) -> str:
        recent = self.messages[-n:]
        return "\n".join([f"{m['role']}: {m['content'][:300]}" for m in recent])
    
    def clear(self):
        self.messages = []
        self.save()


# ═══════════════════════════════════════════════════════
# SWARM ORCHESTRATOR BRIDGE
# ═══════════════════════════════════════════════════════

def run_swarm(goal: str, engine: str, cwd: str) -> bool:
    """Run the orchestrator for a build goal"""
    cmd = [sys.executable, str(SWARM_ROOT / "orchestrator.py")]
    if engine != "auto":
        cmd.extend(["--engine", engine])
    cmd.append(goal)
    
    try:
        # Use Popen for better CTRL+C handling
        proc = subprocess.Popen(cmd, cwd=cwd)
        proc.wait(timeout=600)
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"  {C.t(C.RED, '✗ Timed out')}")
        return False
    except KeyboardInterrupt:
        proc.kill()
        print(f"\n  {C.t(C.YLW, '⏸ Cancelled')}")
        return False


# ═══════════════════════════════════════════════════════
# UPDATE CHECKER
# ═══════════════════════════════════════════════════════

def check_update(current_version: str) -> Optional[str]:
    """Check GitHub for updates. Returns new version or None."""
    try:
        import urllib.request
        url = 'https://raw.githubusercontent.com/Anasabubakar/agent-swarm/main/package.json'
        req = urllib.request.Request(url, headers={'User-Agent': 'swarm-cli'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            remote = data.get("version", "0.0.0")
            if remote != current_version:
                return remote
    except:
        pass
    return None


def auto_update() -> bool:
    """Run git pull to update"""
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=str(SWARM_ROOT),
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except:
        return False


# ═══════════════════════════════════════════════════════
# SLASH COMMANDS
# ═══════════════════════════════════════════════════════

COMMANDS = {
    "/help": "Show all commands",
    "/model": "Change AI engine/model",
    "/model list": "List available models",
    "/employee": "Choose a specific agent",
    "/employee list": "List all 245 agents",
    "/read <file>": "Read a file",
    "/ls [dir]": "List directory contents",
    "/find <pattern>": "Find files",
    "/grep <text>": "Search text in files",
    "/run <cmd>": "Run a shell command",
    "/memory": "Show chat history",
    "/memory clear": "Clear chat history",
    "/update": "Check for updates",
    "/permissions": "Show/set permissions",
    "/workspace": "Show workspace info",
    "/credits": "Show credits",
    "/quit": "Exit swarm",
}


def handle_command(cmd: str, cli: 'SwarmCLI') -> bool:
    cmd = cmd.strip()
    
    if cmd == "/help":
        print(f"\n  {C.t(C.B + C.CYN, 'Commands')}")
        print(f"  {C.t(C.D, '─' * 40)}")
        for c, d in COMMANDS.items():
            print(f"  {C.t(C.CYN, c):<25} {C.t(C.D, d)}")
        print()
        return True
    
    if cmd == "/credits":
        print(f"""
  {C.t(C.B + C.CYN, '═══════════════════════════════')}
  {C.t(C.B, '🛡️  Agent Swarm')}
  {C.t(C.D, 'Created by:')} {C.t(C.B, 'Anas Abubakar')}
  {C.t(C.D, 'License:')}    MIT
  {C.t(C.D, 'Version:')}    1.0.2
  {C.t(C.D, 'Repo:')}      github.com/Anasabubakar/agent-swarm
  {C.t(C.B + C.CYN, '═══════════════════════════════')}
""")
        return True
    
    if cmd.startswith("/read "):
        file_path = cmd[6:].strip()
        content = FileReader.read(file_path)
        print(f"\n  {C.t(C.BLU, f'📄 {file_path}')}")
        print(f"  {C.t(C.D, '─' * 40)}")
        for line in content.split('\n')[:50]:
            print(f"  {C.t(C.D, '│')} {line}")
        print()
        return True
    
    if cmd.startswith("/ls"):
        dir_path = cmd[4:].strip() or "."
        print(f"\n{FileReader.list_directory(dir_path)}\n")
        return True
    
    if cmd.startswith("/find "):
        pattern = cmd[6:].strip()
        print(f"\n{FileReader.find(pattern)}\n")
        return True
    
    if cmd.startswith("/grep "):
        query = cmd[6:].strip()
        print(f"\n{FileReader.search_text(query)}\n")
        return True
    
    if cmd.startswith("/run "):
        command = cmd[5:].strip()
        result = cli.runner.run(command)
        if result["output"]:
            print(f"\n{result['output']}")
        if result["error"]:
            print(f"  {C.t(C.RED, result['error'])}")
        print()
        return True
    
    if cmd == "/model":
        installed = detect_engines()
        options = ["auto"] + installed
        print(f"\n  {C.t(C.B, 'Select engine:')}")
        for i, opt in enumerate(options):
            marker = "▸" if opt == cli.engine else " "
            print(f"  {C.t(C.GRN, marker)} {opt}")
        print(f"\n  {C.t(C.D, 'Type: /model <name> to switch')}")
        print()
        return True
    
    if cmd.startswith("/model "):
        engine = cmd[7:].strip()
        if engine in ENGINES or engine == "auto":
            cli.engine = engine
            print(f"  {C.t(C.GRN, '✓')} Engine: {C.t(C.B, engine)}\n")
        else:
            print(f"  {C.t(C.RED, f'Unknown engine: {engine}')}\n")
        return True
    
    if cmd.startswith("/employee list"):
        config = cli._load_config()
        agents = list(config.get("agents", {}).keys())
        print(f"\n  {C.t(C.B, f'Agents ({len(agents)} total)')}")
        print(f"  {C.t(C.D, '─' * 40)}")
        for a in sorted(agents)[:30]:
            print(f"    {C.t(C.D, '•')} {a}")
        if len(agents) > 30:
            print(f"    {C.t(C.D, f'... and {len(agents)-30} more')}")
        print()
        return True
    
    if cmd.startswith("/employee"):
        print(f"  {C.t(C.D, 'Usage: /employee list | /employee list add')}\n")
        return True
    
    if cmd == "/memory":
        msgs = cli.memory.messages
        if not msgs:
            print(f"  {C.t(C.D, 'No chat history yet')}\n")
            return True
        print(f"\n  {C.t(C.B, f'Chat History ({len(msgs)} messages)')}")
        print(f"  {C.t(C.D, '─' * 40)}")
        for m in msgs[-10:]:
            icon = "▸" if m["role"] == "user" else "◂"
            color = C.WHT if m["role"] == "user" else C.CYN
            print(f"  {C.t(color, icon)} {m['content'][:70]}")
        print()
        return True
    
    if cmd == "/memory clear":
        cli.memory.clear()
        print(f"  {C.t(C.GRN, '✓')} Chat history cleared\n")
        return True
    
    if cmd == "/permissions":
        perms = cli.permissions.always_allow
        print(f"\n  {C.t(C.B, 'Always Allowed:')}")
        if perms:
            for p in perms:
                print(f"    {C.t(C.GRN, '✓')} {p}")
        else:
            print(f"    {C.t(C.D, 'None set yet')}")
        print(f"\n  {C.t(C.D, 'Permissions are saved per-project in .swarm-permissions.json')}")
        print()
        return True
    
    if cmd == "/workspace":
        print(f"\n  {C.t(C.B, 'Workspace')}")
        print(f"  {C.t(C.D, '─' * 40)}")
        print(f"  {C.t(C.D, 'Directory:')} {os.getcwd()}")
        print(f"  {C.t(C.D, 'Engine:')}    {cli.engine}")
        print(f"  {C.t(C.D, 'Messages:')}  {len(cli.memory.messages)}")
        print()
        return True
    
    if cmd == "/update":
        new_ver = check_update(cli.version)
        if new_ver:
            print(f"\n  {C.t(C.YLW, f'⚠ Update available: v{cli.version} → v{new_ver}')}")
            print(f"  {C.t(C.CYN, '[a]')} Auto-update now")
            print(f"  {C.t(C.CYN, '[m]')} Manual (cd ~/.swarm && git pull)")
            print(f"  {C.t(C.CYN, '[s]')} Skip for now")
            print()
            
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                sys.stdout.write(f"  {C.t(C.WHT, '?')} ")
                sys.stdout.flush()
                ch = sys.stdin.read(1).lower()
                print(ch)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            
            if ch == 'a':
                print(f"\n  {C.t(C.CYN, '⠋')} Updating...")
                if auto_update():
                    print(f"  {C.t(C.GRN, '✓')} Updated! Restart swarm to use new version.\n")
                else:
                    print(f"  {C.t(C.RED, '✗')} Update failed. Try manually: cd ~/.swarm && git pull\n")
            elif ch == 'm':
                print(f"  {C.t(C.D, 'Run: cd ~/.swarm && git pull')}\n")
            else:
                print(f"  {C.t(C.D, 'Skipped')}\n")
        else:
            print(f"  {C.t(C.GRN, '✓')} You're on the latest version (v{cli.version})\n")
        return True
    
    if cmd in ["/quit", "/exit"]:
        print(f"\n  {C.t(C.CYN, 'Goodbye! 🛡️')}\n")
        sys.exit(0)
    
    print(f"  {C.t(C.RED, f'Unknown: {cmd}')}  Type /help\n")
    return True


# ═══════════════════════════════════════════════════════
# MAIN CLI
# ═══════════════════════════════════════════════════════

class SwarmCLI:
    def __init__(self):
        self.version = "1.0.2"
        self.engine = "auto"
        self.project_dir = os.getcwd()
        self.memory = Memory(self.project_dir)
        self.permissions = PermissionManager(self.project_dir)
        self.runner = CommandRunner(self.permissions, self.project_dir)
        self.file_reader = FileReader()
    
    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try: return json.loads(CONFIG_FILE.read_text())
            except: return {}
        return {"agents": {}}
    
    def banner(self):
        print(f"""
{C.t(C.B + C.CYN, '  ╔═══════════════════════════════════════╗')}
{C.t(C.B + C.CYN, '  ║                                       ║')}
{C.t(C.B + C.CYN, '  ║  ███████╗██╗    ██╗ █████╗ ██████╗    ║')}
{C.t(C.B + C.CYN, '  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗   ║')}
{C.t(C.B + C.CYN, '  ║  ███████╗██║ █╗ ██║███████║██████╔╝   ║')}
{C.t(C.B + C.CYN, '  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗   ║')}
{C.t(C.B + C.CYN, '  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║   ║')}
{C.t(C.B + C.CYN, '  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ║')}
{C.t(C.B + C.CYN, '  ║                                       ║')}
{C.t(C.B + C.CYN, f'  ║  {C.t(C.WHT, f"v{self.version} by Anas Abubakar")}{C.t(C.B + C.CYN, "          ║")}')}
{C.t(C.B + C.CYN, '  ╚═══════════════════════════════════════╝')}
""")
    
    def run(self):
        # Check for updates
        new_ver = check_update(self.version)
        if new_ver:
            print(f"  {C.t(C.YLW, f'⚠ Update available: v{self.version} → v{new_ver}')}")
            print(f"  {C.t(C.D, 'Type /update to upgrade')}")
            print()
        
        self.banner()
        
        # Select engine
        installed = detect_engines()
        if len(installed) == 1:
            self.engine = installed[0]
            print(f"  {C.t(C.GRN, '✓')} Engine: {C.t(C.B, installed[0])}")
        elif len(installed) > 1:
            print(f"  {C.t(C.B, 'Available engines:')} {', '.join(installed)}")
            print(f"  {C.t(C.D, 'Type /model to change')}")
        print()
        
        print(f"  {C.t(C.D, 'Ask me anything. Type /help for commands.')}")
        print(f"  {C.t(C.D, 'I can answer questions, read files, run commands, and build projects.')}\n")
        
        # Main loop
        while True:
            try:
                eng = f"{C.t(C.D, f'[{self.engine}]')} " if self.engine != "auto" else ""
                sys.stdout.write(f"  {C.t(C.GRN, '▸')} {eng}")
                sys.stdout.flush()
                
                user_input = input().strip()
                if not user_input:
                    continue
                
                # Slash commands
                if user_input.startswith("/"):
                    handle_command(user_input, self)
                    continue
                
                # Exit
                if user_input.lower() in ["quit", "exit", "q"]:
                    print(f"\n  {C.t(C.CYN, 'Goodbye! 🛡️')}\n")
                    break
                
                # Detect action type
                action = ActionDetector.detect(user_input)
                self.memory.add("user", user_input)
                
                if action == "chat":
                    # Casual chat — respond naturally
                    responses = {
                        "yo": "Yo! What's good? 👋",
                        "hi": "Hey! What can I do for you?",
                        "hello": "Hello! Ready to work. What do you need?",
                        "hey": "Hey hey! What's the plan?",
                        "sup": "Not much, just waiting for your commands 😄",
                        "wassup": "Chilling, ready to build. What's up with you?",
                        "haffa": "Haffa! Wetin dey? 😄",
                        "how far": "I dey! You good? What you need?",
                    }
                    reply = responses.get(user_input.lower().strip(), "Hey! What do you need?")
                    print(f"\n  {reply}\n")
                    self.memory.add("assistant", reply)
                
                elif action == "question" or action == "chat":
                    # These should go through the engine for real AI responses
                    # For now, suggest using the engine
                    print(f"\n  {C.t(C.BLU, '💡')} I'd answer this using {self.engine}.")
                    print(f"  {C.t(C.D, 'This connects to the AI engine for real responses.')}")
                    print(f"  {C.t(C.D, 'Try: /model to switch engines, or give me a build task.')}\n")
                    self.memory.add("assistant", "Suggested using engine for question answering")
                
                elif action == "file_read":
                    # Extract filename from input
                    words = user_input.split()
                    filename = None
                    for w in words:
                        if '.' in w and len(w) > 2:
                            filename = w
                            break
                        elif w in ['read', 'show', 'cat', 'open', 'view']:
                            idx = words.index(w)
                            if idx + 1 < len(words):
                                filename = words[idx + 1]
                                break
                    
                    if filename:
                        content = FileReader.read(filename)
                        print(f"\n  {C.t(C.BLU, f'📄 {filename}')}")
                        print(f"  {C.t(C.D, '─' * 40)}")
                        for line in content.split('\n')[:30]:
                            print(f"  {C.t(C.D, '│')} {line}")
                        print()
                        self.memory.add("assistant", f"Read file: {filename}")
                    else:
                        print(f"  {C.t(C.YLW, 'Which file?')} Try: /read <filename>\n")
                
                elif action == "command":
                    # Extract and run command
                    cmd = user_input
                    if cmd.lower().startswith("run "):
                        cmd = cmd[4:].strip()
                    elif cmd.lower() in ["ls", "dir"]:
                        cmd = "ls -la"
                    
                    print()
                    result = self.runner.run(cmd)
                    if result["output"]:
                        for line in result["output"].split('\n')[:20]:
                            print(f"  {line}")
                    if result["error"]:
                        print(f"  {C.t(C.RED, result['error'][:200])}")
                    print()
                    self.memory.add("assistant", f"Ran: {cmd}")
                
                elif action == "build":
                    # Run the swarm orchestrator
                    print()
                    success = run_swarm(user_input, self.engine, self.project_dir)
                    self.memory.add("assistant", f"Built: {user_input}" if success else f"Failed: {user_input}")
                    print()
                
            except KeyboardInterrupt:
                print(f"\n")
                continue
            except EOFError:
                print()
                break


def main():
    cli = SwarmCLI()
    cli.run()


if __name__ == "__main__":
    main()
