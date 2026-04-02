#!/usr/bin/env python3
"""
  ╔════════════════════════════════════════╗
  ║  ███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗║
  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║║
  ║  ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║║
  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║║
  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║║
  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝║
  ║  AI Assistant + Agent Swarm                      ║
  ║  by Anas Abubakar • v1.0.14                      ║
  ╚════════════════════════════════════════╝
"""

import sys, os, json, subprocess, shutil, random
import tty, termios
from pathlib import Path
from datetime import datetime

SWARM_ROOT = Path(os.environ.get("SWARM_ROOT", Path(__file__).parent.parent))

# Auto-sync version from package.json
def _get_version():
    try:
        pkg = json.loads((SWARM_ROOT / "package.json").read_text())
        return pkg.get("version", "1.0.0")
    except:
        return "1.0.0"

VERSION = _get_version()
CWD = os.getcwd()

# Reset terminal state on startup (clean up any escape codes from previous sessions)
sys.stdout.write('\033[0m\033[?25h')  # Reset colors, show cursor
sys.stdout.flush()

WELCOME = [
    "Right then. Let's get to work.",
    "Another day, another codebase to save.",
    "Swarm is online. Try not to break anything.",
    "245 agents. Zero patience for bad code.",
    "I woke up and chose productivity. Barely.",
    "Fresh session. Clean slate. Let's see how long that lasts.",
    "Loaded and ready. Unlike my motivation on Mondays.",
    "Your personal army of AI agents is assembled.",
    "Good to see you again. Or for the first time.",
    "Let me guess — you have a quick project for me.",
    "Ready to turn your caffeine into code.",
    "The swarm is awake. Pray for your codebase.",
]

GOODBYE = [
    "Goodbye. Your code is probably fine. Probably.",
    "Logging off before I break something.",
    "The swarm is going to sleep.",
    "Remember: git commit often. Unlike Anas.",
    "Session over. Go touch grass.",
    "Goodbye. May your tests pass on the first try.",
    "The agents are clocking out. Union rules.",
    "Leaving before the bugs find us.",
    "Peace out. Don't forget to push your code.",
    "If your code breaks after I leave, that is a you problem.",
]

# ═══════════════════════════════════════
# CLEAN INPUT WITH PROPER KEY HANDLING
# ═══════════════════════════════════════

