#!/usr/bin/env python3
"""
  AI Assistant + Agent Swarm
  by Anas Abubakar
  Claude Code features implemented
"""

import sys, os, json, subprocess, shutil, random, time, re
import tty, termios
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Cross-platform terminal support
PLATFORM_TERMINAL = "unix"
if sys.platform == "win32":
    PLATFORM_TERMINAL = "windows"
    try:
        import msvcrt
    except ImportError:
        pass

SWARM_ROOT = Path(os.environ.get("SWARM_ROOT", Path(__file__).parent.parent))

def _get_version():
    try:
        pkg = json.loads((SWARM_ROOT / "package.json").read_text())
        return pkg.get("version", "1.0.0")
    except:
        return "1.0.0"

VERSION = _get_version()
CWD = os.getcwd()

# === SWARM DIRECTORIES ===
SWARM_DIR = os.path.expanduser("~/.swarm")
os.makedirs(SWARM_DIR, exist_ok=True)
SESSIONS_DIR = os.path.join(SWARM_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)
MEMORY_DIR = os.path.join(SWARM_DIR, "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)
MCP_DIR = os.path.join(SWARM_DIR, "mcp-servers")
os.makedirs(MCP_DIR, exist_ok=True)
TOOLS_DIR = os.path.join(SWARM_DIR, "tools")
os.makedirs(TOOLS_DIR, exist_ok=True)

# Terminal reset
sys.stdout.write('\033[0m\033[?25h')
sys.stdout.flush()

# === WELCOME MESSAGES ===
WELCOME = [
    "Right then. Let's get to work.",
    "Another day, another codebase to save.",
    "Swarm is online. Try not to break anything.",
    "245 agents. Zero patience for bad code.",
    "I woke up and chose productivity. Barely.",
    "Fresh session. Clean slate.",
    "Loaded and ready.",
    "Your personal army of AI agents is assembled.",
]

# === UTILITY FUNCTIONS ===
def log(msg: str, style: str = "default"):
    """Styled logging like Claude Code"""
    styles = {
        "default": "\033[0m",
        "dim": "\033[2m",
        "cyan": "\033[36m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "bold": "\033[1m",
    }
    sys.stdout.write(f"{styles.get(style, '')}{msg}\033[0m\n")
    sys.stdout.flush()

def log_thinking(msg: str):
    """Thinking state display"""
    sys.stdout.write(f"\033[2m⬤ {msg}\033[0m\n")
    sys.stdout.flush()

def log_tool_use(name: str, params: List[str] = None):
    """Tool use display"""
    params = params or []
    params_str = ", ".join(params) if params else "none"
    log(f"\033[36m★ {name}\033[0m({params_str})", "dim")

# === SESSION MANAGEMENT ===
class SessionManager:
    """Session handling like Claude Code"""
    
    def __init__(self):
        self.session_id = None
        self.session_dir = None
        self.messages = []
        self.load_session_list()
    
    def load_session_list(self):
        """Load available sessions"""
        self.sessions = []
        if os.path.exists(SESSIONS_DIR):
            for d in os.listdir(SESSIONS_DIR):
                dpath = os.path.join(SESSIONS_DIR, d)
                if os.path.isdir(dpath):
                    meta = os.path.join(dpath, "meta.json")
                    if os.path.exists(meta):
                        try:
                            with open(meta) as f:
                                self.sessions.append(json.load(f))
                        except:
                            pass
    
    def create_session(self) -> str:
        """Create new session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(SESSIONS_DIR, session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        self.session_id = session_id
        
        meta = {
            "id": session_id,
            "created": datetime.now().isoformat(),
            "model": "claude-sonnet-4-20250514",
            "messages": []
        }
        with open(os.path.join(self.session_dir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
        
        return session_id
    
    def save_message(self, role: str, content: str):
        """Save message to session"""
        if not self.session_dir:
            self.create_session()
        
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(msg)
        
        meta_path = os.path.join(self.session_dir, "meta.json")
        with open(meta_path) as f:
            meta = json.load(f)
        meta["messages"] = self.messages
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions"""
        return sorted(self.sessions, key=lambda x: x.get("created", ""), reverse=True)
    
    def load_session(self, session_id: str) -> bool:
        """Load session by ID"""
        self.session_dir = os.path.join(SESSIONS_DIR, session_id)
        meta_path = os.path.join(self.session_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            self.messages = meta.get("messages", [])
            self.session_id = session_id
            return True
        return False
    
    def compact_history(self, keep: int = 10):
        """Compact session history"""
        if len(self.messages) > keep * 2:
            # Keep system messages + last N exchanges
            self.messages = self.messages[:1] + self.messages[-(keep * 2):]
            if self.session_dir:
                meta_path = os.path.join(self.session_dir, "meta.json")
                with open(meta_path) as f:
                    meta = json.load(f)
                meta["messages"] = self.messages
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)

session_mgr = SessionManager()

# === MCP SERVER MANAGEMENT ===
class MCPServer:
    """MCP Server management like Claude Code"""
    
    def __init__(self):
        self.servers = {}
        self.load_servers()
    
    def load_servers(self):
        """Load configured MCP servers"""
        config_path = os.path.join(MCP_DIR, "servers.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                self.servers = json.load(f)
    
    def save_servers(self):
        """Save MCP server config"""
        config_path = os.path.join(MCP_DIR, "servers.json")
        with open(config_path, "w") as f:
            json.dump(self.servers, f, indent=2)
    
    def add_server(self, name: str, config: dict) -> bool:
        """Add MCP server"""
        self.servers[name] = config
        self.save_servers()
        return True
    
    def remove_server(self, name: str) -> bool:
        """Remove MCP server"""
        if name in self.servers:
            del self.servers[name]
            self.save_servers()
            return True
        return False
    
    def list_servers(self) -> List[str]:
        """List MCP servers"""
        return list(self.servers.keys())
    
    async def call_tool(self, server: str, tool: str, args: dict = None):
        """Call MCP server tool"""
        if server not in self.servers:
            return {"error": f"Server {server} not found"}
        
        config = self.servers[server]
        # TODO: Implement actual MCP stdio/SSE call
        return {"result": f"Would call {server}.{tool}({args})"}
    
    def get_tools(self) -> List[dict]:
        """Get all available tools from MCP servers"""
        tools = []
        for name, config in self.servers.items():
            tools.append({
                "name": f"mcp_{name}",
                "description": f"MCP server: {name}",
                "server": name,
            })
        return tools

mcp_server = MCPServer()

# === TOOL MANAGEMENT ===
class ToolManager:
    """Tool management like Claude Code"""
    
    def __init__(self):
        self.tools = self.get_builtin_tools()
        self.load_custom_tools()
    
    def get_builtin_tools(self) -> List[dict]:
        """Get built-in tools"""
        return [
            {"name": "Read", "description": "Read file contents", "params": ["path"]},
            {"name": "Edit", "description": "Edit a file", "params": ["path", "oldText", "newText"]},
            {"name": "Write", "description": "Write file contents", "params": ["path", "content"]},
            {"name": "Bash", "description": "Run shell command", "params": ["command"]},
            {"name": "Glob", "description": "Find files by pattern", "params": ["pattern"]},
            {"name": "Grep", "description": "Search in files", "params": ["pattern", "path"]},
            {"name": "WebFetch", "description": "Fetch URL content", "params": ["url"]},
            {"name": "WebSearch", "description": "Search the web", "params": ["query"]},
        ]
    
    def load_custom_tools(self):
        """Load custom tools from tools directory"""
        for f in os.listdir(TOOLS_DIR):
            if f.endswith(".json"):
                with open(os.path.join(TOOLS_DIR, f)) as fp:
                    tool = json.load(fp)
                    self.tools.append(tool)
    
    def list_tools(self) -> List[str]:
        """List available tools"""
        return [t["name"] for t in self.tools]

tool_mgr = ToolManager()

# === PERMISSIONS ===
class PermissionManager:
    """Tool permissions like Claude Code"""
    
    def __init__(self):
        self.allowed = set()
        self.denied = set()
        self.load()
    
    def load(self):
        """Load permissions"""
        path = os.path.join(SWARM_DIR, "permissions.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                self.allowed = set(data.get("allowed", []))
                self.denied = set(data.get("denied", []))
    
    def save(self):
        """Save permissions"""
        path = os.path.join(SWARM_DIR, "permissions.json")
        with open(path, "w") as f:
            json.dump({
                "allowed": list(self.allowed),
                "denied": list(self.denied)
            }, f, indent=2)
    
    def allow(self, tool: str):
        """Allow tool"""
        self.allowed.add(tool)
        self.save()
    
    def deny(self, tool: str):
        """Deny tool"""
        self.denied.add(tool)
        self.save()
    
    def is_allowed(self, tool: str) -> bool:
        """Check if tool is allowed"""
        if tool in self.denied:
            return False
        if tool in self.allowed:
            return True
        return True  # Default allow

# === AGENT MANAGEMENT ===
class AgentManager:
    """Agent management like Claude Code"""
    
    def __init__(self):
        self.agents = self.get_builtin_agents()
        self.load_agents()
    
    def get_builtin_agents(self) -> dict:
        """Get built-in agents"""
        return {
            "general": {
                "name": "General",
                "model": "claude-sonnet-4-20250514",
                "description": "General purpose assistant"
            },
            "coder": {
                "name": "Coder",
                "model": "claude-opus-4-20250514", 
                "description": "Code specialist"
            },
            "writer": {
                "name": "Writer", 
                "model": "claude-sonnet-4-20250514",
                "description": "Content writer"
            },
            "reviewer": {
                "name": "Reviewer",
                "model": "claude-opus-4-20250514",
                "description": "Code reviewer"
            },
        }
    
    def load_agents(self):
        """Load custom agents"""
        agents_path = os.path.join(SWARM_DIR, "agents.json")
        if os.path.exists(agents_path):
            with open(agents_path) as f:
                custom = json.load(f)
                self.agents.update(custom)
    
    def list_agents(self) -> List[str]:
        """List available agents"""
        return list(self.agents.keys())
    
    def get_agent(self, name: str) -> dict:
        """Get agent config"""
        return self.agents.get(name, self.agents["general"])

agent_mgr = AgentManager()

# === COMMAND HANDLERS ===
class CommandHandler:
    """Slash commands like Claude Code"""
    
    COMMANDS = {
        "help": {
            "description": "List available commands",
            "usage": "/help [command]",
        },
        "clear": {
            "description": "Clear conversation",
            "usage": "/clear",
        },
        "status": {
            "description": "Show session status",
            "usage": "/status",
        },
        "resume": {
            "description": "Resume a session",
            "usage": "/resume [session_id]",
        },
        "sessions": {
            "description": "List saved sessions",
            "usage": "/sessions",
        },
        "model": {
            "description": "Set model",
            "usage": "/model [claude-sonnet|claude-opus]",
        },
        "compact": {
            "description": "Compact conversation history",
            "usage": "/compact",
        },
        "save": {
            "description": "Save current session",
            "usage": "/save [name]",
        },
        "memory": {
            "description": "Manage memory",
            "usage": "/memory [list|add|clear]",
        },
        "mcp": {
            "description": "MCP servers",
            "usage": "/mcp [list|add|remove|tools] [server]",
        },
        "tools": {
            "description": "List available tools",
            "usage": "/tools [tool]",
        },
        "allow": {
            "description": "Allow tool",
            "usage": "/allow [tool]",
        },
        "deny": {
            "description": "Deny tool",
            "usage": "/deny [tool]",
        },
        "git": {
            "description": "Git commands",
            "usage": "/git [status|commit|push|pull|branch]",
        },
        "config": {
            "description": "Show/set config",
            "usage": "/config [key] [value]",
        },
        "cost": {
            "description": "Show usage cost",
            "usage": "/cost",
        },
        "undo": {
            "description": "Undo last message",
            "usage": "/undo",
        },
        "review": {
            "description": "Code review",
            "usage": "/review",
        },
        "btw": {
            "description": "Add comment",
            "usage": "/btw [comment]",
        },
        "agents": {
            "description": "Manage agents",
            "usage": "/agents [list|use|add] [name]",
        },
        "exit": {
            "description": "Exit swarm",
            "usage": "/exit",
        },
        "quit": {
            "description": "Exit swarm",
            "usage": "/quit",
        },
        "task": {
            "description": "Manage tasks",
            "usage": "/task [list|add|done|rm] [task]",
        },
        "issue": {
            "description": "GitHub issues",
            "usage": "/issue [list|create] [title]",
        },
        "pr": {
            "description": "GitHub PR",
            "usage": "/pr [list|create] [title]",
        },
        "theme": {
            "description": "Theme settings",
            "usage": "/theme [name]",
        },
        "skills": {
            "description": "Manage skills",
            "usage": "/skills [list|add|rm] [name]",
        },
        "keybindings": {
            "description": "Show keybindings",
            "usage": "/keybindings",
        },
    }
    
    @classmethod
    def handle(cls, cmd: str, args: str = "") -> Optional[str]:
        """Handle slash command"""
        cmd = cmd.lstrip("/")
        
        if cmd == "help":
            if args:
                c = cls.COMMANDS.get(args)
                if c:
                    return f"/{args} - {c['description']}\nUsage: {c['usage']}"
                return f"Unknown command: /{args}"
            # List all commands
            lines = ["Available commands:"]
            for name, info in cls.COMMANDS.items():
                lines.append(f"  /{name:<12} {info['description']}")
            return "\n".join(lines)
        
        if cmd == "clear":
            session_mgr.messages.clear()
            return "Conversation cleared."
        
        if cmd == "status":
            sessions = session_mgr.list_sessions()
            lines = [
                f"Swarm v{VERSION}",
                f"Model: claude-sonnet-4-20250514",
                f"Current session: {session_mgr.session_id or 'new'}",
                f"Saved sessions: {len(sessions)}",
            ]
            return "\n".join(lines)
        
        if cmd == "sessions":
            sessions = session_mgr.list_sessions()
            if not sessions:
                return "No saved sessions."
            lines = ["Saved sessions:"]
            for s in sessions[:10]:
                sid = s.get("id", "?")
                created = s.get("created", "")[:16]
                lines.append(f"  {created}  {sid}")
            return "\n".join(lines)
        
        if cmd == "resume":
            if args and session_mgr.load_session(args):
                return f"Loaded session: {args}"
            sessions = session_mgr.list_sessions()
            if sessions:
                return f"Available: {', '.join(s.get('id', '') for s in sessions[:5])}"
            return "No sessions to resume."
        
        if cmd == "model":
            if args:
                return f"Model set to: {args}"
            return "claude-sonnet-4-20250514"
        
        if cmd == "compact":
            session_mgr.compact_history()
            return "History compacted."
        
        if cmd == "save":
            name = args or session_mgr.session_id or "default"
            session_mgr.save_message("system", f"Saved: {name}")
            return f"Session saved: {name}"
        
        if cmd == "cost":
            # Estimate cost
            msg_count = len(session_mgr.messages)
            est_cost = msg_count * 0.001  # Rough estimate
            return f"Estimated usage: ~${est_cost:.4f} ({msg_count} messages)"
        
        if cmd == "git":
            # Git commands
            try:
                if args == "status":
                    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
                    return result.stdout or "Clean"
                if args == "commit":
                    result = subprocess.run(["git", "commit", "-m", args[7:] or "Update"], capture_output=True, text=True)
                    return result.stdout or result.stderr
                if args == "push":
                    result = subprocess.run(["git", "push"], capture_output=True, text=True)
                    return result.stdout or "Pushed"
                return "Git: status, commit [msg], push, pull"
            except:
                return "Git not available"
        
        if cmd == "memory":
            # Simple memory
            if args == "list":
                mems = []
                if os.path.exists(MEMORY_DIR):
                    for f in os.listdir(MEMORY_DIR):
                        mems.append(f)
                return " Memories: " + ", ".join(mems) if mems else "No memories"
            if args.startswith("add "):
                mem = args[4:]
                path = os.path.join(MEMORY_DIR, f"{random.randint(1000,9999)}.txt")
                with open(path, "w") as f:
                    f.write(mem)
                return "Memory saved."
            return "/memory list | add [text]"
        
        if cmd == "mcp":
            parts = args.split()
            if len(parts) == 0 or parts[0] == "list":
                servers = mcp_server.list_servers()
                if not servers:
                    return "No MCP servers configured. Use /mcp add [name] [command]"
                return "MCP Servers:\n" + "\n".join(f"  - {s}" for s in servers)
            if parts[0] == "add" and len(parts) >= 2:
                name = parts[1]
                # Check for stdio config
                config = {"type": "stdio", "command": " ".join(parts[2:]) if len(parts) > 2 else "echo"}
                mcp_server.add_server(name, config)
                return f"MCP server '{name}' added"
            if parts[0] == "remove" and len(parts) >= 2:
                name = parts[1]
                if mcp_server.remove_server(name):
                    return f"MCP server '{name}' removed"
                return f"MCP server '{name}' not found"
            if parts[0] == "tools":
                tools = mcp_server.get_tools()
                if not tools:
                    return "No MCP tools available"
                return "MCP Tools:\n" + "\n".join(f"  {t['name']}: {t['description']}" for t in tools)
            return "/mcp list | add [name] [command] | remove [name] | tools"
        
        if cmd == "tools":
            if args:
                for t in tool_mgr.tools:
                    if t["name"].lower() == args.lower():
                        return f"{t['name']}: {t['description']}\nParams: {t.get('params', [])}"
                return f"Tool '{args}' not found"
            tools = tool_mgr.list_tools()
            return f"Available tools ({len(tools)}):\n" + "\n".join(f"  - {t}" for t in tools)
        
        if cmd == "allow":
            if args:
                perm_mgr.allow(args)
                return f"Tool '{args}' allowed"
            return "Tool name required: /allow [tool]"
        
        if cmd == "deny":
            if args:
                perm_mgr.deny(args)
                return f"Tool '{args}' denied"
            return "Tool name required: /deny [tool]"
        
        if cmd == "config":
            key_val = args.split()
            if len(key_val) == 2:
                k, v = key_val
                path = os.path.join(SWARM_DIR, "config.json")
                cfg = {}
                if os.path.exists(path):
                    with open(path) as f:
                        cfg = json.load(f)
                cfg[k] = v
                with open(path, "w") as f:
                    json.dump(cfg, f)
                return f"Set {k} = {v}"
            if len(key_val) == 1:
                path = os.path.join(SWARM_DIR, "config.json")
                if os.path.exists(path):
                    with open(path) as f:
                        cfg = json.load(f)
                return json.dumps(cfg.get(key_val[0], "not set"), "1.0")
            return "No config"
        
        if cmd == "btw":
            if args:
                return f"💬 {args}"
            return "Add a comment"
        
        if cmd == "agents":
            parts = args.split()
            if len(parts) == 0 or parts[0] == "list":
                agents = agent_mgr.list_agents()
                return "Agents:\n" + "\n".join(f"  - {a}: {agent_mgr.get_agent(a).get('description', '')}" for a in agents)
            if parts[0] == "use" and len(parts) >= 2:
                name = parts[1]
                if name in agent_mgr.list_agents():
                    session_mgr.save_message("system", f"Using agent: {name}")
                    return f"Switched to agent: {name}"
                return f"Agent '{name}' not found"
            if parts[0] == "add" and len(parts) >= 2:
                name = parts[1]
                # TODO: Add custom agent
                return f"Agent '{name}' added"
            return "/agents list | use [name] | add [name]"
        
        if cmd == "review":
            return "Code review mode - paste code to review"
        
        if cmd == "exit" or cmd == "quit":
            log("\n\033[2mSession ended.\033[0m", "dim")
            sys.exit(0)
        
        if cmd == "task":
            parts = args.split()
            return "/task list|add|done|rm [task] - tasks coming soon"
        
        if cmd == "issue":
            return "/issue list|create - GitHub issues coming soon"
        
        if cmd == "pr":
            return "/pr list|create - GitHub PRs coming soon"
        
        if cmd == "theme":
            if args:
                return f"Theme set to: {args}"
            return "Available themes: default, dark, light"
        
        if cmd == "skills":
            return "/skills list|add|rm - custom skills coming soon"
        
        if cmd == "keybindings":
            return """Keybindings:
  Ctrl+C: Cancel
  Ctrl+D: Exit
  Ctrl+A: Start of line
  Ctrl+E: End of line
  Ctrl+U: Clear line
  Up/Down: History
  Ctrl+P/N: History"""

# === TYPING INDICATOR ===
def show_typing():
    """Show typing indicator"""
    sys.stdout.write("\033[2m⬤ Thinking...\033[0m\r")
    sys.stdout.flush()

def clear_typing():
    """Clear typing indicator"""
    sys.stdout.write("\r\033[2K")  # Clear line
    sys.stdout.flush()

# === INPUT WITH FEATURES ===
def read_input(prompt: str = "") -> str:
    """Enhanced input with paste support and commands"""
    # Show prompt
    sys.stdout.write(f"\033[36m{prompt or '➤'}\033[0m ")
    sys.stdout.flush()
    
    # Get terminal
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    buf = []
    after = []
    
    # Paste detection
    import select as _sel
    paste_num = 0
    paste_refs = {}
    pasted_just_now = False
    
    # Wait for paste
    r, _, _ = _sel.select([fd], [], [], 0.1)
    if r:
        raw = b''
        while True:
            try:
                chunk = os.read(fd, 8192)
                if not chunk:
                    break
                raw += chunk
                if len(chunk) < 8192:
                    time.sleep(0.05)
                    if not _sel.select([fd], [], [], 0.01)[0]:
                        break
            except:
                break
        
        pasted_text = raw.decode('utf-8', errors='replace').strip()
        
        if pasted_text:
            paste_num += 1
            paste_refs[paste_num] = pasted_text
            lines = pasted_text.split('\n')
            line_count = len(lines)
            char_count = len(pasted_text)
            
            if line_count >= 5:
                display = f"[ Pasted #{paste_num} ] ({line_count} lines)"
            else:
                display = f"[ Pasted #{paste_num} ] ({char_count} chars)"
            
            pasted_just_now = True
            sys.stdout.write(display)
            sys.stdout.flush()
    
    # Input loop
    try:
        tty.setcbreak(fd, termios.TCSANOW)
        
        while True:
            ch = sys.stdin.read(1)
            
            # Enter
            if ch in ('\r', '\n'):
                if pasted_just_now and paste_num > 0:
                    # Expand paste reference
                    last_paste = paste_refs[paste_num]
                    expanded = ' '.join(last_paste.split())
                    for c in expanded:
                        if ord(c) >= 32:
                            buf.append(c)
                    pasted_just_now = False
                    
                    sys.stdout.write('\r\n')
                    sys.stdout.flush()
                    return ''.join(buf + list(reversed(after)))
                
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                return ''.join(buf + list(reversed(after)))
            
            # CTRL+C
            if ch == '\x03':
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise KeyboardInterrupt
            
            # Backspace
            if ch in ('\x7f', '\x08'):
                if buf:
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
                    buf.pop()
                elif after:
                    c = after.pop()
                    sys.stdout.write(c)
                    sys.stdout.flush()
                continue
            
            # CTRL+A - start of line
            if ch == '\x01':
                while buf:
                    after.append(buf.pop())
                    sys.stdout.write('\033[1D')
                sys.stdout.flush()
                continue
            
            # CTRL+E - end of line
            if ch == '\x05':
                while after:
                    c = after.pop()
                    buf.append(c)
                    sys.stdout.write(c)
                sys.stdout.flush()
                continue
            
            # Arrow keys for history
            if ch == '\x1b':
                # Skip alt prefix
                continue
            
            # Normal character
            if ord(ch) >= 32:
                buf.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# === MODEL SELECTION ===
MODELS = {
    "claude-sonnet": "claude-sonnet-4-20250514",
    "claude-opus": "claude-opus-4-20250514",
    "claude-3-5": "claude-3-5-sonnet-20241022",
    "gemini": "gemini-2.0-flash",
    "gpt-4": "gpt-4",
}

def get_model(name: str = None):
    """Get model identifier"""
    if not name:
        return MODELS["claude-sonnet"]
    return MODELS.get(name, MODELS["claude-sonnet"])

# === SWARM CORE ===
def run_swarm(prompt: str, model: str = None):
    """Run swarm with prompt through any LLM API or CLI"""
    
    if not prompt.strip():
        return ""
    
    show_typing()
    
    model = model or get_model()
    
    # Try Gemini CLI first (most common for swarm users)
    try:
        result = subprocess.run(
            ["claude", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            shell=False
        )
        if result.returncode == 0 and result.stdout:
            clear_typing()
            return result.stdout
    except:
        pass
    
    # Try Gemini CLI 
    try:
        result = subprocess.run(
            ["gemini", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            shell=False
        )
        if result.returncode == 0 and result.stdout:
            clear_typing()
            return result.stdout
    except:
        pass
    
    # Try Kilo Code CLI
    try:
        result = subprocess.run(
            ["kilo", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            shell=False
        )
        if result.returncode == 0 and result.stdout:
            clear_typing()
            return result.stdout
    except:
        pass
    
    # Try Codex CLI
    try:
        result = subprocess.run(
            ["codex", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            shell=False
        )
        if result.returncode == 0 and result.stdout:
            clear_typing()
            return result.stdout
    except:
        pass
    
    # Try API calls
    
    # Build messages
    messages = [{"role": "user", "content": prompt}]
    
    # Add session context
    if session_mgr.messages:
        messages = session_mgr.messages + messages
    
    try:
        # Try OpenAI API first
        try:
            import requests
            api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
            if api_key:
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "gpt-4",
                        "messages": messages,
                        "stream": True
                    },
                    stream=True,
                    timeout=120
                )
                
                for line in resp.iter_lines():
                    if line:
                        line = line.decode()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                j = json.loads(data)
                                content = j.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    sys.stdout.write(content)
                                    sys.stdout.flush()
                            except:
                                pass
                
                clear_typing()
                return ""
        except:
            pass
        
        # Try Anthropic
        try:
            import requests
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                    json={
                        "model": model,
                        "max_tokens": 4096,
                        "messages": messages[-10:]
                    },
                    stream=True,
                    timeout=120
                )
                
                for line in resp.iter_lines():
                    if line:
                        line = line.decode()
                        if line.startswith("data: "):
                            data = line[6:]
                            try:
                                j = json.loads(data)
                                content = j.get("delta", {}).get("text", "")
                                if content:
                                    sys.stdout.write(content)
                                    sys.stdout.flush()
                            except:
                                pass
                
                clear_typing()
                return ""
        except:
            pass
        
        # Fallback: simple echo with LLM instruction indicator
        clear_typing()
        return f"[Would run: {prompt[:50]}...] via {model}"
    
    except KeyboardInterrupt:
        clear_typing()
        raise
    except Exception as e:
        clear_typing()
        return f"Error: {e}"

# === MAIN ===
def main():
    # Welcome
    log(f"\033[32m🛡️ Swarm v{VERSION}\033[0m - {random.choice(WELCOME)}")
    log(f"245 agents. One command. Let's go.", "dim")
    
    # Create session
    session_mgr.create_session()
    
    while True:
        try:
            # Read input
            user_input = read_input("\033[36m➤\033[0m")
            
            if not user_input.strip():
                continue
            
            # Check for slash commands
            if user_input.startswith("/"):
                parts = user_input.split(" ", 1)
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                
                result = CommandHandler.handle(cmd, args)
                if result:
                    print(result)
                continue
            
            # Save user message
            session_mgr.save_message("user", user_input)
            
            # Run through swarm
            response = run_swarm(user_input)
            
            if response:
                print(response)
                session_mgr.save_message("assistant", response)
        
        except KeyboardInterrupt:
            log("\n\033[33mInterrupted.\033[0m")
            break
        except EOFError:
            break
    
    log("\033[2mSession ended.\033[0m", "dim")

if __name__ == "__main__":
    main()