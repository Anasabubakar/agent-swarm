#!/usr/bin/env python3
"""
OpenClaw Native Orchestrator
Uses OpenClaw's sessions_spawn tool directly for true parallel execution.

This version is meant to be called FROM WITHIN an OpenClaw session (e.g., by Jarvis).
It outputs the sessions_spawn calls that Jarvis should make.

Usage:
  python openclaw_native.py "Build a landing page for TeenovateX"
  
Output:
  A JSON array of sessions_spawn calls to execute in parallel.
"""

import json
import sys
from pathlib import Path

SWARM_ROOT = Path(__file__).parent.parent
AGENTS_DIR = SWARM_ROOT / "agents"


def load_agent_prompt(agent_file: str) -> str:
    """Load agent definition"""
    agent_path = AGENTS_DIR / agent_file
    if not agent_path.exists():
        return f"# Agent: {agent_file}\n\nAgent file not found."
    return agent_path.read_text()


def build_spawn_call(agent_name: str, agent_file: str, task: str, context: str = "", 
                     model: str = "auto", thinking: str = "low") -> dict:
    """Build a sessions_spawn call for an agent"""
    
    agent_prompt = load_agent_prompt(agent_file)
    
    full_task = f"""You are a specialist agent. Follow your role definition strictly.

## YOUR ROLE
{agent_prompt}

## CONTEXT
{context if context else "No additional context provided."}

## YOUR TASK
{task}

## OUTPUT INSTRUCTIONS
1. Do the work described in your task
2. Return a clear summary of what you built/decided/found
3. Stay within your role constraints — do NOT do work outside your specialty

Begin now."""

    return {
        "tool": "sessions_spawn",
        "params": {
            "task": full_task,
            "label": f"swarm-{agent_name}",
            "model": model,
            "thinking": thinking,
            "mode": "run",
            "cleanup": "delete",
            "runTimeoutSeconds": 600,
        },
        "metadata": {
            "agent": agent_name,
            "file": agent_file,
        }
    }


def generate_parallel_calls(goal: str, agents: list) -> dict:
    """
    Generate the full orchestration plan as sessions_spawn calls.
    
    Returns a structured plan that Jarvis can execute:
    1. Sequential phases (questionnaire, planner)
    2. Parallel phases (frontend, backend, devops, etc.)
    3. Sequential phases (debug, ship)
    """
    
    # Phase 1: Questionnaire (sequential - must complete first)
    questionnaire_call = build_spawn_call(
        agent_name="questionnaire",
        agent_file="core/questionnaire.md",
        task=f"Analyze this goal and produce clarifying questions:\n\n{goal}",
        context="Ask thorough questions about scope, users, data, auth, edge cases.",
    )
    
    # Phase 2: Planner (sequential - depends on questionnaire)
    planner_call = build_spawn_call(
        agent_name="planner",
        agent_file="core/planner.md",
        task=f"Design a complete implementation plan for:\n\n{goal}\n\n(Questionnaire output will be provided after Phase 1)",
        context="Design architecture, file structure, tasks with dependencies.",
    )
    
    # Phase 3: Parallel Execution
    parallel_calls = []
    for agent in agents:
        call = build_spawn_call(
            agent_name=agent["name"],
            agent_file=agent["file"],
            task=agent.get("task", f"Implement your part of: {goal}"),
            context=agent.get("context", "Plan will be provided by the Planner agent."),
        )
        parallel_calls.append(call)
    
    # Phase 4: Debugger (conditional - only if agents fail)
    debugger_call = build_spawn_call(
        agent_name="debugger",
        agent_file="core/debugger.md",
        task=f"Review all agent outputs. Debug and fix any failures for:\n\n{goal}",
        context="Find root causes, apply fixes, verify.",
    )
    
    # Phase 5: Tech Lead Review (sequential - final)
    ship_call = build_spawn_call(
        agent_name="tech-lead",
        agent_file="management/tech-lead.md",
        task=f"Final review of all agent outputs for:\n\n{goal}\n\nCheck consistency, quality, completeness.",
        context="Review all outputs, check for conflicts, validate quality.",
    )
    
    return {
        "goal": goal,
        "total_agents": 2 + len(parallel_calls) + 2,  # questionnaire + planner + parallel + debugger + tech-lead
        "phases": [
            {
                "name": "questionnaire",
                "mode": "sequential",
                "description": "Ask clarifying questions before building",
                "calls": [questionnaire_call],
            },
            {
                "name": "planner",
                "mode": "sequential", 
                "description": "Design implementation plan (depends on questionnaire)",
                "calls": [planner_call],
                "depends_on": ["questionnaire"],
            },
            {
                "name": "execute",
                "mode": "parallel",
                "description": "Dispatch specialist agents simultaneously",
                "calls": parallel_calls,
                "depends_on": ["planner"],
            },
            {
                "name": "debug",
                "mode": "sequential",
                "description": "Fix any failures from execution phase",
                "calls": [debugger_call],
                "depends_on": ["execute"],
            },
            {
                "name": "ship",
                "mode": "sequential",
                "description": "Tech Lead final review",
                "calls": [ship_call],
                "depends_on": ["debug"],
            },
        ]
    }