def clean_input(prompt=""):
    """
    Proper text input with backspace, delete, and arrow keys.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    
    buf = []    # Characters before cursor
    after = []  # Characters after cursor (for right-arrow)
    
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    def redraw():
        """Redraw the entire line from cursor position"""
        # Move to start of input
        if buf:
            sys.stdout.write(f'\x1b[{len(buf)}D')
        # Clear everything after prompt
        total = len(buf) + len(after)
        sys.stdout.write(' ' * total)
        # Move back to start
        sys.stdout.write(f'\x1b[{total}D')
        # Write all characters
        sys.stdout.write(''.join(buf))
        if after:
            sys.stdout.write(''.join(reversed(after)))
            # Move cursor back to correct position
            sys.stdout.write(f'\x1b[{len(after)}D')
        sys.stdout.flush()
    
    try:
        tty.setraw(fd)
        
        while True:
            ch = sys.stdin.read(1)
            
            # Enter
            if ch in ('\r', '\n'):
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                return ''.join(buf + list(reversed(after)))
            
            # CTRL+C
            if ch == '\x03':
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise KeyboardInterrupt
            
            # CTRL+D
            if ch == '\x04':
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise EOFError
            
            # Escape sequence
            if ch == '\x1b':
                seq = sys.stdin.read(2)
                if seq == '[D':  # Left arrow
                    if buf:
                        after.append(buf.pop())
                        sys.stdout.write('\x1b[D')
                        sys.stdout.flush()
                elif seq == '[C':  # Right arrow
                    if after:
                        buf.append(after.pop())
                        sys.stdout.write('\x1b[C')
                        sys.stdout.flush()
                elif seq == '[3':  # Possible delete key
                    tilde = sys.stdin.read(1)  # Should be '~'
                    if tilde == '~' and after:  # Delete key
                        after.pop()
                        # Redraw from current position
                        if after:
                            sys.stdout.write(''.join(reversed(after)))
                            sys.stdout.write(' ')
                            sys.stdout.write(f'\x1b[{len(after) + 1}D')
                        else:
                            sys.stdout.write(' \x1b[D')
                        sys.stdout.flush()
                elif seq == '[H':  # Home
                    if buf:
                        sys.stdout.write(f'\x1b[{len(buf)}D')
                        after = list(reversed(buf)) + after
                        buf = []
                        sys.stdout.flush()
                elif seq == '[F':  # End
                    if after:
                        sys.stdout.write(f'\x1b[{len(after)}C')
                        buf = buf + list(reversed(after))
                        after = []
                        sys.stdout.flush()
                # Ignore other escape sequences
                continue
            
            # Backspace
            if ch in ('\x7f', '\b'):
                if buf:
                    buf.pop()
                    sys.stdout.write('\b \b')  # Move back, clear, move back
                    if after:
                        # Redraw characters after cursor
                        sys.stdout.write(''.join(reversed(after)))
                        sys.stdout.write(' ')
                        sys.stdout.write(f'\x1b[{len(after) + 1}D')
                    sys.stdout.flush()
                continue
            
            # CTRL+U - clear line
            if ch == '\x15':
                total = len(buf) + len(after)
                if total > 0:
                    sys.stdout.write(f'\x1b[{total}D')
                    sys.stdout.write(' ' * total)
                    sys.stdout.write(f'\x1b[{total}D')
                    buf = []
                    after = []
                    sys.stdout.flush()
                continue
            
            # CTRL+A - beginning
            if ch == '\x01':
                if buf:
                    sys.stdout.write(f'\x1b[{len(buf)}D')
                    after = list(reversed(buf)) + after
                    buf = []
                    sys.stdout.flush()
                continue
            
            # CTRL+E - end
            if ch == '\x05':
                if after:
                    sys.stdout.write(f'\x1b[{len(after)}C')
                    buf = buf + list(reversed(after))
                    after = []
                    sys.stdout.flush()
                continue
            
            # Regular printable character
            if ord(ch) >= 32:
                buf.append(ch)
                if after:
                    # Insert in middle
                    sys.stdout.write(ch)
                    sys.stdout.write(''.join(reversed(after)))
                    sys.stdout.write(f'\x1b[{len(after)}D')
                else:
                    sys.stdout.write(ch)
                sys.stdout.flush()
    
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
# Colors
class C:
    R="\033[0m"; B="\033[1m"; D="\033[2m"
    RED="\033[91m"; GRN="\033[92m"; YLW="\033[93m"
    BLU="\033[94m"; MAG="\033[95m"; CYN="\033[96m"; WHT="\033[97m"
    @staticmethod
    def t(c,t): return f"{c}{t}{C.R}"

# Commands
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
    ("credits",       "Show credits"),
    ("quit",          "Exit swarm"),
]

# File reader
def read_file(path):
    try:
        p = Path(path)
        if not p.exists(): return f"Not found: {path}"
        if p.is_dir():
            items = [f"  {'📁' if x.is_dir() else '📄'} {x.name}" for x in sorted(p.iterdir()) if not x.name.startswith('.')][:30]
            return f"{path}:\n" + '\n'.join(items)
        content = p.read_text(errors='replace')
        lines = content.split('\n')
        if len(lines) > 100: return '\n'.join(lines[:100]) + f"\n\n... ({len(lines)-100} more)"
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

# Action detection
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

# Swarm runner
def run_swarm(goal, engine):
    cmd = [sys.executable, str(SWARM_ROOT / "orchestrator.py")]
    if engine != "auto": cmd.extend(["--engine", engine])
    cmd.append(goal)
    try:
        proc = subprocess.Popen(cmd, cwd=CWD)
        proc.wait(timeout=1800)  # 30 minutes for complex tasks
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"  {C.t(C.RED, '✗ Timeout')}")
        return False
    except KeyboardInterrupt:
        proc.kill()
        print(f"\n  {C.t(C.YLW, '⏸ Cancelled')}")
        return False

def run_cmd(command):
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

def handle_slash(text):
    """Handle slash commands. Returns True if handled."""
    cmd = text[1:].strip()
    
    if cmd in ("quit","exit"):
        print(f"\n  {C.t(C.D, random.choice(GOODBYE))}\n")
        sys.exit(0)
    
    if cmd == "help":
        print(f"\n  {C.t(C.B+C.CYN,'Commands')}")
        print(f"  {C.t(C.D,'─'*30)}")
        for c,d in CMDS:
            print(f"  {C.t(C.CYN,'/'+c):<20} {C.t(C.D,d)}")
        print()
        return True
    
    if cmd.startswith("read "):
        path = cmd[5:].strip()
        print(f"\n  {C.t(C.BLU,'📄 '+path)}")
        print(f"  {C.t(C.D,'─'*30)}")
        for line in read_file(path).split('\n')[:30]:
            print(f"  {C.t(C.D,'│')} {line}")
        print()
        return True
    
    if cmd == "ls" or cmd.startswith("ls "):
        d = cmd[3:].strip() or "."
        print(f"\n{read_file(d)}\n")
        return True
    
    if cmd.startswith("find "):
        print(f"\n{find_files(cmd[5:].strip())}\n")
        return True
    
    if cmd.startswith("grep "):
        print(f"\n{search_text(cmd[5:].strip())}\n")
        return True
    
    if cmd.startswith("run "):
        run_cmd(cmd[4:].strip())
        return True
    
    if cmd == "update":
        new = check_update()
        if new:
            print(f"\n  {C.t(C.YLW,f'Update available: v{VERSION} → v{new}')}")
            print(f"  Run: {C.t(C.CYN,'cd ~/.swarm && git pull')}\n")
        else:
            print(f"  {C.t(C.GRN,'✓')} Latest version\n")
        return True
    
    if cmd == "credits":
        print(f"""
  {C.t(C.B+C.CYN,'═'*28)}
  {C.t(C.B,'🛡️  Agent Swarm')}
  {C.t(C.D,'By:')} Anas Abubakar
  {C.t(C.D,'MIT License • v'+VERSION)}
  {C.t(C.B+C.CYN,'═'*28)}
