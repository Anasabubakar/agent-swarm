# 🛡️ Agent Swarm

**Engine-agnostic multi-agent orchestration. 700+ resources from 5 top repos. Works with ANY CLI agent.**

One orchestrator. Hundreds of specialist AI employees. Parallel execution.

## What's Inside

| Category | Count | Sources |
|----------|-------|---------|
| 🤖 **Agents** | 252 | agency-agents, everything-claude-code, superpowers, get-shit-done |
| 🛠️ **Skills** | 239 | everything-claude-code, superpowers |
| 📋 **Commands** | 125 | everything-claude-code, get-shit-done |
| 📏 **Rules** | 77 | everything-claude-code (12+ languages) |
| 🔧 **Engines** | 11+ | Claude Code, Gemini, Codex, Cursor, Aider, Windsurf, Copilot, etc. |
| **Total** | **700+** | |

## Source Repos (Integrated)

- **[agency-agents](https://github.com/msitarzewski/agency-agents)** — 185 specialized agent definitions across engineering, product, design, testing, marketing, sales
- **[everything-claude-code](https://github.com/affaan-m/everything-claude-code)** — 147 skills, 36 agents, 68 commands, language-specific rules
- **[superpowers](https://github.com/obra/superpowers)** — 14 workflow skills (TDD, parallel dispatch, code review, debugging)
- **[get-shit-done](https://github.com/gsd-build/get-shit-done)** — 18 agents (planner, executor, debugger, verifier, UI checker)
- **[claude-mem](https://github.com/thedotmack/claude-mem)** — Persistent memory system

## Key Features

### 🎯 Engine-Agnostic
Works with ANY CLI agent that accepts a prompt:

```
Claude Code · Gemini CLI · Codex · Cursor · Aider · Windsurf · Copilot · OpenCode · Qwen · ANY custom CLI
```

### 🤖 252 Agents

**Engineering:** frontend-dev, backend-architect, mobile-builder, ai-engineer, devops, security, database-optimizer, code-reviewer, SRE, rapid-prototyper, software-architect, and 50+ more

**Design:** ui-designer, ux-architect, brand-guardian, visual-storyteller, whimsy-injector

**Product:** product-manager, sprint-prioritizer, feedback-synthesizer, trend-researcher

**Testing:** qa-tester, api-tester, accessibility-auditor, performance-benchmarker, reality-checker

**Management:** project-manager, tech-lead, studio-producer, experiment-tracker

**And more:** marketing, sales, support, strategy, academic, specialized

### 🛠️ 239 Skills
TDD, parallel agent dispatch, code review, debugging, git workflow, security scanning, database migrations, API design, deployment patterns, and 200+ more

### 📏 77 Language Rules
TypeScript, Python, Go, Rust, Java, Kotlin, Swift, C++, PHP, Perl, C#, and more

## Quick Start

```bash
# Clone
git clone https://github.com/Anasabubakar/agent-swarm.git
cd agent-swarm

# See what's available
python orchestrator.py --list-agents
python orchestrator.py --list-engines

# Give a goal
python orchestrator.py "Build a landing page for TeenovateX Labs"

# Use specific engine
python orchestrator.py --engine gemini "Create a REST API"

# Use specific agent
python orchestrator.py --agent frontend-dev "Create a navbar component"

# Register your own engine
python orchestrator.py --register-engine myagent "my-cli" "--system-prompt"
```

## How It Works

```
1. You give a goal → "Build a landing page"
2. PM agent breaks it into tasks
3. Orchestrator dispatches to specialist agents (parallel)
4. Agents work independently, write to output/
5. Tech Lead reviews for consistency
6. Report compiled with all results
```

## Adding Your Own Agent

Just drop a `.md` file in `agents/`:

```markdown
# My Agent

## Role
You are a [specialty]. You ONLY do [thing].

## Input
[what you receive]

## Output
[what you produce]

## Constraints
- DO [things]
- DON'T [things]
```

## Adding Your Own Engine

```python
from engines.adapter import BaseEngine, register_engine

class MyEngine(BaseEngine):
    name = "myengine"
    command = "my-cli"
    system_prompt_flag = "--system"

register_engine("myengine", MyEngine)
```

Or dynamically:
```bash
python orchestrator.py --engine generic --command "my-cli" --system-flag "--role" "Do something"
```

## Architecture

```
agent-swarm/
├── orchestrator.py          ← Main orchestrator
├── swarm.config.json        ← Configuration (239 agents registered)
├── engines/adapter.py       ← Engine abstraction layer
├── agents/                  ← 252 agent definitions
│   ├── engineering/         ← Frontend, backend, devops, security, etc.
│   ├── design/              ← UI, UX, brand, visual
│   ├── product/             ← PM, sprint, feedback
│   ├── testing/             ← QA, API, accessibility, performance
│   ├── project-management/  ← Project shepherd, experiment tracker
│   ├── ecc/                 ← everything-claude-code agents
│   ├── gsd/                 ← get-shit-done agents
│   └── ...                  ← More categories
├── skills/                  ← 239 workflow skills
│   ├── superpowers/         ← TDD, parallel dispatch, code review
│   └── ...                  ← 147 ECC skills
├── commands/                ← 125 slash commands
├── rules/                   ← 77 language-specific rules
├── memory-system/           ← claude-mem integration
├── memory/                  ← Agent shared state
└── output/                  ← Agent work output
```

## License

MIT — All source repos included under their original licenses.
