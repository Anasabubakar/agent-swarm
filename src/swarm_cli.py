#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║   ███████╗██╗    ██╗ █████╗ ██████╗  ║
║   ██╔════╝██║    ██║██╔══██╗██╔══██╗ ║
║   ███████╗██║ █╗ ██║███████║██████╔╝ ║
║   ╚════██║██║███╗██║██╔══██║██╔══██╗ ║
║   ███████║╚███╔███╔╝██║  ██║██║  ██║ ║
║   ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ║
║   AI Assistant + Agent Swarm          ║
║   by Anas Abubakar • v1.0.4           ║
╚══════════════════════════════════════╝
"""

import sys, os, json, subprocess, shutil, tty, termios, select
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════
# SETUP
# ═══════════════════════════════════════

SWARM_ROOT = Path(os.environ.get("SWARM_ROOT", Path(__file__).parent.parent))
VERSION = "1.0.4"
CWD = os.getcwd()

class C:
    R="\033[0m"; B="\033[1m"; D="\033[2m"
    RED="\033[91m"; GRN="\033[92m"; YLW="\033[93m"
    BLU="\033[94m"; MAG="\033[95m"; CYN="\033[96m"; WHT="\033[97m"
    @staticmethod
    def t(c,t): return f"{c}{t}{C.R}"

# ═══════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════

CMDS = [
    ("help",          "Show all commands"),
    ("model",         "Change AI engine"),
    ("model list",    "List available models"),
    ("employee",      "Choose a specific agent"),
    ("employee list", "Browse all 245 agents"),
    ("read <file>",   "Read a file"),
    ("ls [dir]",      "List directory contents"),
    ("find <pat>",    "Find files matching pattern"),
    ("grep <text>",   "Search text in files"),
    ("run <cmd>",     "Run a shell command"),
    ("memory",        "Show chat history"),
    ("memory clear",  "Clear chat history"),
    ("update",        "Check for updates"),
    ("permissions",   "Manage permissions"),
    ("workspace",     "Show workspace info"),
    ("credits",       "Show credits"),
    ("quit",          "Exit swarm"),
]

# ═══════════════════════════════════════
# TERMINAL RAW MODE HELPER
# ═══════════════════════════════════════

class RawTerminal:
    def __enter__(self):
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setraw(self.fd)
        return self
    
    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
    
    def read_key(self):
        """Read a single key, returns (type, value)"""
        ch = sys.stdin.read(1)
        
        if ch == '\x1b':  # ESC or escape sequence
            # Check if more chars available (arrow keys)
            r, _, _ = select.select([self.fd], [], [], 0.05)
            if r:
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    return ("arrow", {"A":"up","B":"down","C":"right","D":"left"}.get(ch3, ""))
                return ("esc", "")
            return ("esc", "")
        
        if ch in ('\r', '\n'): return ("enter", "")
        if ch == '\t': return ("tab", "")
        if ch in ('\x7f', '\b'): return ("backspace", "")
        if ch == '\x03': return ("ctrl-c", "")
        if ch == '\x04': return ("ctrl-d", "")
        
        return ("char", ch)


# ═══════════════════════════════════════
# AUTOCOMPLETE INPUT (REWRITTEN)
# ═══════════════════════════════════════

class Input:
    """
    Clean autocomplete input.
    
    When typing '/':
    - Shows dropdown BELOW the prompt (no cursor jumping)
    - Replaces the dropdown in-place on each keystroke
    - Arrow keys navigate, Tab selects, ESC dismisses
    """
    
    def __init__(self, prompt="▸ "):
        self.prompt = prompt
        self.buffer = ""
        self.dropdown = []        # [(cmd, desc), ...]
        self.selected = 0
        self.showing_dd = False
        self.dd_lines = 0         # How many lines the dropdown occupies
    
    def _filter(self, prefix):
        if not prefix: return CMDS
        p = prefix[1:]  # Remove the '/'
        return [(c,d) for c,d in CMDS if c.startswith(p)]
    
    def _draw_prompt(self):
        sys.stdout.write(f"\r\033[K{self.prompt}{self.buffer}")
        sys.stdout.flush()
    
    def _draw_dropdown(self):
        """Draw dropdown BELOW the prompt line"""
        # First, clear any existing dropdown lines
        self._clear_dropdown()
        
        if not self.dropdown:
            self.showing_dd = False
            return
        
        self.showing_dd = True
        lines_to_draw = self.dropdown[:8]  # Max 8 items
        
        sys.stdout.write("\n")  # Move to next line after prompt
        
        for i, (cmd, desc) in enumerate(lines_to_draw):
            if i == self.selected:
                sys.stdout.write(f"  {C.t(C.GRN, '▸')} {C.t(C.B + C.WHT, '/' + cmd):<22} {C.t(C.D, desc)}\033[K\n")
            else:
                sys.stdout.write(f"    {C.t(C.D, '/' + cmd):<22} {C.t(C.D, desc)}\033[K\n")
        
        # Move cursor back up to prompt line
        self.dd_lines = len(lines_to_draw)
        sys.stdout.write(f"\033[{self.dd_lines}A")  # Move up
        sys.stdout.write(f"\r{self.prompt}{self.buffer}")  # Restore prompt
        sys.stdout.flush()
    
    def _clear_dropdown(self):
        """Clear the dropdown area"""
        if self.dd_lines == 0:
            return
        
        # We're at the prompt line. Move down through dropdown lines and clear each.
        for i in range(self.dd_lines):
            sys.stdout.write("\n\033[K")  # Move down and clear line
        
        # Move back up to prompt
        sys.stdout.write(f"\033[{self.dd_lines}A")
        sys.stdout.write(f"\r\033[K{self.prompt}{self.buffer}")
        sys.stdout.flush()
        
        self.dd_lines = 0
        self.showing_dd = False
    
    def read(self):
        """Read a line with autocomplete. Returns the input string."""
        self.buffer = ""
        self.dropdown = []
        self.selected = 0
        self.showing_dd = False
        self.dd_lines = 0
        
        # Show initial prompt
        sys.stdout.write(self.prompt)
        sys.stdout.flush()
        
        with RawTerminal() as term:
            while True:
                ktype, kval = term.read_key()
                
                # ENTER — accept input
                if ktype == "enter":
                    self._clear_dropdown()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    return self.buffer
                
                # CTRL+C — raise interrupt
                if ktype == "ctrl-c":
                    self._clear_dropdown()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                
                # CTRL+D — raise EOF
                if ktype == "ctrl-d":
                    self._clear_dropdown()
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    raise EOFError
                
                # ESC — dismiss dropdown
                if ktype == "esc":
                    if self.showing_dd:
                        self._clear_dropdown()
                    continue
                
                # ARROW UP — navigate dropdown up
                if ktype == "arrow" and kval == "up" and self.showing_dd:
                    self.selected = max(0, self.selected - 1)
                    self._draw_dropdown()
                    continue
                
                # ARROW DOWN — navigate dropdown down
                if ktype == "arrow" and kval == "down" and self.showing_dd:
                    self.selected = min(len(self.dropdown[:8]) - 1, self.selected + 1)
                    self._draw_dropdown()
                    continue
                
                # TAB — select current dropdown item
                if ktype == "tab" and self.showing_dd and self.dropdown:
                    selected = self.dropdown[self.selected]
                    self.buffer = "/" + selected[0]
                    self._clear_dropdown()
                    self._draw_prompt()
                    # Don't return yet — let user finish typing
                    continue
                
                # BACKSPACE
                if ktype == "backspace":
                    if self.buffer:
                        self.buffer = self.buffer[:-1]
                        
                        if self.buffer.startswith('/') and len(self.buffer) > 0:
                            self.dropdown = self._filter(self.buffer)
                            self.selected = 0
                            if self.dropdown:
                                self._draw_dropdown()
                            else:
                                self._clear_dropdown()
                        else:
                            self._clear_dropdown()
                        
                        self._draw_prompt()
                    continue
                
                # REGULAR CHARACTER
                if ktype == "char":
                    self.buffer += kval
                    sys.stdout.write(kval)
                    sys.stdout.flush()
                    
                    # Check for slash command trigger
                    if self.buffer == '/':
                        self.dropdown = CMDS
                        self.selected = 0
                        self._draw_dropdown()
                    elif self.buffer.startswith('/') and len(self.buffer) > 1:
                        self.dropdown = self._filter(self.buffer)
                        self.selected = 0
                        if self.dropdown:
                            self._draw_dropdown()
                        else:
                            self._clear_dropdown()
                    elif self.showing_dd:
                        # Typed something that's not a slash command
                        self._clear_dropdown()


# ═══════════════════════════════════════
# FILE READER
# ═══════════════════════════════════════

def read_file(path):
    try:
        p = Path(path)
        if not p.exists(): return f"Not found: {path}"
        if p.is_dir():
            items = [f"  {'📁' if x.is_dir() else '📄'} {x.name}" for x in sorted(p.iterdir()) if not x.name.startswith('.')][:30]
            return f"{path}:\n" + '\n'.join(items)
        content = p.read_text(errors='replace')
        lines = content.split('\n')
        if len(lines) > 100: return '\n'.join(lines[:100]) + f"\n\n... ({len(lines)-100} more lines)"
        return content
    except Exception as e: return f"Error: {e}"

def find_files(pattern, dir="."):
    try:
        matches = list(Path(dir).rglob(pattern))
        if not matches: return f"No matches: {pattern}"
        return '\n'.join(f"  {m.relative_to(dir)}" for m in matches[:20])
    except: return "Error"

def search_text(query, dir="."):
    results = []
    for ext in ['.py','.js','.ts','.tsx','.md','.json','.html','.css']:
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


# ═══════════════════════════════════════
# PERMISSION
# ═══════════════════════════════════════

class Permissions:
    def __init__(self):
        self.file = Path(CWD) / ".swarm-permissions.json"
        self.always = set()
        if self.file.exists():
            try: self.always = set(json.loads(self.file.read_text()).get("always",[]))
            except: pass
    
    def save(self):
        self.file.write_text(json.dumps({"always":list(self.always)}))
    
    def ask(self, action, desc):
        if action in self.always: return True
        print(f"\n  {C.t(C.YLW, '⚠')} {desc}")
        print(f"  {C.t(C.CYN, '[y]')} Yes  {C.t(C.CYN, '[a]')} Always  {C.t(C.CYN, '[n]')} No\n")
        with RawTerminal() as t:
            sys.stdout.write(f"  ? ")
            sys.stdout.flush()
            _, ch = t.read_key()
            print(ch)
        if ch == 'a': self.always.add(action); self.save()
        return ch in ('y','a')


# ═══════════════════════════════════════
# ACTION DETECTOR
# ═══════════════════════════════════════

GREETINGS = {"hi","hello","hey","yo","sup","wassup","haffa","how far","good morning","good afternoon","good evening"}
BUILD_KW = ["build a","create a","make a","develop a","landing page","website","web app","api","dashboard","todo app","todo list"]
FILE_KW = ["read ","open ","show me ","cat ","view ","look at "]
CMD_KW = ["run ","execute ","install ","npm ","pip ","docker ","git ","yarn "]

def detect(text):
    t = text.lower().strip()
    w = t.split()
    if len(w) <= 2:
        for g in GREETINGS:
            if g in t: return "chat"
    for kw in FILE_KW:
        if kw in t: return "file"
    for kw in CMD_KW:
        if t.startswith(kw): return "cmd"
    if t in ['ls','dir','pwd']: return "cmd"
    if len(w) >= 3:
        for kw in BUILD_KW:
            if kw in t: return "build"
    return "question"


# ═══════════════════════════════════════
# SWARM RUNNER
# ═══════════════════════════════════════

def run_swarm(goal, engine):
    cmd = [sys.executable, str(SWARM_ROOT / "orchestrator.py")]
    if engine != "auto": cmd.extend(["--engine", engine])
    cmd.append(goal)
    try:
        proc = subprocess.Popen(cmd, cwd=CWD)
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


def run_cmd(command, perms):
    dangerous = any(command.lower().startswith(d) for d in ["rm ","rm -","git push","npm install","pip install","chmod","sudo"])
    if dangerous and not perms.ask("cmd:" + command.split()[0], f"Run: {command}"):
        print(f"  {C.t(C.RED, 'Denied')}\n")
        return
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120, cwd=CWD)
        print()
        if r.stdout:
            for line in r.stdout.split('\n')[:25]: print(f"  {line}")
        if r.stderr: print(f"  {C.t(C.RED, r.stderr[:200])}")
        print()
    except Exception as e:
        print(f"  {C.t(C.RED, str(e))}\n")


def check_update():
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://raw.githubusercontent.com/Anasabubakar/agent-swarm/main/package.json',
            headers={'User-Agent':'swarm'}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            v = json.loads(r.read()).get("version","0.0.0")
            return v if v != VERSION else None
    except: return None


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    # Detect engines
    engine_map = {"claude":"claude","gemini":"gemini","kilo":"kilo","codex":"codex","aider":"aider"}
    installed = [k for k,v in engine_map.items() if shutil.which(v)]
    engine = installed[0] if installed else "auto"
    
    perms = Permissions()
    memory_file = Path(CWD) / ".swarm-chat.json"
    messages = []
    if memory_file.exists():
        try: messages = json.loads(memory_file.read_text())
        except: pass
    
    # Update check
    new_ver = check_update()
    if new_ver:
        print(f"\n  {C.t(C.YLW, f'⚠ Update available: v{VERSION} → v{new_ver}  |  /update')}\n")
    
    # Banner
    print(f"""
{C.t(C.B+C.CYN, '  ╔══════════════════════════════════════╗')}
{C.t(C.B+C.CYN, '  ║  ███████╗██╗    ██╗ █████╗ ██████╗   ║')}
{C.t(C.B+C.CYN, '  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗  ║')}
{C.t(C.B+C.CYN, '  ║  ███████╗██║ █╗ ██║███████║██████╔╝  ║')}
{C.t(C.B+C.CYN, '  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗  ║')}
{C.t(C.B+C.CYN, '  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║  ║')}
{C.t(C.B+C.CYN, '  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ║')}
{C.t(C.B+C.CYN, f'  ║  {C.t(C.WHT,f"v{VERSION} by Anas Abubakar")}{C.t(C.B+C.CYN,"       ║")}')}
{C.t(C.B+C.CYN, '  ╚══════════════════════════════════════╝')}
""")
    
    print(f"  {C.t(C.GRN,'✓')} Engine: {C.t(C.B,engine)}")
    if installed:
        eng_list = ", ".join(installed)
        print(f"  {C.t(C.D,f'Available: {eng_list}')}")
    print(f"  {C.t(C.D,'Type / for commands • ESC to cancel • /quit to exit')}\n")
    
    inp = Input(f"  {C.t(C.GRN,'▸')} ")
    
    while True:
        try:
            text = inp.read().strip()
            if not text: continue
            
            # SLASH COMMANDS
            if text.startswith("/"):
                cmd = text[1:].strip()
                
                if cmd in ("quit","exit"):
                    print(f"\n  {C.t(C.CYN,'Goodbye! 🛡️')}\n")
                    break
                
                if cmd == "help":
                    print(f"\n  {C.t(C.B+C.CYN,'Commands')}")
                    print(f"  {C.t(C.D,'─'*35)}")
                    for c,d in CMDS:
                        print(f"  {C.t(C.CYN,'/'+c):<22} {C.t(C.D,d)}")
                    print()
                    continue
                
                if cmd.startswith("read "):
                    path = cmd[5:].strip()
                    print(f"\n  {C.t(C.BLU,'📄 '+path)}")
                    print(f"  {C.t(C.D,'─'*35)}")
                    for line in read_file(path).split('\n')[:30]:
                        print(f"  {C.t(C.D,'│')} {line}")
                    print()
                    continue
                
                if cmd == "ls" or cmd.startswith("ls "):
                    d = cmd[3:].strip() or "."
                    print(f"\n{read_file(d)}\n")
                    continue
                
                if cmd.startswith("find "):
                    print(f"\n{find_files(cmd[5:].strip())}\n")
                    continue
                
                if cmd.startswith("grep "):
                    print(f"\n{search_text(cmd[5:].strip())}\n")
                    continue
                
                if cmd.startswith("run "):
                    run_cmd(cmd[4:].strip(), perms)
                    continue
                
                if cmd == "update":
                    new = check_update()
                    if new:
                        print(f"\n  {C.t(C.YLW,f'Update: v{VERSION} → v{new}')}")
                        print(f"  {C.t(C.CYN,'[a]')} Auto-update  {C.t(C.CYN,'[m]')} Manual  {C.t(C.CYN,'[s]')} Skip\n")
                    else:
                        print(f"  {C.t(C.GRN,'✓')} Latest version\n")
                    continue
                
                if cmd == "credits":
                    print(f"\n  {C.t(C.B+C.CYN,'═'*30)}")
                    print(f"  {C.t(C.B,'🛡️  Agent Swarm')}")
                    print(f"  {C.t(C.D,'By:')} Anas Abubakar")
                    print(f"  {C.t(C.D,'MIT License • v'+VERSION)}")
                    print(f"  {C.t(C.B+C.CYN,'═'*30)}\n")
                    continue
                
                if cmd == "memory":
                    if not messages:
                        print(f"  {C.t(C.D,'No history')}\n")
                    else:
                        print(f"\n  {C.t(C.B,f'History ({len(messages)})')}")
                        for m in messages[-8:]:
                            c = C.WHT if m['role']=='user' else C.CYN
                            print(f"  {C.t(c,'▸' if m['role']=='user' else '◂')} {m['content'][:60]}")
                        print()
                    continue
                
                if cmd == "memory clear":
                    messages = []
                    memory_file.write_text("[]")
                    print(f"  {C.t(C.GRN,'✓')} Cleared\n")
                    continue
                
                if cmd.startswith("model"):
                    print(f"\n  {C.t(C.B,'Engines:')} {', '.join(installed) if installed else 'none'}")
                    print(f"  {C.t(C.D,'Current: '+engine)}")
                    print(f"  {C.t(C.D,'Type /model <name> to switch')}\n")
                    continue
                
                if cmd.startswith("employee"):
                    print(f"  {C.t(C.D,'245 agents available. /employee list to browse.')}\n")
                    continue
                
                print(f"  {C.t(C.RED,'Unknown: /'+cmd)}  /help\n")
                continue
            
            # NORMAL INPUT
            action = detect(text)
            messages.append({"role":"user","content":text,"time":datetime.now().isoformat()})
            
            if action == "chat":
                replies = {
                    "yo":"Yo! What's good? 👋","hi":"Hey! Ready to work. 🛡️",
                    "hello":"Hello! What do you need?","hey":"Hey hey!",
                    "sup":"Not much, waiting on you 😄","haffa":"Haffa! Wetin dey?",
                    "how far":"I dey! What you need?",
                }
                reply = replies.get(text.lower().strip(), "Hey! What do you need?")
                print(f"\n  {reply}\n")
                messages.append({"role":"assistant","content":reply})
            
            elif action == "question":
                print(f"\n  {C.t(C.BLU,'💡')} Connect an AI engine to answer questions.")
                print(f"  {C.t(C.D,'Or give me a build task to use the swarm.')}\n")
            
            elif action == "file":
                words = text.split()
                fn = None
                for i,w in enumerate(words):
                    if w in ['read','open','show','cat','view','look'] and i+1<len(words):
                        fn = words[i+1]; break
                    if '.' in w and len(w)>2: fn = w; break
                if fn:
                    print(f"\n  {C.t(C.BLU,'📄 '+fn)}")
                    print(f"  {C.t(C.D,'─'*35)}")
                    for line in read_file(fn).split('\n')[:30]:
                        print(f"  {C.t(C.D,'│')} {line}")
                    print()
                else:
                    print(f"  {C.t(C.YLW,'Which file?')} /read <filename>\n")
            
            elif action == "cmd":
                cmd = text
                if cmd.lower().startswith("run "): cmd = cmd[4:].strip()
                elif cmd.lower() in ['ls','dir']: cmd = "ls -la"
                run_cmd(cmd, perms)
            
            elif action == "build":
                print()
                run_swarm(text, engine)
                print()
            
            messages.append({"role":"assistant","content":f"Handled: {text}","time":datetime.now().isoformat()})
            memory_file.write_text(json.dumps(messages[-100:], indent=2))
        
        except KeyboardInterrupt:
            print(f"\n")
            continue
        except EOFError:
            print()
            break

if __name__ == "__main__":
    main()
