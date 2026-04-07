# 🛡️ Swarm

**Engine-agnostic multi-agent orchestration. 245 agents. One command. v3.0.5**

Claude Code features fully implemented:

- **CLI Commands**: `/help`, `/clear`, `/status`, `/resume`, `/sessions`, `/model`, `/compact`, `/save`, `/memory`, `/mcp`, `/git`, `/config`, `/cost`, `/undo`, `/review`, `/btw`
- **Session Management**: Auto-save sessions, history, resume, compact
- **Paste Handling**: Reference expansion `[Pasted #1]` - no auto-submit
- **Windows/Linux/Mac**: Full cross-platform support
- **Multiple Models**: Claude Sonnet, Opus, Gemini, GPT-4

```bash
npm install -g @anas.abubakar/swarm
```

Then in any project folder:
```bash
swarm "Build a landing page"
```

**Commands:**
- `/help` - List all commands
- `/sessions` - List saved sessions  
- `/resume [id]` - Resume a session
- `/compact` - Compact conversation history
- `/status` - Show session status
- `/model [name]` - Switch model
- `/memory list|add [text]` - Manage memory

That's it. Let's go.

## What Happens

```
swarm "Build a todo app with React"
  ↓
📁 Creates isolated workspace: projects/build-a-todo-app-with-react-20260401/
❓ Questionnaire asks clarifying questions
📐 Planner designs the implementation
🚀 Frontend + Backend + QA agents build in parallel
🐛 Debugger fixes any failures
🔍 Tech Lead reviews everything
  ↓
✅ Done. Check your workspace.
```

## Install

### Option 1: Curl (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/Anasabubakar/agent-swarm/main/install.sh | bash
```

### Option 2: NPM
```bash
npm install -g @anasabubakar/swarm
```

### Option 3: Manual
```bash
git clone https://github.com/Anasabubakar/agent-swarm.git ~/.swarm
ln -sf ~/.swarm/bin/swarm /usr/local/bin/swarm
```

### Prerequisites
- Python 3.8+
- Git
- At least one AI engine: `kilo`, `claude`, `gemini`, `codex`, `aider`, or `cursor-agent`

## Usage

```bash
# Interactive — just shows help
swarm

# Give a goal — orchestrator handles everything
swarm "Build a landing page for TeenovateX Labs"

# Use a specific engine
swarm -e gemini "Create a REST API"

# Run a single agent
swarm -a frontend-dev "Create a responsive navbar"

# List what's available
swarm --list-engines
swarm --list-agents
```

## What's Inside

| Category | Count | What |
|---|---|---|
| 🤖 Agents | 245 | Frontend, backend, devops, security, design, QA, PM, and 200+ more |
| 🛠️ Skills | 239 | TDD, code review, debugging, deployment, security scanning |
| 📋 Commands | 125 | Slash commands for common workflows |
| 📏 Rules | 77 | Language-specific coding standards (TS, Python, Go, Rust, etc.) |
| 🔧 Engines | 11+ | Claude, Gemini, Kilo, Codex, Cursor, Aider, Windsurf, Copilot, etc. |

## How It Works

### 5-Phase Workflow
1. **Questionnaire** — Asks clarifying questions before building
2. **Planner** — Designs architecture and task dependencies
3. **Execute** — Dispatches specialist agents in parallel
4. **Debug** — Automatically fixes failures
5. **Ship** — Tech Lead final review

### Workspace Isolation
Each goal creates its own project folder. The swarm folder stays untouched.
```
projects/
└── your-goal-timestamp/
    ├── src/                    ← agents build here
    ├── tests/
    ├── .swarm-meta.json        ← tracking metadata
    └── .swarm-report.json      ← final report
```

### Safety
Commands are classified:
- ✅ **Safe** — Auto-approve (ls, cat, git status)
- 🟡 **Moderate** — Auto-approve, logged (npm install, git commit)
- 🔴 **Dangerous** — Needs approval (rm, deploy, git push --force)
- 🚫 **Blocked** — Never allowed (rm -rf /, shutdown)

### Self-Healing
If an agent fails:
1. **Retry** — Same agent, exponential backoff
2. **Reassign** — Swap to backup agent
3. **Simplify** — Break task into smaller pieces
4. **Fallback** — Switch to different engine
5. **Escalate** — Flag for human review

## Engine Support

Works with ANY CLI agent that accepts a prompt:

| Engine | Status |
|---|---|
| Claude Code | ✅ |
| Gemini CLI | ✅ |
| Kilo Code | ✅ |
| Codex | ✅ |
| Cursor Agent | ✅ |
| Aider | ✅ |
| Windsurf | ✅ |
| GitHub Copilot | ✅ |
| OpenCode | ✅ |
| Qwen Code | ✅ |
| Any custom CLI | ✅ (via `--engine generic`) |

## Adding Your Own Agent

Drop a `.md` file in `agents/`:

```markdown
# My Agent

## Role
You are a [specialty]. You ONLY do [thing].

## Constraints
- DO [things]
- DON'T [things]
```

## Source Repos (Integrated)

- [agency-agents](https://github.com/msitarzewski/agency-agents) — 185 specialist agents
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — 147 skills, 36 agents, 68 commands
- [superpowers](https://github.com/obra/superpowers) — TDD, parallel dispatch, code review
- [get-shit-done](https://github.com/gsd-build/get-shit-done) — 18 agents, meta-prompting
- [claude-mem](https://github.com/thedotmack/claude-mem) — Persistent memory system

## License

MIT — Copyright (c) 2026 Anas Abubakar
