#!/usr/bin/env python3
"""
Agent Swarm — Dashboard & Monitoring
Real-time monitoring of agent health, execution, and performance.

Features:
- Live agent status tracking
- Performance metrics
- Execution timeline
- Failure analysis
- Resource usage
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

SWARM_ROOT = Path(__file__).parent.parent
MEMORY_DIR = SWARM_ROOT / "memory"
OUTPUT_DIR = SWARM_ROOT / "output"
DASHBOARD_STATE = MEMORY_DIR / "dashboard_state.json"
METRICS_FILE = MEMORY_DIR / "metrics.json"


class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    DEBUGGING = "debugging"
    TIMEOUT = "timeout"
    ESCALATED = "escalated"


class AgentTracker:
    """Tracks the status and performance of a single agent"""
    
    def __init__(self, name: str, engine: str = "claude"):
        self.name = name
        self.engine = engine
        self.status = AgentStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.attempts = 0
        self.error: Optional[str] = None
        self.output_size = 0
        self.healing_actions = []
    
    def start(self):
        self.status = AgentStatus.RUNNING
        self.start_time = datetime.now()
        self.attempts += 1
    
    def succeed(self, output_size: int = 0):
        self.status = AgentStatus.SUCCESS
        self.end_time = datetime.now()
        self.output_size = output_size
    
    def fail(self, error: str):
        self.status = AgentStatus.FAILED
        self.end_time = datetime.now()
        self.error = error
    
    def debug(self):
        self.status = AgentStatus.DEBUGGING
    
    def escalate(self):
        self.status = AgentStatus.ESCALATED
        self.end_time = datetime.now()
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "engine": self.engine,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration, 1),
            "attempts": self.attempts,
            "error": self.error,
            "output_size": self.output_size,
            "healing_actions": self.healing_actions,
        }


class Dashboard:
    """
    Real-time dashboard for monitoring agent swarm execution.
    """
    
    def __init__(self, goal: str = ""):
        self.goal = goal
        self.agents: dict[str, AgentTracker] = {}
        self.start_time = datetime.now()
        self.phases: list[dict] = []
        self.current_phase = ""
    
    def register_agent(self, name: str, engine: str = "claude"):
        """Register an agent for tracking"""
        self.agents[name] = AgentTracker(name, engine)
    
    def start_phase(self, phase_name: str):
        """Mark the start of an orchestration phase"""
        self.current_phase = phase_name
        self.phases.append({
            "name": phase_name,
            "start_time": datetime.now().isoformat(),
            "status": "running",
        })
    
    def end_phase(self, phase_name: str, status: str = "completed"):
        """Mark the end of an orchestration phase"""
        for phase in self.phases:
            if phase["name"] == phase_name:
                phase["end_time"] = datetime.now().isoformat()
                phase["status"] = status
                break
    
    def start_agent(self, name: str, engine: str = "claude"):
        """Mark an agent as started"""
        if name not in self.agents:
            self.register_agent(name, engine)
        self.agents[name].start()
        self._save_state()
    
    def succeed_agent(self, name: str, output_size: int = 0):
        """Mark an agent as succeeded"""
        if name in self.agents:
            self.agents[name].succeed(output_size)
        self._save_state()
    
    def fail_agent(self, name: str, error: str):
        """Mark an agent as failed"""
        if name in self.agents:
            self.agents[name].fail(error)
        self._save_state()
    
    def heal_agent(self, name: str, strategy: str):
        """Record a healing action on an agent"""
        if name in self.agents:
            self.agents[name].healing_actions.append({
                "strategy": strategy,
                "timestamp": datetime.now().isoformat(),
            })
            self.agents[name].debug()
        self._save_state()
    
    def escalate_agent(self, name: str):
        """Mark an agent as escalated (needs human review)"""
        if name in self.agents:
            self.agents[name].escalate()
        self._save_state()
    
    # ═══════════════════════════════════════════
    # DISPLAY METHODS
    # ═══════════════════════════════════════════
    
    def render_live(self) -> str:
        """Render a live dashboard view"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"🛡️  AGENT SWARM DASHBOARD")
        lines.append(f"📋 Goal: {self.goal[:50]}...")
        lines.append(f"⏱️  Elapsed: {elapsed:.0f}s")
        lines.append(f"🔧 Phase: {self.current_phase}")
        lines.append("=" * 60)
        lines.append("")
        
        # Status bar
        status_counts = {}
        for agent in self.agents.values():
            status_counts[agent.status] = status_counts.get(agent.status, 0) + 1
        
        status_line = " | ".join([
            f"{'🟢' if s == 'success' else '🔴' if s == 'failed' else '🟡' if s == 'running' else '⚪'} {count} {s}"
            for s, count in status_counts.items()
        ])
        lines.append(f"Status: {status_line}")
        lines.append("")
        
        # Agent table
        lines.append(f"{'Agent':<25} {'Engine':<10} {'Status':<12} {'Duration':<10} {'Attempts'}")
        lines.append("-" * 70)
        
        for name, agent in sorted(self.agents.items()):
            status_icon = {
                AgentStatus.IDLE: "⚪",
                AgentStatus.RUNNING: "🟡",
                AgentStatus.SUCCESS: "🟢",
                AgentStatus.FAILED: "🔴",
                AgentStatus.DEBUGGING: "🐛",
                AgentStatus.TIMEOUT: "⏰",
                AgentStatus.ESCALATED: "⚠️",
            }.get(agent.status, "❓")
            
            duration_str = f"{agent.duration:.1f}s" if agent.duration > 0 else "-"
            lines.append(
                f"{status_icon} {name:<23} {agent.engine:<10} {agent.status:<12} {duration_str:<10} {agent.attempts}"
            )
        
        lines.append("")
        
        # Errors section
        failed = [a for a in self.agents.values() if a.status in (AgentStatus.FAILED, AgentStatus.ESCALATED)]
        if failed:
            lines.append("❌ FAILURES:")
            for agent in failed:
                lines.append(f"  {agent.name}: {agent.error[:80]}...")
            lines.append("")
        
        # Performance
        lines.append("📊 PERFORMANCE:")
        total_agents = len(self.agents)
        succeeded = status_counts.get(AgentStatus.SUCCESS, 0)
        failed_count = status_counts.get(AgentStatus.FAILED, 0) + status_counts.get(AgentStatus.ESCALATED, 0)
        
        lines.append(f"  Total: {total_agents} | ✅ {succeeded} | ❌ {failed_count} | 🟡 {status_counts.get(AgentStatus.RUNNING, 0)}")
        
        if total_agents > 0:
            success_rate = (succeeded / total_agents) * 100
            lines.append(f"  Success Rate: {success_rate:.0f}%")
        
        avg_duration = sum(a.duration for a in self.agents.values() if a.duration > 0) / max(1, succeeded)
        lines.append(f"  Avg Duration: {avg_duration:.1f}s")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def render_summary(self) -> dict:
        """Render a final summary as JSON"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        status_counts = {}
        for agent in self.agents.values():
            status_counts[agent.status] = status_counts.get(agent.status, 0) + 1
        
        return {
            "goal": self.goal,
            "total_time_seconds": round(elapsed, 1),
            "total_agents": len(self.agents),
            "status_breakdown": status_counts,
            "success_rate": f"{(status_counts.get(AgentStatus.SUCCESS, 0) / max(1, len(self.agents)) * 100):.1f}%",
            "phases": self.phases,
            "agents": {name: agent.to_dict() for name, agent in self.agents.items()},
            "failures": [
                agent.to_dict() for agent in self.agents.values()
                if agent.status in (AgentStatus.FAILED, AgentStatus.ESCALATED)
            ],
        }
    
    def _save_state(self):
        """Persist dashboard state"""
        MEMORY_DIR.mkdir(exist_ok=True)
        state = {
            "goal": self.goal,
            "start_time": self.start_time.isoformat(),
            "current_phase": self.current_phase,
            "phases": self.phases,
            "agents": {name: agent.to_dict() for name, agent in self.agents.items()},
        }
        DASHBOARD_STATE.write_text(json.dumps(state, indent=2, default=str))


class PerformanceMetrics:
    """Collects and analyzes performance metrics over time"""
    
    def __init__(self):
        self.runs: list[dict] = []
    
    def record_run(self, dashboard: Dashboard):
        """Record metrics from a completed run"""
        summary = dashboard.render_summary()
        self.runs.append(summary)
        self._save()
    
    def get_trends(self) -> dict:
        """Analyze trends across multiple runs"""
        if not self.runs:
            return {"message": "No runs recorded yet"}
        
        total_runs = len(self.runs)
        avg_time = sum(r["total_time_seconds"] for r in self.runs) / total_runs
        avg_agents = sum(r["total_agents"] for r in self.runs) / total_runs
        
        # Success rate trend
        success_rates = []
        for r in self.runs:
            total = r["total_agents"]
            succeeded = r["status_breakdown"].get("success", 0)
            success_rates.append((succeeded / max(1, total)) * 100)
        
        return {
            "total_runs": total_runs,
            "avg_time_seconds": round(avg_time, 1),
            "avg_agents_per_run": round(avg_agents, 1),
            "success_rate_trend": success_rates,
            "latest_success_rate": f"{success_rates[-1]:.0f}%" if success_rates else "N/A",
        }
    
    def _save(self):
        """Persist metrics"""
        MEMORY_DIR.mkdir(exist_ok=True)
        METRICS_FILE.write_text(json.dumps({
            "runs": self.runs,
            "trends": self.get_trends(),
        }, indent=2, default=str))