""")
        return True
    
    if cmd == "memory":
        print(f"  {C.t(C.D,'Chat history saved in .swarm-chat.json')}\n")
        return True
    
    if cmd == "memory clear":
        mf = Path(CWD) / ".swarm-chat.json"
        mf.write_text("[]")
        print(f"  {C.t(C.GRN,'✓')} Cleared\n")
        return True
    
    if cmd.startswith("model"):
        engine_map = {"claude":"claude","gemini":"gemini","kilo":"kilo","codex":"codex","aider":"aider"}
        installed = [k for k,v in engine_map.items() if shutil.which(v)]
        print(f"\n  {C.t(C.B,'Installed:')} {', '.join(installed) if installed else 'none'}")
        print(f"  {C.t(C.D,'Use --engine <name> when running goals')}\n")
        return True
    
    if cmd.startswith("employee list"):
        # Actually list the agents
        agents_dir = SWARM_ROOT / "agents"
        if not agents_dir.exists():
            print(f"  {C.t(C.RED,'Agents directory not found')}\n")
            return True
        
        all_agents = []
        for root, dirs, files in os.walk(agents_dir):
            for f in files:
                if f.endswith('.md'):
                    rel = os.path.relpath(os.path.join(root, f), agents_dir)
                    category = rel.split('/')[0] if '/' in rel else 'custom'
                    name = f.replace('.md','')
                    all_agents.append((name, category))
        
        # Group by category
        categories = {}
        for name, cat in all_agents:
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)
        
        print(f"\n  {C.t(C.B, f'Agents ({len(all_agents)} total)')}")
        print(f"  {C.t(C.D, '─'*40)}")
        for cat in sorted(categories.keys()):
            names = sorted(categories[cat])
            print(f"\n  {C.t(C.CYN, cat.upper())} ({len(names)})")
            for name in names[:15]:
                print(f"    {C.t(C.D, '.')} {name}")
            if len(names) > 15:
                print(f"    {C.t(C.D, f'... and {len(names)-15} more')}")
        print()
        return True
    
    if cmd.startswith("employee"):
        print(f"  {C.t(C.D, 'Commands:')} /employee list {C.t(C.D, '(browse all agents)')}\n")
        return True
    
    print(f"  {C.t(C.RED,'Unknown: /'+cmd)}  /help\n")
    return True


def main():
    # Detect engines
    engine_map = {"claude":"claude","gemini":"gemini","kilo":"kilo","codex":"codex","aider":"aider"}
    installed = [k for k,v in engine_map.items() if shutil.which(v)]
    engine = installed[0] if installed else "auto"
    
    # Memory
    memory_file = Path(CWD) / ".swarm-chat.json"
    messages = []
    if memory_file.exists():
        try: messages = json.loads(memory_file.read_text())
        except: pass
    
    # Banner
    print(f"""
{C.t(C.B+C.CYN,'  ╔════════════════════════════════════════╗')}
{C.t(C.B+C.CYN,'  ║  ███████╗██╗    ██╗ █████╗ ██████╗ ███╗   ███╗║')}
{C.t(C.B+C.CYN,'  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗████╗ ████║║')}
{C.t(C.B+C.CYN,'  ║  ███████╗██║ █╗ ██║███████║██████╔╝██╔████╔██║║')}
{C.t(C.B+C.CYN,'  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗██║╚██╔╝██║║')}
{C.t(C.B+C.CYN,'  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║██║ ╚═╝ ██║║')}
{C.t(C.B+C.CYN,'  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝║')}
{C.t(C.B+C.CYN,'  ║                                              ║')}
{C.t(C.B+C.CYN,f'  ║  {C.t(C.WHT,f"v{VERSION} by Anas Abubakar")}{C.t(C.B+C.CYN,"              ║")}')}
{C.t(C.B+C.CYN,'  ╚════════════════════════════════════════╝')}
""")
    
    print(f"  {C.t(C.D, random.choice(WELCOME))}\n")
    
    eng_list = ', '.join(installed)
    print(f"  {C.t(C.GRN,'✓')} Engine: {C.t(C.B,engine)}  ({eng_list})")
    print(f"  {C.t(C.D,'Type / for commands • /quit to exit')}\n")
    
    # Main loop — just use regular input()
    while True:
        try:
            text = clean_input(f"  {C.t(C.GRN,'▸')} ").strip()
            if not text: continue
            
            # Show command list when user types just /
            if text == '/':
                print()
                for c, d in CMDS:
                    print(f"  {C.t(C.CYN,'/'+c):<20} {C.t(C.D,d)}")
                print()
                continue
            
            # Slash commands
            if text.startswith("/"):
                handle_slash(text)
                continue
            
            # Exit shortcuts
            if text.lower() in ("quit","exit","q"):
                print(f"\n  {C.t(C.D, random.choice(GOODBYE))}\n")
                break
            
            # Detect and handle
            action = detect(text)
            messages.append({"role":"user","content":text,"time":datetime.now().isoformat()})
            
            if action == "chat":
                replies = {
                    "yo":"Yo! What is good?","hi":"Hey! Ready to work. 🛡️",
                    "hello":"Hello! What do you need?","hey":"Hey hey!",
                    "sup":"Not much, waiting on you","haffa":"Haffa! Wetin dey?",
                    "how far":"I dey! What you need?",
                }
                reply = replies.get(text.lower().strip(), "Hey! What do you need?")
                print(f"\n  {reply}\n")
            
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
                    print(f"  {C.t(C.D,'─'*30)}")
                    for line in read_file(fn).split('\n')[:30]:
                        print(f"  {C.t(C.D,'│')} {line}")
                    print()
                else:
                    print(f"  {C.t(C.YLW,'Which file?')} /read <filename>\n")
            
            elif action == "cmd":
                cmd = text
                if cmd.lower().startswith("run "): cmd = cmd[4:].strip()
                elif cmd.lower() in ['ls','dir']: cmd = "ls -la"
                run_cmd(cmd)
            
            elif action == "build":
                print()
                run_swarm(text, engine)
                print()
            
            messages.append({"role":"assistant","content":f"Handled: {text}","time":datetime.now().isoformat()})
            memory_file.write_text(json.dumps(messages[-100:], indent=2))
        
        except KeyboardInterrupt:
            print(f"\n  {C.t(C.D, random.choice(GOODBYE))}\n")
            sys.stdout.write('\033[0m\033[?25h')
            sys.stdout.flush()
            break
        except EOFError:
            print()
            break
    
    # Clean terminal state on exit
    sys.stdout.write('\033[0m\033[?25h')
    sys.stdout.flush()

if __name__ == "__main__":
    main()
