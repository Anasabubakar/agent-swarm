#!/usr/bin/env python3
"""
Agent Swarm — Self-Healing System
Automatically detects failures and recovers without human intervention.

Recovery strategies:
1. Retry — Same agent, same task (up to 3 times)
2. Reassign — Different agent, same task (if agent-specific failure)
3. Simplify — Break failed task into smaller sub-tasks
4. Fallback — Use a different engine/model
5. Escalate — Flag for human review if all else fails
"""

import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

SWARM_ROOT = Path(__file__).parent.parent
MEMORY_DIR = SWARM_ROOT / "memory"
HEALING_LOG = MEMORY_DIR / "healing_log.json"


class HealingStrategy:
    """Enum-like class for healing strategies"""
    RETRY = "retry"
    REASSIGN = "reassign"
    SIMPLIFY = "simplify"
    FALLBACK = "fallback"
    ESCALATE = "escalate"


class AgentFailure:
    """Represents a failed agent execution"""
    
    def __init__(self, agent_name: str, task: str, error: str, 
                 attempt: int = 1, engine: str = "claude"):
        self.agent_name = agent_name
        self.task = task
        self.error = error
        self.attempt = attempt
        self.engine = engine
        self.timestamp = datetime.now().isoformat()
        self.strategy = None
        self.recovered = False
    
    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "task": self.task,
            "error": self.error,
            "attempt": self.attempt,
            "engine": self.engine,
            "timestamp": self.timestamp,
            "strategy": self.strategy,
            "recovered": self.recovered,
        }


