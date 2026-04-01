#!/usr/bin/env python3
"""
Agent Swarm Orchestrator
Engine-agnostic multi-agent task execution.

Works with ANY CLI agent that accepts a prompt.
Add your own engine with 5 lines of code.

Usage:
  python orchestrator.py "Build a landing page"
  python orchestrator.py --engine gemini "Create an API"
  python orchestrator.py --engine generic --command "my-agent" --system-flag "--role" "Do something"
  python orchestrator.py --list-engines
  python orchestrator.py --list-agents
"""

import os
import json
import sys
import argparse
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Add engines to path
sys.path.insert(0, str(Path(__file__).parent))
from engines.adapter import (
    get_engine, register_engine, list_engines, GenericEngine, BaseEngine
)

# Paths
SWARM_ROOT = Path(__file__).parent
AGENTS_DIR = SWARM_ROOT / "agents"
MEMORY_DIR = SWARM_ROOT / "memory"
OUTPUT_DIR = SWARM_ROOT / "output"
CONFIG_FILE = SWARM_ROOT / "swarm.config.json"

# Ensure directories exist
MEMORY_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    """Load swarm configuration"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {"default_engine": "claude", "agents": {}}


def dispatch_agent(
    agent_name: str,
    task: str,
    context: str = "",
    engine_name: str = None,
    config: dict = None
) -> dict:
    """Dispatch a task to a specific agent via an engine"""
    
    if config is None:
        config = load_config()
    
    # Determine which engine to use
    if engine_name is None:
        engine_name = (
            config.get("agents", {}).get(agent_name, {}).get("engine")
            or config.get("default_engine", "claude")
        )
    
    engine = get_engine(engine_name)
    if engine is None:
        return {
            "agent": agent_name,
            "status": "ERROR",
            "error": f"Unknown engine: {engine_name}. Use --list-engines to see available engines."
        }
    
    # Find agent file
    agent_config = config.get("agents", {}).get(agent_name, {})
    agent_file = agent_config.get("file")
    
    if agent_file is None:
        # Try to find agent file by convention
        agent_file = f"engineering/{agent_name}.md"
        if not (AGENTS_DIR / agent_file).exists():
            agent_file = f"management/{agent_name}.md"
            if not (AGENTS_DIR / agent_file).exists():
                return {
                    "agent": agent_name,
                    "status": "ERROR",
                    "error": f"No agent definition found for: {agent_name}"
                }
    
    # Build full task with context
    full_task = task
    if context:
        full_task = f"CONTEXT:\n{context}\n\nTASK:\n{task}"
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"{agent_name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 [{engine_name}] Dispatching to {agent_name}...")
    
    try:
        result = engine.run(agent_file, full_task, str(run_dir))
        
        # Save output
        output_file = run_dir / "output.md"
        output_file.write_text(result["stdout"])
        
        # Save command used
        cmd_file = run_dir / "command.txt"
        cmd_file.write_text(result.get("command", ""))
        
        # Update memory
        memory_file = MEMORY_DIR / f"{agent_name}_latest.md"
        memory_file.write_text(f"# {agent_name} Output — {timestamp}\n\n{result['stdout']}")
        
        status = "✅ SUCCESS" if result["returncode"] == 0 else "❌ FAILED"
        print(f"{status} {agent_name}")
        
        return {
            "agent": agent_name,
            "engine": engine_name,
            "status": status,
            "output": result["stdout"],
            "error": result.get("stderr", ""),
            "command": result.get("command", ""),
            "output_dir": str(run_dir),
        }
    
    except Exception as e:
        print(f"💥 {agent_name} crashed: {e}")
        return {
            "agent": agent_name,
            "engine": engine_name,
            "status": "ERROR",
            "error": str(e)
        }


def dispatch_parallel(tasks: list, config: dict = None) -> list:
    """Dispatch multiple agents in parallel"""
    if config is None:
        config = load_config()
    
    max_workers = config.get("parallel_max_workers", 4)
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                dispatch_agent,
                t["agent"],
                t["task"],
                t.get("context", ""),
                t.get("engine"),
                config
            ): t
            for t in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return results


def orchestrate(goal: str, engine: str = None, project_dir: str = ".") -> dict:
    """
    Main orchestration flow:
    1. PM breaks goal into tasks
    2. Orchestrator dispatches tasks to agents
    3. Agents work in parallel
    4. Tech Lead reviews
    5. Report compiled
    """
    config = load_config()
    
    print(f"\n🎯 GOAL: {goal}")
    print(f"🔧 ENGINE: {engine or config.get('default_engine', 'claude')}")
    print("=" * 60)
    
    # Step 1: PM breaks down the goal
    print("\n📋 Step 1: Project Manager breaking down the goal...")
    pm_result = dispatch_agent(
        "project-manager",
        f"Break down this goal into atomic tasks:\n\n{goal}\n\nProject directory: {project_dir}",
        context=f"You are managing a project at {project_dir}",
        engine_name=engine,
        config=config
    )
    
    if pm_result["status"] != "✅ SUCCESS":
        return {"error": "PM failed", "details": pm_result}
    
    print(f"\n📝 PM Plan:\n{pm_result['output'][:500]}...")
    
    # Step 2: Parse tasks
    tasks = parse_tasks(pm_result["output"], goal, engine)
    
    # Step 3: Dispatch agents
    print(f"\n🚀 Step 2: Dispatching {len(tasks)} agents...")
    results = dispatch_parallel(tasks, config)
    
    # Step 4: Tech Lead reviews
    print("\n🔍 Step 3: Tech Lead reviewing outputs...")
    review_context = "\n\n".join([
        f"## {r['agent']} Output\n{r.get('output', '')[:500]}"
        for r in results if r.get("output")
    ])
    
    review_result = dispatch_agent(
        "tech-lead",
        f"Review these agent outputs for consistency and quality:\n\n{review_context}",
        context=goal,
        engine_name=engine,
        config=config
    )
    
    # Step 5: Report
    report = {
        "goal": goal,
        "engine": engine or config.get("default_engine"),
        "timestamp": datetime.now().isoformat(),
        "pm_plan": pm_result["output"],
        "agent_results": results,
        "tech_lead_review": review_result.get("output", ""),
        "status": "COMPLETED"
    }
    
    report_file = OUTPUT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(report, indent=2, default=str))
    
    print(f"\n✅ Orchestration complete! Report: {report_file}")
    return report


def parse_tasks(pm_output: str, goal: str, engine: str = None) -> list:
    """Parse PM output into dispatchable tasks"""
    tasks = []
    goal_lower = goal.lower()
    
    if any(kw in goal_lower for kw in ["website", "web app", "landing page", "frontend", "ui"]):
        tasks.append({
            "agent": "frontend-dev",
            "task": f"Build the frontend for: {goal}",
            "context": pm_output,
            "engine": engine
        })
    
    if any(kw in goal_lower for kw in ["api", "backend", "server", "database", "auth"]):
        tasks.append({
            "agent": "backend-dev",
            "task": f"Build the backend for: {goal}",
            "context": pm_output,
            "engine": engine
        })
    
    if any(kw in goal_lower for kw in ["deploy", "docker", "ci/cd", "pipeline", "hosting"]):
        tasks.append({
            "agent": "devops",
            "task": f"Set up deployment for: {goal}",
            "context": pm_output,
            "engine": engine
        })
    
    if any(kw in goal_lower for kw in ["secure", "security", "audit"]):
        tasks.append({
            "agent": "security",
            "task": f"Audit security for: {goal}",
            "context": pm_output,
            "engine": engine
        })
    
    # Always add QA
    tasks.append({
        "agent": "qa-tester",
        "task": f"Write tests for: {goal}",
        "context": pm_output,
        "engine": engine
    })
    
    # Default: frontend + backend
    if not tasks:
        tasks = [
            {"agent": "frontend-dev", "task": f"Build the frontend for: {goal}", "context": pm_output, "engine": engine},
            {"agent": "backend-dev", "task": f"Build the backend for: {goal}", "context": pm_output, "engine": engine},
        ]
    
    return tasks


def main():
    parser = argparse.ArgumentParser(
        description="🛡️ Agent Swarm — Engine-agnostic multi-agent orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Build a landing page for TeenovateX"
  %(prog)s --engine gemini "Create a REST API"
  %(prog)s --engine generic --command "my-agent" --system-flag "--role" "Do something"
  %(prog)s --agent frontend-dev "Create a navbar"
  %(prog)s --list-engines
  %(prog)s --list-agents
        """
    )
    
    parser.add_argument("goal", nargs="?", help="Goal or task description")
    parser.add_argument("--engine", "-e", help="Engine to use (claude, gemini, codex, kilocode, etc.)")
    parser.add_argument("--agent", "-a", help="Dispatch to a specific agent only")
    parser.add_argument("--command", help="Custom command for generic engine")
    parser.add_argument("--system-flag", default="--prompt", help="System prompt flag for generic engine")
    parser.add_argument("--auto-flag", default="", help="Auto/yes flag for generic engine")
    parser.add_argument("--project", default=".", help="Project directory")
    parser.add_argument("--list-engines", action="store_true", help="List available engines")
    parser.add_argument("--list-agents", action="store_true", help="List available agents")
    parser.add_argument("--register-engine", nargs=3, metavar=("NAME", "COMMAND", "FLAG"),
                        help="Register a custom engine: NAME COMMAND SYSTEM_FLAG")
    
    args = parser.parse_args()
    
    # List engines
    if args.list_engines:
        print("\n🔧 Available Engines:\n")
        for eng in list_engines():
            print(f"  {eng['name']:12} — {eng['command']:20} (flag: {eng['system_prompt_flag']})")
        print(f"\n  {'generic':12} — (configure dynamically with --command and --system-flag)")
        print(f"\nTotal: {len(list_engines()) + 1} engines")
        return
    
    # List agents
    if args.list_agents:
        config = load_config()
        print("\n🤖 Available Agents:\n")
        for name, conf in config.get("agents", {}).items():
            print(f"  {name:20} — {conf.get('description', 'No description')}")
        print(f"\nTotal: {len(config.get('agents', {}))} agents")
        return
    
    # Register custom engine
    if args.register_engine:
        name, command, flag = args.register_engine
        
        class CustomEngine(BaseEngine):
            pass
        
        CustomEngine.name = name
        CustomEngine.command = command
        CustomEngine.system_prompt_flag = flag
        
        register_engine(name, CustomEngine)
        print(f"✅ Registered custom engine: {name} ({command} {flag})")
        return
    
    # Configure generic engine
    if args.command:
        GenericEngine.configure(args.command, args.system_flag, args.auto_flag)
        register_engine("generic", GenericEngine)
    
    # Single agent dispatch
    if args.agent:
        if not args.goal:
            print("❌ Error: Provide a task/goal after --agent")
            sys.exit(1)
        
        result = dispatch_agent(args.agent, args.goal, engine_name=args.engine)
        print(json.dumps(result, indent=2, default=str))
        return
    
    # Full orchestration
    if args.goal:
        report = orchestrate(args.goal, engine=args.engine, project_dir=args.project)
        return
    
    # No args — show help
    parser.print_help()


if __name__ == "__main__":
    main()
