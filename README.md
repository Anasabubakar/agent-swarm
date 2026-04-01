# 🛡️ Agent Swarm

**Engine-agnostic multi-agent orchestration. Works with ANY CLI agent.**

One orchestrator. Specialist AI employees. Parallel execution.

## What Is This?

Instead of one AI doing everything, you have specialized agents working together:

```
Orchestrator (the boss)
├── 🎨 Frontend Dev    — React/Next.js UI specialist
├── 🏗️  Backend Dev     — Node.js API specialist  
├── 🚀 DevOps          — Docker/CI-CD specialist
├── 🔒 Security        — Security audit specialist
├── ✅ QA Tester       — Testing specialist
├── 📋 Project Manager — Task breakdown
└── 🧠 Tech Lead       — Architecture decisions
```

## The Key Insight

**Agents are just markdown files. Engines are just command templates.**

An agent is a `.md` file with role instructions. Any CLI that accepts a prompt can be the engine. Same agent definition, different engine — swap anytime.

## Supported Engines

| Engine | Command | Flag |
|--------|---------|------|
| Claude Code | `claude` | `--system-prompt` |
| Gemini CLI | `gemini` | `--system-prompt` |
| Kilo Code | `kilo run --auto` | inline |
| Codex | `codex` | inline |
| Cursor Agent | `cursor-agent` | `-p` |
| Aider | `aider` | `--message` |
| Windsurf | `windsurf` | `--system-prompt` |
| GitHub Copilot | `gh copilot` | suggest |
| OpenCode | `opencode` | inline |
| Qwen Code | `qwen` | `--system` |
| **Any CLI** | configure dynamically | your choice |

**Adding your own engine takes 5 lines of code.** Or use `--engine generic --command "your-cli" --system-flag "--role"`.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Anasabubakar/agent-swarm.git
cd agent-swarm

# Give a goal — orchestrator handles everything
python orchestrator.py "Build a landing page for TeenovateX Labs"

# Use a specific engine
python orchestrator.py --engine gemini "Create a REST API"

# Dispatch to a single agent
python orchestrator.py --agent frontend-dev "Create a responsive navbar"

# List available engines and agents
python orchestrator.py --list-engines
python orchestrator.py --list-agents

# Register a custom engine
python orchestrator.py --register-engine myagent "my-cli" "--system-prompt"
```

## Architecture

```
agent-swarm/
├── README.md
├── orchestrator.py          ← Main orchestrator
├── swarm.sh                 ← CLI wrapper
├── swarm.config.json        ← Configuration
├── agents/
│   ├── engineering/
│   │   ├── frontend-dev.md
│   │   ├── backend-dev.md
│   │   ├── devops.md
│   │   ├── security.md
│   │   └── qa-tester.md
│   └── management/
│       ├── project-manager.md
│       └── tech-lead.md
├── engines/
│   └── adapter.py           ← Engine abstraction layer
├── memory/                  ← Shared state between agents
├── output/                  ← Where agents write their work
└── research/                ← Reference repos
```

## How It Works

1. **You give a goal** — "Build a landing page"
2. **PM agent** breaks it into tasks
3. **Orchestrator** dispatches tasks to specialist agents (in parallel)
4. **Agents** work independently, write to `output/`
5. **Tech Lead** reviews for consistency
6. **Report** compiled with all results

## Adding Your Own Agent

Create a markdown file in `agents/`:

```markdown
# My Custom Agent

## Role
You are a [specialty]. You ONLY do [specific thing].

## Input
You receive: [what you'll get]

## Output
You return: [what you'll produce]

## Constraints
- DO [things you should do]
- DON'T [things you shouldn't do]
```

That's it. The orchestrator will find it automatically.

## Adding Your Own Engine

```python
from engines.adapter import BaseEngine, register_engine

class MyEngine(BaseEngine):
    name = "myengine"
    command = "my-cli"
    system_prompt_flag = "--system"
    auto_flag = "--auto"

register_engine("myengine", MyEngine)
```

Or just use the generic engine:
```bash
python orchestrator.py --engine generic --command "my-cli" --system-flag "--role" "Do something"
```

## Inspired By

- [agency-agents](https://github.com/msitarzewski/agency-agents) — 50+ specialized agent definitions
- [superpowers](https://github.com/obra/superpowers) — Parallel agent dispatching
- [get-shit-done](https://github.com/gsd-build/get-shit-done) — Meta-prompting and context engineering
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — Complete Claude Code setup

## License

MIT