class SelfHealer:
    """
    Monitors agent failures and applies recovery strategies.
    """
    
    MAX_RETRIES = 3
    FALLBACK_ENGINES = ["claude", "gemini", "kilocode", "codex"]
    
    # Agent substitution map — if agent X fails, try agent Y
    AGENT_SUBSTITUTES = {
        "frontend-dev": ["engineering-frontend-developer", "engineering-rapid-prototyper"],
        "backend-dev": ["engineering-backend-architect", "engineering-senior-developer"],
        "devops": ["engineering-devops-automator", "engineering-sre"],
        "security": ["engineering-security-engineer", "engineering-threat-detection-engineer"],
        "qa-tester": ["testing-api-tester", "testing-reality-checker"],
        "project-manager": ["project-management-project-shepherd", "project-manager-senior"],
        "tech-lead": ["engineering-software-architect", "engineering-code-reviewer"],
    }
    
    def __init__(self):
        self.failures: list[AgentFailure] = []
        self.healing_log: list[dict] = []
    
    def analyze_failure(self, failure: AgentFailure) -> str:
        """
        Analyze a failure and determine the best healing strategy.
        """
        error_lower = failure.error.lower()
        
        # Timeout — retry with same or simpler task
        if "timeout" in error_lower or "timed out" in error_lower:
            if failure.attempt < self.MAX_RETRIES:
                return HealingStrategy.RETRY
            return HealingStrategy.SIMPLIFY
        
        # Rate limit — wait and retry, or switch engine
        if "rate" in error_lower or "429" in error_lower or "limit" in error_lower:
            if failure.attempt < 2:
                return HealingStrategy.RETRY
            return HealingStrategy.FALLBACK
        
        # Auth/connection — switch engine
        if "auth" in error_lower or "connection" in error_lower or "401" in error_lower:
            return HealingStrategy.FALLBACK
        
        # Agent not found — reassign
        if "not found" in error_lower or "no agent" in error_lower:
            return HealingStrategy.REASSIGN
        
        # Model error — switch engine
        if "model" in error_lower or "unsupported" in error_lower:
            return HealingStrategy.FALLBACK
        
        # Unknown — retry first, then escalate
        if failure.attempt < self.MAX_RETRIES:
            return HealingStrategy.RETRY
        return HealingStrategy.ESCALATE
    
    def apply_strategy(self, failure: AgentFailure, strategy: str) -> dict:
        """
        Apply a healing strategy and return recovery action.
        """
        failure.strategy = strategy
        self.failures.append(failure)
        
        action = {
            "strategy": strategy,
            "original_agent": failure.agent_name,
            "original_engine": failure.engine,
            "attempt": failure.attempt,
        }
        
        if strategy == HealingStrategy.RETRY:
            # Same agent, same task, wait a bit
            action.update({
                "action": "retry",
                "agent": failure.agent_name,
                "task": failure.task,
                "engine": failure.engine,
                "delay_seconds": 5 * failure.attempt,  # Exponential backoff
                "message": f"Retry #{failure.attempt + 1} for {failure.agent_name}",
            })
        
        elif strategy == HealingStrategy.REASSIGN:
            # Different agent, same task
            substitutes = self.AGENT_SUBSTITUTES.get(failure.agent_name, [])
            next_agent = substitutes[0] if substitutes else failure.agent_name
            action.update({
                "action": "reassign",
                "agent": next_agent,
                "task": failure.task,
                "engine": failure.engine,
                "message": f"Reassigning from {failure.agent_name} to {next_agent}",
            })
        
        elif strategy == HealingStrategy.SIMPLIFY:
            # Break task into smaller pieces
            simplified_task = f"""The following task failed (attempt {failure.attempt}). 
Break it into the smallest possible sub-task and complete ONLY that:

ORIGINAL TASK:
{failure.task}

ERROR:
{failure.error}

Complete ONE small piece. Return what you managed to do."""
            action.update({
                "action": "simplify",
                "agent": failure.agent_name,
                "task": simplified_task,
                "engine": failure.engine,
                "message": f"Simplifying task for {failure.agent_name}",
            })
        
        elif strategy == HealingStrategy.FALLBACK:
            # Switch to a different engine
            current_idx = self.FALLBACK_ENGINES.index(failure.engine) if failure.engine in self.FALLBACK_ENGINES else -1
            next_engine = self.FALLBACK_ENGINES[(current_idx + 1) % len(self.FALLBACK_ENGINES)]
            action.update({
                "action": "fallback",
                "agent": failure.agent_name,
                "task": failure.task,
                "engine": next_engine,
                "message": f"Switching engine from {failure.engine} to {next_engine}",
            })
        
        elif strategy == HealingStrategy.ESCALATE:
            # Flag for human review
            action.update({
                "action": "escalate",
                "agent": failure.agent_name,
                "task": failure.task,
                "error": failure.error,
                "message": f"⚠️ ESCALATION: {failure.agent_name} failed after {failure.attempt} attempts. Human review needed.",
                "requires_human": True,
            })
        
        # Log the healing action
        self.healing_log.append({
            "timestamp": datetime.now().isoformat(),
            "failure": failure.to_dict(),
            "action": action,
        })
        
        return action
    
    def heal(self, agent_name: str, task: str, error: str, 
             attempt: int = 1, engine: str = "claude") -> dict:
        """
        Full healing flow: analyze failure → determine strategy → apply.
        """
        failure = AgentFailure(agent_name, task, error, attempt, engine)
        strategy = self.analyze_failure(failure)
        action = self.apply_strategy(failure, strategy)
        
        # Save healing log
        self._save_log()
        
        return action
    
    def _save_log(self):
        """Persist healing log"""
        MEMORY_DIR.mkdir(exist_ok=True)
        HEALING_LOG.write_text(json.dumps(self.healing_log, indent=2, default=str))
    
    def get_stats(self) -> dict:
        """Get healing statistics"""
        total = len(self.failures)
        recovered = len([f for f in self.failures if f.recovered])
        escalated = len([f for f in self.failures if f.strategy == HealingStrategy.ESCALATE])
        
        strategies_used = {}
        for f in self.failures:
            strategies_used[f.strategy] = strategies_used.get(f.strategy, 0) + 1
        
        return {
            "total_failures": total,
            "recovered": recovered,
            "escalated": escalated,
            "recovery_rate": f"{(recovered/total*100):.1f}%" if total > 0 else "N/A",
            "strategies_used": strategies_used,
        }


def heal_agent_failure(agent_name: str, task: str, error: str, 
                       attempt: int = 1, engine: str = "claude") -> dict:
    """Convenience function to heal a single failure"""
    healer = SelfHealer()
    return healer.heal(agent_name, task, error, attempt, engine)
