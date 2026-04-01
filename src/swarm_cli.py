#!/usr/bin/env python3
"""
  ╔══════════════════════════════════════╗
  ║  ███████╗██╗    ██╗ █████╗ ██████╗   ║
  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗  ║
  ║  ███████╗██║ █╗ ██║███████║██████╔╝  ║
  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗  ║
  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║  ║
  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ║
  ║  AI Assistant + Agent Swarm          ║
  ║  by Anas Abubakar • v1.0.5           ║
  ╚══════════════════════════════════════╝
"""

import sys, os, json, subprocess, shutil
from pathlib import Path
from datetime import datetime

SWARM_ROOT = Path(os.environ.get("SWARM_ROOT", Path(__file__).parent.parent))
VERSION = "1.0.5"
CWD = os.getcwd()

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
        print(f"\n  {C.t(C.CYN,'Goodbye! 🛡️')}\n")
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
    
    if cmd.startswith("employee"):
        print(f"  {C.t(C.D,'245 agents available. Build a goal and they auto-activate.')}\n")
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
    
    # Update check
    new_ver = check_update()
    if new_ver:
        print(f"\n  {C.t(C.YLW,f'⚠ Update available: v{VERSION} → v{new_ver}')}")
        print(f"  {C.t(C.D,'Run: cd ~/.swarm && git pull')}\n")
    
    # Banner
    print(f"""
{C.t(C.B+C.CYN,'  ╔══════════════════════════════════════╗')}
{C.t(C.B+C.CYN,'  ║  ███████╗██╗    ██╗ █████╗ ██████╗   ║')}
{C.t(C.B+C.CYN,'  ║  ██╔════╝██║    ██║██╔══██╗██╔══██╗  ║')}
{C.t(C.B+C.CYN,'  ║  ███████╗██║ █╗ ██║███████║██████╔╝  ║')}
{C.t(C.B+C.CYN,'  ║  ╚════██║██║███╗██║██╔══██║██╔══██╗  ║')}
{C.t(C.B+C.CYN,'  ║  ███████║╚███╔███╔╝██║  ██║██║  ██║  ║')}
{C.t(C.B+C.CYN,'  ║  ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ║')}
{C.t(C.B+C.CYN,f'  ║  {C.t(C.WHT,f"v{VERSION} by Anas Abubakar")}{C.t(C.B+C.CYN,"       ║")}')}
{C.t(C.B+C.CYN,'  ╚══════════════════════════════════════╝')}
""")
    
    eng_list = ', '.join(installed)
    print(f"  {C.t(C.GRN,'✓')} Engine: {C.t(C.B,engine)}  ({eng_list})")
    print(f"  {C.t(C.D,'Type / for commands • /quit to exit')}\n")
    
    # Main loop — just use regular input()
    while True:
        try:
            text = input(f"  {C.t(C.GRN,'▸')} ").strip()
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
                print(f"\n  {C.t(C.CYN,'Goodbye! 🛡️')}\n")
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
            print(f"\n  {C.t(C.CYN,'Goodbye! 🛡️')}\n")
            break
        except EOFError:
            print()
            break

if __name__ == "__main__":
    main()