def auto_detect_agents(goal: str) -> list:
    """Auto-detect which agents are needed based on the goal"""
    goal_lower = goal.lower()
    agents = []
    
    if any(kw in goal_lower for kw in ["website", "web app", "landing page", "frontend", "ui", "react", "next"]):
        agents.append({
            "name": "frontend-dev",
            "file": "engineering/engineering-frontend-developer.md",
            "task": f"Build the frontend for: {goal}",
        })
    
    if any(kw in goal_lower for kw in ["api", "backend", "server", "database", "auth", "node"]):
        agents.append({
            "name": "backend-dev",
            "file": "engineering/engineering-backend-architect.md",
            "task": f"Build the backend for: {goal}",
        })
    
    if any(kw in goal_lower for kw in ["deploy", "docker", "ci/cd", "pipeline", "hosting", "vercel"]):
        agents.append({
            "name": "devops",
            "file": "engineering/engineering-devops-automator.md",
            "task": f"Set up deployment for: {goal}",
        })
    
    if any(kw in goal_lower for kw in ["design", "ui", "ux", "brand", "visual"]):
        agents.append({
            "name": "design-scout",
            "file": "creative/ui-ux-scout.md",
            "task": f"Research design inspiration for: {goal}",
        })
    
    if any(kw in goal_lower for kw in ["animation", "motion", "video", "graphic", "intro"]):
        agents.append({
            "name": "motion-graphics",
            "file": "creative/motion-graphics.md",
            "task": f"Create motion graphics for: {goal}",
        })
    
    if any(kw in goal_lower for kw in ["secure", "security", "audit", "vulnerability"]):
        agents.append({
            "name": "security",
            "file": "engineering/engineering-security-engineer.md",
            "task": f"Audit security for: {goal}",
        })
    
    # Always add QA
    agents.append({
        "name": "qa-tester",
        "file": "engineering/engineering-qa-tester.md" if (AGENTS_DIR / "engineering/engineering-qa-tester.md").exists() else "testing/testing-api-tester.md",
        "task": f"Write tests for: {goal}",
    })
    
    # Default: frontend + backend if nothing matched
    if len(agents) <= 1:  # Only QA
        agents.insert(0, {
            "name": "frontend-dev",
            "file": "engineering/engineering-frontend-developer.md",
            "task": f"Build the frontend for: {goal}",
        })
        agents.insert(1, {
            "name": "backend-dev",
            "file": "engineering/engineering-backend-architect.md",
            "task": f"Build the backend for: {goal}",
        })
    
    return agents


def main():
    if len(sys.argv) < 2:
        print("Usage: python openclaw_native.py \"Your goal here\"")
        sys.exit(1)
    
    goal = " ".join(sys.argv[1:])
    agents = auto_detect_agents(goal)
    
    plan = generate_parallel_calls(goal, agents)
    
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
