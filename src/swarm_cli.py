#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║   ███████╗██╗    ██╗ █████╗ ██████╗  ║
║   ██╔════╝██║    ██║██╔══██╗██╔══██╗ ║
║   ███████╗██║ █╗ ██║███████║██████╔╝ ║
║   ╚════██║██║███╗██║██╔══██║██╔══██╗ ║
║   ███████║╚███╔███╔╝██║  ██║██║  ██║ ║
║   ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ║
║   Interactive AI + Agent Swarm        ║
║   by Anas Abubakar • v1.0.3           ║
╚══════════════════════════════════════╝
"""

import sys
import os
import json
import subprocess
import threading
import itertools
import time
import tty
import termios
import select
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════
# PATHS
# ═══════════════════════════════════════

SWARM_ROOT = Path(os.environ.get("SWARM_ROOT", Path(__file__).parent.parent))
CONFIG_FILE = SWARM_ROOT / "swarm.config.json"
VERSION = "1.0.3"

# ═══════════════════════════════════════
# COLORS
# ═══════════════════════════════════════

class C:
    R = "\033[0m"
    B = "\033[1m"
    D = "\033[2m"
    RED = "\033[91m"
    GRN = "\033[92m"
    YLW = "\033[93m"
    BLU = "\033[94m"
    MAG = "\033[95m"
    CYN = "\033[96m"
    WHT = "\033[97m"
    
    @staticmethod
    def t(c, text): return f"{c}{text}{C.R}"

# ═══════════════════════════════════════
# SLASH COMMANDS WITH DESCRIPTIONS
# ═══════════════════════════════════════

SLASH_COMMANDS = [
    ("/help",        "Show all commands"),
    ("/model",       "Change AI engine"),
    ("/model list",  "List available models"),
    ("/employee",    "Choose a specific agent"),
    ("/employee list", "Browse all 245 agents"),
    ("/read <file>", "Read a file"),
    ("/ls [dir]",    "List directory"),
    ("/find <pat>",  "Find files"),
    ("/grep <text>", "Search in files"),
    ("/run <cmd>",   "Run a shell command"),
    ("/memory",      "Show chat history"),
    ("/memory clear","Clear chat history"),
    ("/update",      "Check for updates"),
    ("/permissions", "Manage permissions"),
    ("/workspace",   "Show workspace info"),
    ("/credits",     "Show credits"),
    ("/quit",        "Exit swarm"),
]

# ═══════════════════════════════════════
# AUTOCOMPLETE INPUT
# ═══════════════════════════════════════

class AutoCompleteInput:
    """
    Input with slash command autocomplete.
    When user types '/', shows dropdown of available commands.
    Arrow keys to navigate, Enter to select, ESC to dismiss.
    """
    
    def __init__(self, prompt_text="▸ "):
        self.prompt = prompt_text
        self.buffer = ""
        self.dropdown_visible = False
        self.dropdown_selected = 0
        self.dropdown_items = []
        self.dropdown_offset = 0  # Lines drawn by dropdown
    
    def _get_filtered_commands(self, prefix: str) -> list:
        """Filter commands matching the prefix"""
        if not prefix:
            return SLASH_COMMANDS
        return [(cmd, desc) for cmd, desc in SLASH_COMMANDS if cmd.startswith(prefix)]
    
    def _draw_dropdown(self):
        """Draw the dropdown menu above the prompt"""
        self._clear_dropdown()
        
        if not self.dropdown_items:
            self.dropdown_visible = False
            return
        
        self.dropdown_visible = True
        lines = []
        
        for i, (cmd, desc) in enumerate(self.dropdown_items[:8]):
            if i == self.dropdown_selected:
                line = f"    {C.t(C.GRN, '▸')} {C.t(C.B + C.WHT, cmd):<22} {C.t(C.D, desc)}"
            else:
                line = f"      {C.t(C.D, cmd):<22} {C.t(C.D, desc)}"
            lines.append(line)
        
        # Draw above cursor
        num_lines = len(lines)
        sys.stdout.write(f"\033[{num_lines}B")  # Move down
        for line in reversed(lines):
            sys.stdout.write(f"\r\033[K{line}\033[1A")  # Clear line, write, move up
        sys.stdout.write(f"\r\033[K")  # Clear the bottom line
        sys.stdout.flush()
        
        self.dropdown_offset = num_lines
    
    def _clear_dropdown(self):
        """Clear previously drawn dropdown"""
        if self.dropdown_offset > 0:
            for _ in range(self.dropdown_offset):
                sys.stdout.write("\033[1A\r\033[K")
            sys.stdout.flush()
            self.dropdown_offset = 0
        self.dropdown_visible = False
    
    def _redraw_prompt(self):
        """Redraw the current prompt with buffer"""
        sys.stdout.write(f"\r\033[K{self.prompt}{self.buffer}")
        sys.stdout.flush()
    
    def read(self) -> str:
        """Read a line with autocomplete support"""
        self.buffer = ""
        self.dropdown_visible = False
        self.dropdown_selected = 0
        self.dropdown_offset = 0
        
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            sys.stdout.write(self.prompt)
            sys.stdout.flush()
            
            while True:
                # Wait for input
                r, _, _ = select.select([fd], [], [], 0.1)
                if not r:
                    continue
                
                ch = sys.stdin.read(1)
                
                # Enter
                if ch in ('\r', '\n'):
                    self._clear_dropdown()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return self.buffer
                
                # CTRL+C
                if ch == '\x03':
                    self._clear_dropdown()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                
                # CTRL+D / EOF
                if ch == '\x04':
                    self._clear_dropdown()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    raise EOFError
                
                # ESC — dismiss dropdown
                if ch == '\x1b':
                    # Check for arrow keys
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if self.dropdown_visible and self.dropdown_items:
                            if ch3 == 'A':  # Up
                                self.dropdown_selected = max(0, self.dropdown_selected - 1)
                                self._draw_dropdown()
                                self._redraw_prompt()
                                continue
                            elif ch3 == 'B':  # Down
                                self.dropdown_selected = min(len(self.dropdown_items) - 1, self.dropdown_selected + 1)
                                self._draw_dropdown()
                                self._redraw_prompt()
                                continue
                    # ESC without arrow — dismiss dropdown
                    self._clear_dropdown()
                    self._redraw_prompt()
                    continue
                
                # Tab — select current dropdown item
                if ch == '\t':
                    if self.dropdown_visible and self.dropdown_items:
                        self.buffer = self.dropdown_items[self.dropdown_selected][0]
                        self._clear_dropdown()
                        self._redraw_prompt()
                    continue
                
                # Backspace
                if ch in ('\x7f', '\b'):
                    if self.buffer:
                        self.buffer = self.buffer[:-1]
                        self._redraw_prompt()
                        # Update dropdown
                        if self.buffer.startswith('/'):
                            self.dropdown_items = self._get_filtered_commands(self.buffer)
                            self.dropdown_selected = 0
                            self._draw_dropdown()
                            self._redraw_prompt()
                        else:
                            self._clear_dropdown()
                    continue
                
                # Regular character
                self.buffer += ch
                sys.stdout.write(ch)
                sys.stdout.flush()
                
                # Show dropdown when typing /
                if self.buffer == '/':
                    self.dropdown_items = SLASH_COMMANDS
                    self.dropdown_selected = 0
                    self._draw_dropdown()
                    self._redraw_prompt()
                elif self.buffer.startswith('/') and len(self.buffer) > 1:
                    self.dropdown_items = self._get_filtered_commands(self.buffer)
                    self.dropdown_selected = 0
                    if self.dropdown_items:
                        self._draw_dropdown()
                        self._redraw_prompt()
                    else:
                        self._clear_dropdown()
                elif self.dropdown_visible:
                    self._clear_dropdown()
                    self._redraw_prompt()
        
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ═══════════════════════════════════════
# REST OF THE CLI (same as before, trimmed)
# ═══════════════════════════════════════

class FileReader:
    @staticmethod
    def read(path):
        try:
            p = Path(path)
            if not p.exists(): return f"Not found: {path}"
            if p.is_dir():
                items = [f"  {'📁' if x.is_dir() else '📄'} {x.name}" for x in sorted(p.iterdir()) if not x.name.startswith('.')][:30]
                return f"{path}:\n" + '\n'.join(items)
            content = p.read_text(errors='replace')
            lines = content.split('\n')
            if len(lines) > 100:
                return '\n'.join(lines[:100]) + f"\n\n... ({len(lines)-100} more)"
            return content
        except Exception as e:
            return f"Error: {e}"
    
    @staticmethod
    def find(pattern, dir="."):
        try:
            matches = list(Path(dir).rglob(pattern))
            if not matches: return f"No matches: {pattern}"
            return '\n'.join(f"  {m.relative_to(dir)}" for m in matches[:20])
        except: return "Error searching"
    
    @staticmethod
    def search(query, dir="."):
        results = []
        for ext in ['.py', '.js', '.ts', '.tsx', '.md', '.json']:
            for f in Path(dir).rglob(f"*{ext}"):
                if '.git' in str(f) or 'node_modules' in str(f): continue
                try:
                    for i, line in enumerate(f.read_text(errors='replace').split('\n'), 1):
                        if query.lower() in line.lower():
                            results.append(f"  {f.relative_to(dir)}:{i}: {line.strip()[:60]}")
                            if len(results) >= 15: break
                except: pass
                if len(results) >= 15: break
        return '\n'.join(results) if results else f"No matches: {query}"


class PermissionManager:
    def __init__(self, cwd="."):
        self.file = Path(cwd) / ".swarm-permissions.json"
        self.always = set()
        if self.file.exists():
            try: self.always = set(json.loads(self.file.read_text()).get("always", []))
            except: pass
    
    def save(self):
        self.file.write_text(json.dumps({"always": list(self.always)}))
    
    def ask(self, action, desc):
        if action in self.always: return "yes"
        print(f"\n  {C.t(C.YLW, '⚠ Permission')}")
        print(f"  {C.t(C.D, desc)}")
        print(f"\n  {C.t(C.CYN, '[y]')} Yes  {C.t(C.CYN, '[a]')} Always allow  {C.t(C.CYN, '[n]')} No\n")
        
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
            self.always.add(action)
            self.save()
        return {"y": "yes", "a": "yes", "n": "no"}.get(ch, "no")


class ActionDetector:
    GREETINGS = ["hi","hello","hey","yo","sup","wassup","what's up","haffa","wetin dey","good morning","good afternoon","good evening","how far","oya"]
    BUILD_KW = ["build a","create a","make a","develop a","scaffold a","setup a","landing page","website","web app","api","dashboard","todo app","todo list"]
    FILE_KW = ["read ","open ","show me ","cat ","view ","look at "]
    CMD_KW = ["run ","execute ","install ","npm ","pip ","docker ","git ","yarn "]
    
    @staticmethod
    def detect(text):
        t = text.lower().strip()
        w = t.split()
        if len(w) <= 2:
            for g in ActionDetector.GREETINGS:
                if g in t: return "chat"
        for kw in ActionDetector.FILE_KW:
            if kw in t: return "file"
        for kw in ActionDetector.CMD_KW:
            if t.startswith(kw): return "cmd"
        if t in ['ls','dir','pwd']: return "cmd"
        if len(w) >= 3:
            for kw in ActionDetector.BUILD_KW:
                if kw in t: return "build"
        return "question"


def run_swarm(goal, engine, cwd):
    cmd = [sys.executable, str(SWARM_ROOT / "orchestrator.py")]
    if engine != "auto": cmd.extend(["--engine", engine])
    cmd.append(goal)
    try:
        proc = subprocess.Popen(cmd, cwd=cwd)
        proc.wait(timeout=600)
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"  {C.t(C.RED, '✗ Timeout')}")
        return False
    except KeyboardInterrupt:
        proc.kill()
        print(f"\n  {C.t(C.YLW, '⏸ Cancelled')}")
        return False


def check_update(ver):
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://raw.githubusercontent.com/Anasabubakar/agent-swarm/main/package.json',
            headers={'User-Agent': 'swarm'}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            remote = json.loads(r.read()).get("version", "0.0.0")
            return remote if remote != ver else None
    except: return None


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    cwd = os.getcwd()
    engine = "auto"
    memory_file = Path(cwd) / ".swarm-chat.json"
    messages = []
    if memory_file.exists():
        try: messages = json.loads(memory_file.read_text())
        except: pass
    permissions = PermissionManager(cwd)
    
    # Detect engines
    import shutil
    engines_map = {"claude":"claude","gemini":"gemini","kilo":"kilo","codex":"codex","aider":"aider"}
    installed = [k for k,v in engines_map.items() if shutil.which(v)]
    if installed:
        engine = installed[0]
    
    # Check update
    new_ver = check_update(VERSION)
    if new_ver:
        print(f"\n  {C.t(C.YLW, f'⚠ Update: v{VERSION} → v{new_ver}')}")
        print(f"  {C.t(C.D, 'Run: cd ~/.swarm && git pull')}\n")
    
    # Banner
    print(f"""
{C.t(C.B + C.CYN, '  ╔══════════════════════════════════════╗')}
{C.t(C.B + C.CYN, '  ║  ███████╗██╗    ██╗ █████╗ ██████╗   ║')}
{C.t(C.B + C.CYN, '  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗  ║')}
{C.t(C.B + C.CYN, '  ║  ███████╗██║ █╗ ██║███████║██████╔╝  ║')}
{C.t(C.B + C.CYN, '  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗  ║')}
{C.t(C.B + C.CYN, '  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║  ║')}
{C.t(C.B + C.CYN, '  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ║')}
{C.t(C.B + C.CYN, f'  ║  {C.t(C.WHT, f"v{VERSION} by Anas Abubakar")}{C.t(C.B + C.CYN, "       ║")}')}
{C.t(C.B + C.CYN, '  ╚══════════════════════════════════════╝')}
""")
    
    print(f"  {C.t(C.GRN, '✓')} Engine: {C.t(C.B, engine)}")
    print(f"  {C.t(C.D, 'Type / for commands • ESC or /quit to exit')}\n")
    
    input_handler = AutoCompleteInput(f"  {C.t(C.GRN, '▸')} ")
    
    while True:
        try:
            user_input = input_handler.read().strip()
            if not user_input: continue
            
            # Slash commands
            if user_input.startswith("/"):
                cmd = user_input
                
                if cmd in ["/quit", "/exit"]:
                    print(f"\n  {C.t(C.CYN, 'Goodbye! 🛡️')}\n")
                    break
                
                if cmd == "/help":
                    print(f"\n  {C.t(C.B + C.CYN, 'Commands')}")
                    print(f"  {C.t(C.D, '─'*35)}")
                    for c, d in SLASH_COMMANDS:
                        print(f"  {C.t(C.CYN, c):<22} {C.t(C.D, d)}")
                    print()
                    continue
                
                if cmd.startswith("/read "):
                    path = cmd[6:].strip()
                    print(f"\n  {C.t(C.BLU, f'📄 {path}')}")
                    print(f"  {C.t(C.D, '─'*35)}")
                    for line in FileReader.read(path).split('\n')[:30]:
                        print(f"  {C.t(C.D, '│')} {line}")
                    print()
                    continue
                
                if cmd.startswith("/ls"):
                    d = cmd[4:].strip() or "."
                    print(f"\n{FileReader.read(d)}\n")
                    continue
                
                if cmd.startswith("/find "):
                    print(f"\n{FileReader.find(cmd[6:].strip())}\n")
                    continue
                
                if cmd.startswith("/grep "):
                    print(f"\n{FileReader.search(cmd[6:].strip())}\n")
                    continue
                
                if cmd.startswith("/run "):
                    command = cmd[5:].strip()
                    safety = "dangerous" if any(command.lower().startswith(d) for d in ["rm","git push","npm install","pip install"]) else "safe"
                    if safety == "dangerous":
                        perm = permissions.ask("run_cmd", f"Run: {command}")
                        if perm == "no":
                            print(f"  {C.t(C.RED, 'Denied')}\n")
                            continue
                    try:
                        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120, cwd=cwd)
                        if r.stdout: print(f"\n{r.stdout}")
                        if r.stderr: print(f"  {C.t(C.RED, r.stderr[:200])}")
                        print()
                    except Exception as e:
                        print(f"  {C.t(C.RED, str(e))}\n")
                    continue
                
                if cmd == "/update":
                    new = check_update(VERSION)
                    if new:
                        print(f"\n  {C.t(C.YLW, f'Update: v{VERSION} → v{new}')}")
                        print(f"  {C.t(C.CYN, '[a]')} Auto-update  {C.t(C.CYN, '[m]')} Manual  {C.t(C.CYN, '[s]')} Skip\n")
                    else:
                        print(f"  {C.t(C.GRN, '✓')} Latest version\n")
                    continue
                
                if cmd == "/credits":
                    print(f"\n  {C.t(C.B + C.CYN, '═'*30)}")
                    print(f"  {C.t(C.B, '🛡️  Agent Swarm')}")
                    print(f"  {C.t(C.D, 'By:')} Anas Abubakar")
                    print(f"  {C.t(C.D, 'MIT License • v' + VERSION)}")
                    print(f"  {C.t(C.B + C.CYN, '═'*30)}\n")
                    continue
                
                if cmd == "/memory":
                    if not messages:
                        print(f"  {C.t(C.D, 'No history yet')}\n")
                    else:
                        print(f"\n  {C.t(C.B, f'History ({len(messages)})')}")
                        for m in messages[-8:]:
                            icon = "▸" if m["role"] == "user" else "◂"
                            print(f"  {C.t(C.WHT if m['role']=='user' else C.CYN, icon)} {m['content'][:60]}")
                        print()
                    continue
                
                if cmd == "/memory clear":
                    messages = []
                    memory_file.write_text("[]")
                    print(f"  {C.t(C.GRN, '✓')} Cleared\n")
                    continue
                
                if cmd.startswith("/model"):
                    print(f"\n  {C.t(C.B, 'Engines:')} {', '.join(installed) if installed else 'none found'}")
                    print(f"  {C.t(C.D, 'Type /model <name> to switch')}\n")
                    continue
                
                if cmd.startswith("/employee"):
                    print(f"  {C.t(C.D, 'Type /employee list to browse 245 agents')}\n")
                    continue
                
                print(f"  {C.t(C.RED, f'Unknown: {cmd}')}  /help\n")
                continue
            
            # Regular input
            action = ActionDetector.detect(user_input)
            messages.append({"role": "user", "content": user_input, "time": datetime.now().isoformat()})
            
            if action == "chat":
                replies = {
                    "yo": "Yo! What's good? 👋", "hi": "Hey! Ready to work. 🛡️",
                    "hello": "Hello! What do you need?", "hey": "Hey hey!",
                    "sup": "Not much, waiting on you 😄", "haffa": "Haffa! Wetin dey?",
                    "how far": "I dey! What you need?",
                }
                reply = replies.get(user_input.lower().strip(), "Hey! What do you need?")
                print(f"\n  {reply}\n")
                messages.append({"role": "assistant", "content": reply})
            
            elif action == "question":
                print(f"\n  {C.t(C.BLU, '💡')} Connect your AI engine to answer questions.")
                print(f"  {C.t(C.D, 'Or give me a build task to use the swarm.')}\n")
                messages.append({"role": "assistant", "content": "Suggested engine connection"})
            
            elif action == "file":
                words = user_input.split()
                filename = None
                for i, w in enumerate(words):
                    if w in ['read','open','show','cat','view','look'] and i+1 < len(words):
                        filename = words[i+1]; break
                    if '.' in w and len(w) > 2: filename = w; break
                if filename:
                    print(f"\n  {C.t(C.BLU, f'📄 {filename}')}")
                    print(f"  {C.t(C.D, '─'*35)}")
                    for line in FileReader.read(filename).split('\n')[:30]:
                        print(f"  {C.t(C.D, '│')} {line}")
                    print()
                else:
                    print(f"  {C.t(C.YLW, 'Which file?')} /read <filename>\n")
            
            elif action == "cmd":
                cmd = user_input
                if cmd.lower().startswith("run "): cmd = cmd[4:].strip()
                elif cmd.lower() in ['ls','dir']: cmd = "ls -la"
                try:
                    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=cwd)
                    print()
                    if r.stdout:
                        for line in r.stdout.split('\n')[:20]: print(f"  {line}")
                    if r.stderr: print(f"  {C.t(C.RED, r.stderr[:200])}")
                    print()
                except Exception as e:
                    print(f"  {C.t(C.RED, str(e))}\n")
            
            elif action == "build":
                print()
                run_swarm(user_input, engine, cwd)
                print()
            
            # Save memory
            memory_file.write_text(json.dumps(messages[-100:], indent=2))
        
        except KeyboardInterrupt:
            print(f"\n")
            continue
        except EOFError:
            print()
            break


if __name__ == "__main__":
    main()
