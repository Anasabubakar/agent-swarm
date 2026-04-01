#!/usr/bin/env python3
"""
OpenClaw Parallel Engine
Uses OpenClaw's sessions_spawn API for true parallel sub-agent execution.

Each agent runs as an isolated session with:
- Its own context window
- Its own memory
- Its own tool access
- No cross-contamination with other agents

This is NOT Python threads — these are real isolated AI sessions.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

SWARM_ROOT = Path(__file__).parent.parent
AGENTS_DIR = SWARM_ROOT / "agents"
MEMORY_DIR = SWARM_ROOT / "memory"
OUTPUT_DIR = SWARM_ROOT / "output"


class OpenClawSubAgent:
    """
    Spawns an isolated OpenClaw sub-agent session.
    
    Each agent is a real AI session with:
    - Isolated context (no pollution from other agents)
    - Agent-specific system prompt (the markdown file)
    - Task-specific instructions
    - File-based output
    """
    
    def __init__(self, agent_name: str, agent_file: str, task: str, context: str = "", 
                 model: str = "auto", thinking: str = "low"):
        self.agent_name = agent_name
        self.agent_file = agent_file
        self.task = task
        self.context = context
        self.model = model
        self.thinking = thinking
        self.session_key = None
        self.result = None
    
    def _load_agent_prompt(self) -> str:
        """Load the agent definition as system prompt"""
        agent_path = AGENTS_DIR / self.agent_file
        if not agent_path.exists():
            raise FileNotFoundError(f"Agent file not found: {self.agent_file}")
        return agent_path.read_text()
    
    def build_task_message(self) -> str:
        """Build the full task message for the sub-agent"""
        agent_prompt = self._load_agent_prompt()
        
        message = f"""You are a specialist agent. Follow your role definition strictly.

## YOUR ROLE
{agent_prompt}

## CONTEXT
{self.context if self.context else "No additional context provided."}

## YOUR TASK
{self.task}

## OUTPUT INSTRUCTIONS
1. Do the work described in your task
2. Write your output to a file at: output/{self.agent_name}_output.md
3. Return a summary of what you built/decided/found
4. Stay within your role constraints — do NOT do work outside your specialty

Begin now."""
        
        return message
    
    def spawn(self) -> dict:
        """
        Spawn the sub-agent as an OpenClaw session.
        
        Returns session info for tracking.
        """
        task_message = self.build_task_message()
        
        # Use the sessions_spawn API via the gateway
        # In a real implementation, this would call the OpenClaw API directly
        # For now, we structure the call for the gateway to process
        
        spawn_config = {
            "task": task_message,
            "label": f"swarm-{self.agent_name}",
            "model": self.model,
            "thinking": self.thinking,
            "mode": "run",  # One-shot execution
            "cleanup": "delete",  # Clean up after done
            "cwd": str(SWARM_ROOT),
            "runTimeoutSeconds": 600,  # 10 minute timeout
        }
        
        return spawn_config
    
    def spawn_via_gateway(self) -> dict:
        """
        Actually spawn via OpenClaw gateway API.
        Uses curl to call the gateway's session spawn endpoint.
        """
        task_message = self.build_task_message()
        
        # Save task to file for the sub-agent
        task_file = MEMORY_DIR / f"{self.agent_name}_task.md"
        task_file.write_text(task_message)
        
        # Build the gateway API call
        import os
        gateway_url = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:37777")
        gateway_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
        
        payload = {
            "task": task_message,
            "label": f"swarm-{self.agent_name}-{int(time.time())}",
            "model": self.model,
            "thinking": self.thinking,
            "mode": "run",
            "cleanup": "delete",
            "cwd": str(SWARM_ROOT),
            "runTimeoutSeconds": 600,
        }
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                f"{gateway_url}/api/sessions/spawn",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}" if gateway_token else "",
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read())
                self.session_key = result.get("sessionKey")
                return result
        
        except Exception as e:
            return {"error": str(e), "agent": self.agent_name}


class OpenClawParallelEngine:
    """
    Parallel execution engine using OpenClaw sub-agents.
    
    Dispatches multiple agents simultaneously, each running in its own
    isolated session. Collects results when all complete.
    """
    
    def __init__(self, max_parallel: int = 4):
        self.max_parallel = max_parallel
        self.agents: list[OpenClawSubAgent] = []
        self.results: dict = {}
    
    def add_agent(self, agent_name: str, agent_file: str, task: str, 
                  context: str = "", model: str = "auto") -> OpenClawSubAgent:
        """Add an agent to the execution queue"""
        agent = OpenClawSubAgent(
            agent_name=agent_name,
            agent_file=agent_file,
            task=task,
            context=context,
            model=model
        )
        self.agents.append(agent)
        return agent
    
    def dispatch_all(self) -> list:
        """Dispatch all agents in parallel"""
        print(f"\n🚀 Dispatching {len(self.agents)} agents in parallel...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            futures = {
                executor.submit(agent.spawn_via_gateway): agent
                for agent in self.agents
            }
            
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    result = future.result()
                    results.append({
                        "agent": agent.agent_name,
                        "status": "DISPATCHED" if "error" not in result else "FAILED",
                        "session_key": result.get("sessionKey"),
                        "error": result.get("error"),
                    })
                    status = "✅" if "error" not in result else "❌"
                    print(f"  {status} {agent.agent_name}")
                except Exception as e:
                    results.append({
                        "agent": agent.agent_name,
                        "status": "ERROR",
                        "error": str(e),
                    })
                    print(f"  ❌ {agent.agent_name}: {e}")
        
        return results
    
    def collect_results(self, session_keys: list, timeout: int = 600) -> dict:
        """
        Collect results from all spawned sessions.
        Polls until all sessions complete or timeout.
        """
        import os
        gateway_url = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:37777")
        gateway_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
        
        results = {}
        pending = set(session_keys)
        start = time.time()
        
        while pending and (time.time() - start) < timeout:
            for key in list(pending):
                try:
                    import urllib.request
                    req = urllib.request.Request(
                        f"{gateway_url}/api/sessions/{key}/status",
                        headers={"Authorization": f"Bearer {gateway_token}"} if gateway_token else {},
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        status = json.loads(response.read())
                        
                        if status.get("state") in ("completed", "failed", "cancelled"):
                            results[key] = status
                            pending.discard(key)
                            print(f"  ✅ {key}: {status.get('state')}")
                
                except Exception:
                    pass  # Session might not exist yet
            
            if pending:
                time.sleep(5)  # Poll every 5 seconds
        
        return results


# Convenience function for the orchestrator
def dispatch_openclaw_agents(tasks: list, max_parallel: int = 4) -> list:
    """
    Dispatch multiple agents via OpenClaw sub-agents.
    
    Args:
        tasks: List of dicts with keys: agent, file, task, context, model
        max_parallel: Maximum parallel sessions
    
    Returns:
        List of dispatch results
    """
    engine = OpenClawParallelEngine(max_parallel=max_parallel)
    
    for task in tasks:
        engine.add_agent(
            agent_name=task["agent"],
            agent_file=task.get("file", f"{task['agent']}.md"),
            task=task["task"],
            context=task.get("context", ""),
            model=task.get("model", "auto"),
        )
    
    return engine.dispatch_all()
