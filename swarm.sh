#!/bin/bash
# Agent Swarm Quick Start
# Usage: ./swarm.sh "Build a landing page for TeenovateX"

SWARM_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🛡️ Agent Swarm Orchestrator"
echo "=========================="

if [ -z "$1" ]; then
    echo ""
    echo "Usage:"
    echo "  ./swarm.sh \"Your goal here\""
    echo "  ./swarm.sh --agent frontend-dev \"Create a navbar\""
    echo ""
    echo "Available agents:"
    echo "  🎨 frontend-dev    — React/Next.js UI specialist"
    echo "  🏗️  backend-dev     — Node.js API specialist"
    echo "  🚀 devops          — Docker/CI/CD specialist"
    echo "  🔒 security        — Security audit specialist"
    echo "  ✅ qa-tester       — Testing specialist"
    echo "  📋 project-manager — Task breakdown & coordination"
    echo "  🧠 tech-lead       — Architecture & code review"
    echo ""
    echo "Engines: claude, gemini, kilocode"
    exit 0
fi

cd "$SWARM_DIR"
python3 orchestrator.py "$@"
