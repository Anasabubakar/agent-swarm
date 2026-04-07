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
            "usage": "/mcp [list|add|remove] [server]",
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
            return "MCP servers: none configured (use /mcp add [server])"
        
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
        
        if cmd == "review":
            return "Code review mode - paste code to review"
        
        # Unknown command
        return f"Unknown: /{cmd}. Use /help for commands."

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
    """Run swarm with prompt through any LLM API"""
    
    # Build messages
    messages = [{"role": "user", "content": prompt}]
    
    # Add session context
    if session_mgr.messages:
        messages = session_mgr.messages + messages
    
    model = model or get_model()
    
    show_typing()
    
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